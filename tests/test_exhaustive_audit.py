import pytest
import asyncio
import uuid
import time
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from elephantine.api.app import app
from elephantine.config import settings
from elephantine.core.embedder import OnnxCpuEmbedder
from elephantine.core.scoring import HybridScorer
from elephantine.core.conflict import ConflictResolver
from elephantine.core.graph_extractor import RuleBasedGraphExtractor
from elephantine.core.project import detect_project_workspace
from elephantine.storage.sqlite_store import SqliteMetadataStore
from elephantine.storage.lancedb_store import LanceDbVectorStore
from elephantine.storage.procedural_store import ProceduralMemoryStore
from elephantine.enterprise.rbac import (
    RoleBasedAuthEngine,
    ApiKeyManager,
    ROLE_ADMIN,
    ROLE_ARCHITECT,
    ROLE_EDITOR,
    ROLE_VIEWER
)
from elephantine.client import ElephantineClient, AsyncElephantineClient, ElephantineLangChainMemory

# ==============================================================================
# 1. STORAGE LAYER: SQLITE & LANCEDB ROBUSTNESS & SQL INJECTION RESISTANCE
# ==============================================================================

@pytest.mark.asyncio
async def test_sqlite_sql_injection_resilience():
    """Verify that malicious SQL injection inputs do not compromise SQLite FTS5 or metadata."""
    sqlite_store = SqliteMetadataStore()
    malicious_payloads = [
        "'; DROP TABLE memories; --",
        "\" OR 1=1; --",
        "' UNION SELECT * FROM memories --",
        "MATCH '\"* AND DROP TABLE memories--'"
    ]
    
    for payload in malicious_payloads:
        # Search BM25 with SQL injection attempts
        results = await sqlite_store.search_bm25(query=payload, top_k=5)
        assert isinstance(results, list)
        
        # Workspace filter injection attempts
        stats = await sqlite_store.get_engine_stats(workspace_id=payload)
        assert "total_memories" in stats
        
        # Memory listing with injection attempt
        mems = await sqlite_store.list_all_memories(workspace_id=payload)
        assert isinstance(mems, list)
        
        # Graph triplets with injection attempt
        triplets = await sqlite_store.get_all_graph_triplets(workspace_id=payload)
        assert isinstance(triplets, list)

