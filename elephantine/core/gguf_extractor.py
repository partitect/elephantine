import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from elephantine.config import settings
from elephantine.core.structured_extractor import (
    ExtractionOutputSchema,
    ExtractedFactItem,
    GroundingValidator
)

logger = logging.getLogger("elephantine.core.gguf_extractor")

class LlamaCppEngine:
    """
    High-Performance, In-Process GGUF SLM Engine.
    Executes quantized SLMs (Qwen2.5-0.5B, Smollm2, Phi-3.5) directly via llama-cpp-python C-bindings.
    Guarantees strict JSON schema conformance without external servers.
    """
    _instance: Optional["LlamaCppEngine"] = None

    def __init__(
        self,
        model_path: Optional[Path] = settings.GGUF_MODEL_PATH,
        n_ctx: int = settings.GGUF_N_CTX,
        n_threads: int = settings.GGUF_N_THREADS,
        temperature: float = settings.GGUF_TEMPERATURE
    ):
        self.model_path = Path(model_path) if model_path else None
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.temperature = temperature
        self._llm = None
        self.validator = GroundingValidator()

    @classmethod
    def get_instance(cls) -> "LlamaCppEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_available(self) -> bool:
        return self.model_path is not None and self.model_path.exists()

    def _load_model(self):
        if self._llm is not None:
            return
        if not self.is_available:
            raise FileNotFoundError(f"GGUF model file not found at: {self.model_path}")

        try:
            from llama_cpp import Llama
            logger.info(f"Loading in-process GGUF model: {self.model_path} (threads={self.n_threads}, n_ctx={self.n_ctx})")
            self._llm = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Failed to initialize llama-cpp-python runtime: {e}")
            raise e

    def extract_memories(self, text: str) -> List[ExtractedFactItem]:
        """
        Performs in-process SLM extraction with grammar-constrained JSON output.
        """
        cleaned_text = text.strip()
        if len(cleaned_text) < 4:
            return []

        self._load_model()
        schema_json = ExtractionOutputSchema.model_json_schema()

        prompt = (
            "<|im_start|>system\n"
            "You are Elephantine Cognitive Memory Engine. Extract atomic, persistent facts, user preferences, "
            "and configurations from the user input. Ignore greetings and ephemeral small talk.\n"
            f"Return output strictly adhering to this JSON schema:\n{json.dumps(schema_json)}<|im_end|>\n"
            f"<|im_start|>user\n{cleaned_text}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

        response = self._llm.create_completion(
            prompt=prompt,
            max_tokens=512,
            temperature=self.temperature,
            response_format={
                "type": "json_object",
                "schema": schema_json
            }
        )

        raw_output = response["choices"][0]["text"]
        try:
            parsed = json.loads(raw_output)
            output_model = ExtractionOutputSchema.model_validate(parsed)
        except Exception as e:
            logger.warning(f"GGUF output JSON parsing failed: {e}. Raw was: {raw_output}")
            return []

        if not output_model.has_meaningful_memory:
            return []

        # Validate grounding against hallucinations
        validated_facts = []
        for fact_item in output_model.facts:
            if self.validator.verify_grounding(cleaned_text, fact_item):
                validated_facts.append(fact_item)
            else:
                logger.warning(f"GroundingValidator discarded ungrounded GGUF fact: '{fact_item.fact}'")

        return validated_facts

    def synthesize_answer(self, question: str, contexts: List[Dict[str, Any]]) -> str:
        """
        Synthesizes a factual, grounded answer to a question using retrieved memory contexts.
        """
        if not self.is_available:
            # Clean grounded summary fallback when GGUF model is not loaded
            lines = [f"Found {len(contexts)} grounded memory item(s) for '{question}':\n"]
            for i, c in enumerate(contexts, 1):
                src = c.get('source_agent', 'system')
                lines.append(f"[{i}] ({c.get('category', 'fact').upper()}) {c.get('content')} [source: {src}]")
            return "\n".join(lines)

        self._load_model()
        formatted_context = "\n".join([
            f"- [{i+1}] {c.get('content')} (Source: {c.get('source_agent', 'unknown')}, Category: {c.get('category', 'general')})"
            for i, c in enumerate(contexts)
        ])

        prompt = (
            "<|im_start|>system\n"
            "You are Elephantine Cognitive Memory Assistant. Synthesize a concise, factual answer to the user's question "
            "based strictly on the provided retrieved memories. Cite the memory index [1], [2] when stating facts. "
            "If the memories contradict each other, highlight the conflict and rely on the higher authority source. "
            "If the memories do not contain the answer, state that clearly.<|im_end|>\n"
            f"<|im_start|>user\nContext Memories:\n{formatted_context}\n\nQuestion: {question}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

        response = self._llm.create_completion(
            prompt=prompt,
            max_tokens=512,
            temperature=self.temperature
        )
        return response["choices"][0]["text"].strip()
