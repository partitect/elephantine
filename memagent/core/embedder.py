import os
import pathlib
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from huggingface_hub import hf_hub_download
from memagent.config import settings

class OnnxCpuEmbedder:
    """
    High-performance CPU-native embedder using ONNX Runtime with AVX/threading optimizations.
    Dynamic padding and compact sequence lengths ensure sub-10ms CPU inference.
    Zero PyTorch or CUDA dependencies.
    """
    def __init__(self, model_repo: str = settings.EMBEDDING_MODEL_NAME):
        self.model_repo = model_repo
        self.cache_dir = pathlib.Path(settings.ONN_MODELS_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.tokenizer = None
        self.session = None
        self._initialize()

    def _initialize(self):
        onnx_file = hf_hub_download(
            repo_id=self.model_repo,
            filename="onnx/model.onnx",
            subfolder="",
            cache_dir=str(self.cache_dir)
        )
        tokenizer_file = hf_hub_download(
            repo_id=self.model_repo,
            filename="tokenizer.json",
            cache_dir=str(self.cache_dir)
        )

        self.tokenizer = Tokenizer.from_file(tokenizer_file)
        self.tokenizer.enable_truncation(max_length=256)

        sess_options = ort.SessionOptions()
        sess_options.intra_op_num_threads = 4
        sess_options.inter_op_num_threads = 1
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        self.session = ort.InferenceSession(
            onnx_file,
            sess_options=sess_options,
            providers=["CPUExecutionProvider"]
        )

    def _mean_pooling(self, token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        return sum_embeddings / sum_mask

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, ord=2, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-9, norms)
        return vectors / norms

    def embed_text(self, text: str) -> list[float]:
        encoding = self.tokenizer.encode(text)
        input_ids = np.array([encoding.ids], dtype=np.int64)
        attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
        token_type_ids = np.array([encoding.type_ids], dtype=np.int64)

        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        model_inputs = [inp.name for inp in self.session.get_inputs()]
        if "token_type_ids" in model_inputs:
            inputs["token_type_ids"] = token_type_ids

        outputs = self.session.run(None, inputs)
        sentence_embedding = self._mean_pooling(outputs[0], attention_mask)
        normalized = self._normalize(sentence_embedding)
        return normalized[0].astype(np.float32).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # Use dynamic padding per batch to max length in current batch
        max_len = max(len(self.tokenizer.encode(t).ids) for t in texts)
        max_len = min(256, max(8, max_len))
        
        self.tokenizer.enable_padding(length=max_len)
        encodings = self.tokenizer.encode_batch(texts)
        self.tokenizer.no_padding()

        input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        token_type_ids = np.array([e.type_ids for e in encodings], dtype=np.int64)

        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        model_inputs = [inp.name for inp in self.session.get_inputs()]
        if "token_type_ids" in model_inputs:
            inputs["token_type_ids"] = token_type_ids

        outputs = self.session.run(None, inputs)
        sentence_embeddings = self._mean_pooling(outputs[0], attention_mask)
        normalized = self._normalize(sentence_embeddings)
        return normalized.astype(np.float32).tolist()
