import os
import shutil
import pathlib
import pytest
from datetime import datetime
from elephantine.storage.sqlite_store import SqliteMetadataStore
from elephantine.storage.lancedb_store import LanceDbVectorStore
from elephantine.core.embedder import OnnxCpuEmbedder
from elephantine.core.conflict import ConflictResolver

@pytest.fixture
def temp_dirs(tmp_path):
    sqlite_p = tmp_path / "test_meta.db"
    lance_p = tmp_path / "test_lancedb"
    return sqlite_p, lance_p

@pytest.mark.asyncio
async def test_sqlite_and_lancedb_crud(temp_dirs):
    sqlite_p, lance_p = temp_dirs
    sql_store = SqliteMetadataStore(db_path=sqlite_p)
    lance_store = LanceDbVectorStore(db_dir=lance_p, dim=384)
    
    # 1. Insert memory
    mem_id = "mem-1"
    now = datetime.utcnow()
    await sql_store.insert_memory(
        memory_id=mem_id,
        content="The main engine runs on port 8765 with FastAPI.",
        source_agent="agent-alpha",
        entity_key="config:port",
        category="config",
        confidence=0.95,
        metadata={"env": "prod"},
        created_at=now
    )
    
    # Check SQLite retrieval
    saved = await sql_store.get_memory_by_id(mem_id)
    assert saved is not None
    assert saved["content"] == "The main engine runs on port 8765 with FastAPI."
    assert saved["is_active"] == 1
    
    # Check BM25 search
    bm25 = await sql_store.search_bm25("port FastAPI", top_k=5)
    assert len(bm25) >= 1
    assert bm25[0]["id"] == mem_id

    # 2. Add Vector to LanceDB
    dummy_vec = [0.05] * 384
    lance_store.add_vector(
        memory_id=mem_id,
        vector=dummy_vec,
        source_agent="agent-alpha",
        category="config",
        created_at_epoch=now.timestamp()
    )
    
    results = lance_store.search_similar(dummy_vec, top_k=5)
    assert len(results) >= 1
    assert results[0]["id"] == mem_id
    assert results[0]["cosine_similarity"] > 0.99
