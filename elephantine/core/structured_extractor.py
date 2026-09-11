import re
import json
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator

class ExtractedFactItem(BaseModel):
    """Strict structured representation of an extracted fact."""
    fact: str = Field(..., description="Atomic, unambiguous fact sentence in natural language")
    entity_key: Optional[str] = Field(default=None, description="Normalized entity key, e.g. 'user:db_choice' or 'config:port'")
    category: str = Field(default="general", description="Category: 'fact', 'preference', 'config', 'procedural'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from model or extractor")
    grounding_tokens: List[str] = Field(default_factory=list, description="Key anchor tokens present in source text that ground this fact")

    @field_validator("fact")
    def fact_must_not_be_blank(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 5:
            raise ValueError("Fact must contain at least 5 meaningful characters")
        return s

class ExtractionOutputSchema(BaseModel):
    """Top-level schema enforced on SLM / Extraction outputs."""
    has_meaningful_memory: bool = Field(..., description="True if text contained persistent facts/preferences, False otherwise")
    facts: List[ExtractedFactItem] = Field(default_factory=list, description="List of validated extracted fact items")

class GroundingValidator:
    """
    Prevents SLM hallucinations by verifying that extracted entities,
    numbers, and keywords genuinely exist in the source raw prompt.
    """
    def __init__(self, stop_words: Optional[Set[str]] = None):
        self.stop_words = stop_words or {
            "the", "a", "an", "in", "on", "at", "to", "for", "is", "are", "was",
            "were", "of", "and", "or", "user", "agent", "system", "that", "this",
            "with", "by", "as", "from", "it", "my", "our", "i", "we"
        }

    def tokenize(self, text: str) -> Set[str]:
        # Strip all punctuation cleanly, keep alpha-numeric words
        clean_text = re.sub(r"[^\w\s]", " ", text)
        words = clean_text.lower().split()
        return {w for w in words if w not in self.stop_words and len(w) > 1}

    def verify_grounding(self, raw_input: str, extracted_item: ExtractedFactItem) -> bool:
        raw_tokens = self.tokenize(raw_input)
        if not raw_tokens:
            return False

        fact_tokens = self.tokenize(extracted_item.fact)
        if not fact_tokens:
            return False

        # Check direct token overlap and root prefixes (e.g. live/lives, develop/developer)
        overlap = set()
        for ft in fact_tokens:
            if ft in raw_tokens:
                overlap.add(ft)
            else:
                # Check root prefix matching (e.g. lives -> live)
                for rt in raw_tokens:
                    if len(ft) >= 4 and len(rt) >= 4 and (ft.startswith(rt[:4]) or rt.startswith(ft[:4])):
                        overlap.add(ft)
                        break

        for token in extracted_item.grounding_tokens:
            clean_t = re.sub(r"[^\w]", "", token.lower().strip())
            if clean_t and clean_t in raw_tokens:
                overlap.add(clean_t)

        overlap_ratio = len(overlap) / len(fact_tokens)
        return overlap_ratio >= 0.35 or len(overlap) >= 2

class StructuredMemoryExtractor:
    def __init__(self):
        self.validator = GroundingValidator()

    def get_json_schema(self) -> Dict[str, Any]:
        return ExtractionOutputSchema.model_json_schema()

    def extract_with_grounding(self, raw_text: str, default_category: str = "general") -> List[ExtractedFactItem]:
        raw_clean = raw_text.strip()
        if len(raw_clean) < 4:
            return []

        # 1. Try In-Process GGUF SLM Engine if model file is configured and present
        try:
            from elephantine.core.gguf_extractor import LlamaCppEngine
            engine = LlamaCppEngine.get_instance()
            if engine.is_available:
                facts = engine.extract_memories(raw_clean)
                if facts:
                    return facts
        except Exception:
            pass

        # 2. Fallback to ultra-fast two-stage heuristic extraction
        from elephantine.core.extractor import TwoStageMemoryExtractor
        stage1 = TwoStageMemoryExtractor()
        res = stage1.extract_structured(raw_clean, default_category=default_category)

        if not res.get("should_store", False):
            return []

        candidate = ExtractedFactItem(
            fact=res["cleaned_content"],
            entity_key=res.get("entity_key"),
            category=res.get("category", "general"),
            confidence=float(res.get("confidence", 0.8)),
            grounding_tokens=list(self.validator.tokenize(raw_clean))
        )

        if self.validator.verify_grounding(raw_clean, candidate):
            return [candidate]

        return []
