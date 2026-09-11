import os
import pathlib
import lancedb
import pyarrow as pa
from typing import Any, Dict, List, Optional
from memagent.config import settings

class LanceDbVectorStore:
    """
    Embedded, C++ backed LanceDB vector store.
    Zero external database server, pure file-backed zero-copy querying.
    """
    def __init__(self, db_dir: pathlib.Path = settings.lancedb_path, dim: int = settings.EMBEDDING_DIM):
        self.db_dir = pathlib.Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self.db = lancedb.connect(str(self.db_dir))
        self.table_name = "memory_vectors"
        self._init_table()

    def _init_table(self):
        schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), self.dim)),
            pa.field("source_agent", pa.string()),
            pa.field("category", pa.string()),
            pa.field("created_at_epoch", pa.float64()),
        ])

        tables = self.db.table_names() if hasattr(self.db, "table_names") else []
        if self.table_name not in tables:
            try:
                self.table = self.db.create_table(self.table_name, schema=schema)
            except Exception:
                self.table = self.db.open_table(self.table_name)
        else:
            self.table = self.db.open_table(self.table_name)

    def add_vector(
        self,
        memory_id: str,
        vector: List[float],
        source_agent: str,
        category: str,
        created_at_epoch: float
    ) -> None:
        data = [{
            "id": memory_id,
            "vector": vector,
            "source_agent": source_agent,
            "category": category,
            "created_at_epoch": created_at_epoch
        }]
        self.table.add(data)

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 20,
        source_agent: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = self.table.search(query_vector).metric("cosine").limit(top_k)

        filters = []
        if source_agent:
            filters.append(f"source_agent = '{source_agent}'")
        if category:
            filters.append(f"category = '{category}'")

        if filters:
            query = query.where(" AND ".join(filters))

        results = query.to_list()
        formatted = []
        for row in results:
            dist = row.get("_distance", 1.0)
            similarity = max(0.0, min(1.0, 1.0 - dist))
            formatted.append({
                "id": row["id"],
                "cosine_similarity": float(similarity),
                "distance": float(dist),
                "source_agent": row.get("source_agent"),
                "category": row.get("category"),
                "created_at_epoch": row.get("created_at_epoch")
            })
        return formatted

    def delete_memory(self, memory_id: str) -> None:
        """Removes a superseded or soft-deprecated vector from the active vector index."""
        try:
            self.table.delete(f"id = '{memory_id}'")
        except Exception:
            pass
