import os
import pathlib
import lancedb
import pyarrow as pa
from typing import Any, Dict, List, Optional
from elephantine.config import settings

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
            pa.field("workspace_id", pa.string()),
            pa.field("expires_at_epoch", pa.float64()),
        ])

        tables = self.db.table_names() if hasattr(self.db, "table_names") else []
        if self.table_name not in tables:
            try:
                self.table = self.db.create_table(self.table_name, schema=schema)
            except Exception:
                self.table = self.db.open_table(self.table_name)
        else:
            self.table = self.db.open_table(self.table_name)
            # Check if existing table needs schema migration (e.g. adding workspace_id)
            current_schema = self.table.schema
            field_names = [f.name for f in current_schema]
            if "workspace_id" not in field_names or "expires_at_epoch" not in field_names:
                try:
                    # Migrate existing records to new schema using pure PyArrow (zero pandas dependency)
                    arrow_tbl = self.table.to_arrow()
                    num_rows = arrow_tbl.num_rows
                    if "workspace_id" not in field_names:
                        ws_array = pa.array(["default"] * num_rows, type=pa.string())
                        arrow_tbl = arrow_tbl.append_column("workspace_id", ws_array)
                    if "expires_at_epoch" not in field_names:
                        exp_array = pa.array([0.0] * num_rows, type=pa.float64())
                        arrow_tbl = arrow_tbl.append_column("expires_at_epoch", exp_array)
                    self.db.drop_table(self.table_name)
                    self.table = self.db.create_table(self.table_name, data=arrow_tbl)
                except Exception:
                    pass

    def add_vector(
        self,
        memory_id: str,
        vector: List[float],
        source_agent: str,
        category: str,
        created_at_epoch: float,
        workspace_id: str = "default",
        expires_at_epoch: float = 0.0
    ) -> None:
        data = [{
            "id": memory_id,
            "vector": vector,
            "source_agent": source_agent,
            "category": category,
            "created_at_epoch": created_at_epoch,
            "workspace_id": workspace_id,
            "expires_at_epoch": float(expires_at_epoch) if expires_at_epoch else 0.0
        }]
        self.table.add(data)

    def add_vectors_batch(self, items: List[Dict[str, Any]]) -> int:
        """
        Batch adds dense vectors in a single LanceDB Arrow commit.
        """
        if not items:
            return 0
        data = []
        for item in items:
            data.append({
                "id": item["id"],
                "vector": item["vector"],
                "source_agent": item.get("source_agent", "unknown"),
                "category": item.get("category", "general"),
                "created_at_epoch": float(item.get("created_at_epoch", 0.0)),
                "workspace_id": item.get("workspace_id", "default"),
                "expires_at_epoch": float(item.get("expires_at_epoch", 0.0))
            })
        self.table.add(data)
        return len(data)

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 20,
        source_agent: Optional[str] = None,
        category: Optional[str] = None,
        workspace_id: Optional[str] = None,
        current_epoch: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        query = self.table.search(query_vector).metric("cosine").limit(top_k)

        filters = []
        if workspace_id:
            filters.append(f"workspace_id = '{workspace_id}'")
        if source_agent:
            filters.append(f"source_agent = '{source_agent}'")
        if category:
            filters.append(f"category = '{category}'")
        if current_epoch:
            # Exclude expired memories at the dense index level
            filters.append(f"(expires_at_epoch == 0.0 OR expires_at_epoch > {current_epoch})")

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
                "created_at_epoch": row.get("created_at_epoch"),
                "workspace_id": row.get("workspace_id", "default")
            })
        return formatted

    def delete_memory(self, memory_id: str) -> None:
        """Removes a superseded or soft-deprecated vector from the active vector index."""
        try:
            self.table.delete(f"id = '{memory_id}'")
        except Exception:
            pass
