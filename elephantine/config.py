"""Configuration module for MemAgent."""
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MEMAGENT_", env_file=".env", extra="ignore")

    # Host & Server
    HOST: str = "127.0.0.1"
    PORT: int = 8765
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Storage Paths
    BASE_DATA_DIR: Path = Path("./data")
    SQLITE_DB_NAME: str = "elephantine_metadata.db"
    LANCEDB_DIR_NAME: str = "lancedb_store"

    # Embedding Model Settings (CPU Native ONNX)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    ONN_MODELS_CACHE_DIR: Path = Path("./data/models")
    LOCAL_MODEL_PATH: Optional[Path] = None
    OFFLINE_MODE: bool = False
    ONNX_INTRA_OP_NUM_THREADS: int = 2
    ONNX_INTER_OP_NUM_THREADS: int = 1

    # In-Process GGUF / llama.cpp Engine Settings
    GGUF_MODEL_PATH: Optional[Path] = None
    GGUF_N_CTX: int = 2048
    GGUF_N_THREADS: int = 2
    GGUF_TEMPERATURE: float = 0.1

    # Cognitive & Recall Settings
    TIME_DECAY_LAMBDA: float = 0.005  # Decay rate per hour
    DENSE_SEARCH_TOP_K: int = 20
    BM25_SEARCH_TOP_K: int = 20
    HYBRID_RRF_K: int = 60            # Reciprocal Rank Fusion constant
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.78  # Conflict detection cutoff

    # Enterprise & RBAC Settings
    AUTH_ENABLED: bool = False
    API_KEYS_JSON: str = "{}"
    CORS_ORIGINS: list[str] = ["*"]


    @property
    def sqlite_path(self) -> Path:
        return self.BASE_DATA_DIR / self.SQLITE_DB_NAME

    @property
    def lancedb_path(self) -> Path:
        return self.BASE_DATA_DIR / self.LANCEDB_DIR_NAME

settings = Settings()
