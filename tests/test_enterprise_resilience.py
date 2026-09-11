import pytest
import asyncio
from elephantine.storage.sqlite_store import SqliteMetadataStore
from elephantine.storage.lancedb_store import LanceDbVectorStore
from elephantine.core.buffer import AsyncMemoryWriteBuffer
from elephantine.core.consolidator import MemoryConsolidator
from elephantine.core.governor import AdaptiveComputeGovernor

@pytest.mark.asyncio
async def test_async_write_buffer_high_concurrency(tmp_path):
    sql_store = SqliteMetadataStore(db_path=tmp_path / 'test_buf.db')
    lance_store = LanceDbVectorStore(db_dir=tmp_path / 'test_lance_buf')
    buffer = AsyncMemoryWriteBuffer(sql_store, lance_store, batch_size=10, flush_interval_seconds=0.01)
    buffer.start()

    # Enqueue 20 concurrent items
    futures = []
    for i in range(20):
        item = {
            'memory_id': f'buf_mem_{i}',
            'content': f'Concurrent memory content {i}',
            'source_agent': 'agent_swarm',
            'entity_key': f'entity_{i}',
            'vector': [0.1] * 384,
            'workspace_id': 'swarm_pool',
            'role_authority': 0.8
        }
        fut = await buffer.enqueue(item)
        futures.append(fut)

    results = await asyncio.gather(*futures)
    assert len(results) == 20
    assert all(r is True for r in results)

    # Verify persisted in sqlite
    mems = await sql_store.get_active_by_entity('entity_0', workspace_id='swarm_pool')
    assert len(mems) == 1
    assert mems[0]['id'] == 'buf_mem_0'

    await buffer.stop()

@pytest.mark.asyncio
async def test_memory_consolidator_and_pruning(tmp_path):
    sql_store = SqliteMetadataStore(db_path=tmp_path / 'test_cons.db')
    consolidator = MemoryConsolidator(sql_store)

    # Insert 3 fragmented facts for user:stack
    import uuid
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for i, stack_part in enumerate(['Uses FastAPI', 'Uses LanceDB', 'Prefers Python 3.12']):
        await sql_store.insert_memory(
            memory_id=f'frag_{i}',
            content=stack_part,
            source_agent='junior_dev',
            entity_key='user:tech_stack',
            category='pref',
            confidence=1.0,
            metadata={},
            created_at=now,
            workspace_id='team_core',
            role_authority=0.5
        )

    # Consolidate
    res = await consolidator.consolidate_entity('user:tech_stack', workspace_id='team_core')
    assert res is not None
    assert res['consolidated_count'] == 3
    assert 'FastAPI' in res['canonical_content']
    assert 'LanceDB' in res['canonical_content']

    # Check that fragments are now deprecated
    active = await sql_store.get_active_by_entity('user:tech_stack', workspace_id='team_core')
    assert len(active) == 1
    assert active[0]['category'] == 'consolidated'

def test_adaptive_compute_governor():
    gov = AdaptiveComputeGovernor(max_concurrent_slm=1, cooldown_seconds=1.0)
    assert gov.should_use_slm(5) is False
    assert gov.should_use_slm(50) is True

    gov.acquire_slm()
    # Should throttle when at capacity
    assert gov.should_use_slm(50) is False
    gov.release_slm()