@pytest.mark.asyncio
async def test_lancedb_and_sqlite_concurrency():
    """Verify concurrent write operations do not deadlock SQLite WAL or LanceDB."""
    sqlite_store = SqliteMetadataStore()
    lancedb_store = LanceDbVectorStore()
    embedder = OnnxCpuEmbedder()
    
    async def write_op(idx: int):
        m_id = str(uuid.uuid4())
        content = f"Concurrent test message #{idx}"
        vec = embedder.embed_text(content)
        await sqlite_store.insert_memory(
            memory_id=m_id,
            content=content,
            source_agent="concurrency_test",
            entity_key=None,
            category="general",
            confidence=1.0,
            metadata={},
            created_at=datetime.now(timezone.utc),
            workspace_id="test-concurrency",
            role_authority=0.5
        )
        lancedb_store.add_vector(
            memory_id=m_id,
            vector=vec,
            source_agent="concurrency_test",
            category="general",
            created_at_epoch=time.time()
        )
        return m_id

    # Execute 15 concurrent writes
    tasks = [write_op(i) for i in range(15)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for r in results:
        assert not isinstance(r, Exception), f"Concurrent write failed: {r}"

# ==============================================================================
# 2. EDGE CASES: EXTREME LENGTHS, EMPTY STRINGS, UNICODE & EMOJIS
# ==============================================================================

def test_embedder_edge_cases():
    """Verify embedder handles empty string, massive text, and diverse unicode cleanly."""
    embedder = OnnxCpuEmbedder()
    
    # Empty string
    vec_empty = embedder.embed_text("")
    assert len(vec_empty) == settings.EMBEDDING_DIM
    assert abs(sum(x**2 for x in vec_empty) - 1.0) < 1e-3  # Normalized L2
    
    # 50,000 character string (exceeds typical context)
    huge_text = "elephantine memory persistence " * 2000
    vec_huge = embedder.embed_text(huge_text)
    assert len(vec_huge) == settings.EMBEDDING_DIM
    
    # Diverse multilingual unicode and emojis
    multi_text = "🐘 象 は 決 し て 忘 れ な い ! ¡Los elefantes nunca olvidan! Filler asla unutmaz."
    vec_multi = embedder.embed_text(multi_text)
    assert len(vec_multi) == settings.EMBEDDING_DIM

# ==============================================================================
# 3. PROCEDURAL MEMORY & WORKFLOW EXECUTION
# ==============================================================================

@pytest.mark.asyncio
async def test_procedural_store_full_lifecycle():
    """Verify tool call execution tracking and workflow snippet extraction."""
    proc_store = ProceduralMemoryStore()
    from elephantine.api.schemas import ToolCallExecution
    
    sess_id = f"test-sess-{uuid.uuid4()}"
    call = ToolCallExecution(
        tool_name="git_commit",
        tool_input={"message": "test commit"},
        tool_output={"stdout": "[main 1234567] test commit"},
        status="success",
        execution_time_ms=45.2,
        session_id=sess_id
    )
    
    call_id = await proc_store.record_tool_call(call)
    assert call_id is not None
    
    history = await proc_store.get_session_history(sess_id)
    assert len(history) == 1
    assert history[0]["tool_name"] == "git_commit"
    
    # Save & retrieve workflow
    step_sequence = [{"step": 1, "action": "git_tag"}, {"step": 2, "action": "git_push"}]
    wf_id = await proc_store.save_or_update_workflow(
        pattern_name="git_release_workflow",
        description="Standard git tag and release pattern",
        steps=step_sequence,
        success=True
    )
    assert wf_id is not None
    
    retrieved = await proc_store.get_workflow("git_release_workflow")
    assert retrieved is not None
    assert retrieved.step_sequence == step_sequence

# ==============================================================================
# 4. CONSOLIDATION & PRUNING LIFECYCLE
# ==============================================================================

@pytest.mark.asyncio
async def test_consolidation_and_pruning_api():
    """Verify /memories/consolidate and /memories/prune endpoints."""
    transport = ASGITransport(app=app)
    sqlite_store = SqliteMetadataStore()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ws = f"ws-consolidate-{uuid.uuid4()}"
        now = datetime.now(timezone.utc)
        
        # Insert two active facts directly to test multi-record consolidation
        m1_id = str(uuid.uuid4())
        m2_id = str(uuid.uuid4())
        await sqlite_store.insert_memory(
            memory_id=m1_id,
            content="User prefers dark mode in editor.",
            source_agent="audit",
            entity_key="user:ui_theme",
            category="preference",
            confidence=1.0,
            metadata={},
            created_at=now - timedelta(hours=2),
            workspace_id=ws,
            role_authority=0.5
        )
        await sqlite_store.insert_memory(
            memory_id=m2_id,
            content="User prefers high contrast mode.",
            source_agent="audit",
            entity_key="user:ui_theme",
            category="preference",
            confidence=1.0,
            metadata={},
            created_at=now - timedelta(hours=1),
            workspace_id=ws,
            role_authority=0.8
        )
        
        # Consolidate memories for this entity
        cons_res = await client.post("/memories/consolidate", json={
            "entity_key": "user:ui_theme",
            "workspace_id": ws
        })
        assert cons_res.status_code == 200
        cons_data = cons_res.json()
        assert cons_data["status"] == "consolidated"
        assert cons_data["consolidated_count"] == 2
        assert "canonical_id" in cons_data
        
        # Test pruning endpoint (POST /memories/prune)
        prune_res = await client.post(f"/memories/prune?older_than_days=1&workspace_id={ws}")
        assert prune_res.status_code == 200
        prune_data = prune_res.json()
        assert "pruned_count" in prune_data
        assert isinstance(prune_data["pruned_count"], int)

# ==============================================================================
# 5. ERROR RESILIENCE: 404, MALFORMED REQUESTS, MISSING PARAMS
# ==============================================================================

@pytest.mark.asyncio
async def test_api_error_handling():
    """Verify API handles invalid input, missing parameters, and non-existent IDs gracefully."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Missing required 'content' in remember -> 422 Unprocessable Entity
        res1 = await client.post("/remember", json={"category": "test"})
        assert res1.status_code == 422
        
        # 2. Missing required 'query' in recall -> 422 Unprocessable Entity
        res2 = await client.post("/recall", json={"top_k": 5})
        assert res2.status_code == 422
        
        # 3. Deleting non-existent memory ID -> 404 Not Found
        res3 = await client.delete("/api/v1/memories/non-existent-memory-uuid-99999")
        assert res3.status_code == 404

# ==============================================================================
# 6. LANGCHAIN MEMORY ADAPTER & CLIENT SDK COMPREHENSIVE TEST
# ==============================================================================

def test_langchain_adapter_unit():
    """Verify LangChain ElephantineLangChainMemory interface."""
    from starlette.testclient import TestClient
    client = ElephantineClient(base_url="http://test")
    client._client = TestClient(app=app, base_url="http://test")
    adapter = ElephantineLangChainMemory(
        client=client,
        workspace_id="langchain-test-ws"
    )
    assert adapter.memory_variables == ["history"]
    
    # Save context
    adapter.save_context({"input": "What is our architecture?"}, {"output": "PostgreSQL 16 on backend."})
    
    # Load variables
    loaded = adapter.load_memory_variables({"input": "architecture database"})
    assert "history" in loaded
    
    # Clear
    adapter.clear()

# ==============================================================================
# 7. TIME DECAY SCORER MATHEMATICAL BOUNDARY VERIFICATION
# ==============================================================================

def test_temporal_decay_math():
    """Verify time decay function decreases monotonically and never goes negative."""
    scorer = HybridScorer(time_decay_lambda=0.01)
    
    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    one_day_ago = (now - timedelta(days=1)).isoformat()
    one_month_ago = (now - timedelta(days=30)).isoformat()
    future_time = (now + timedelta(hours=5)).isoformat()
    
    # Future timestamp should not exceed 1.0
    decay_future = scorer.calculate_temporal_decay(future_time)
    assert decay_future == 1.0
    
    # Monotonic decay
    decay_1h = scorer.calculate_temporal_decay(one_hour_ago)
    decay_1d = scorer.calculate_temporal_decay(one_day_ago)
    decay_1m = scorer.calculate_temporal_decay(one_month_ago)
    
    assert 1.0 > decay_1h > decay_1d > decay_1m > 0.0
