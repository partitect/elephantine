import pytest
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from elephantine.api.app import app
from elephantine.storage.sqlite_store import SqliteMetadataStore
from elephantine.core.proactive import ProactiveEngine, parse_trigger_condition

def test_parse_trigger_condition():
    ref_time = datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc) # Friday
    
    # 1. Interval
    next_run, is_rec = parse_trigger_condition('interval', 'every:30m', reference_time=ref_time)
    assert is_rec is True
    assert next_run == ref_time + timedelta(minutes=30)
    
    # 2. Daily
    next_run, is_rec = parse_trigger_condition('daily', 'daily:14:00', reference_time=ref_time)
    assert is_rec is True
    assert next_run.hour == 14 and next_run.day == 11

    # 3. Weekly Friday (today is Friday 12:00, target 17:00)
    next_run, is_rec = parse_trigger_condition('weekly', 'weekly:FRI:17:00', reference_time=ref_time)
    assert is_rec is True
    assert next_run.weekday() == 4
    assert next_run.hour == 17

    # 4. Absolute datetime
    iso_str = '2026-10-01T10:00:00Z'
    next_run, is_rec = parse_trigger_condition('datetime', iso_str, reference_time=ref_time)
    assert is_rec is False
    assert next_run.year == 2026 and next_run.month == 10

@pytest.mark.asyncio
async def test_proactive_engine_evaluation_and_ack():
    store = SqliteMetadataStore()
    engine = ProactiveEngine(store)
    
    # Create memory first
    m_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    ws = f'ws-proactive-{uuid.uuid4()}'
    
    await store.insert_memory(
        memory_id=m_id,
        content='Team reminder: Weekly status report is due at 17:00.',
        source_agent='manager',
        entity_key='team:reminder',
        category='proactive',
        confidence=1.0,
        metadata={},
        created_at=now,
        workspace_id=ws,
        role_authority=0.9
    )
    
    # Create a trigger that is ALREADY DUE (1 minute in the past)
    t_id = str(uuid.uuid4())
    due_time = now - timedelta(minutes=1)
    await store.create_proactive_trigger(
        trigger_id=t_id,
        memory_id=m_id,
        trigger_type='interval',
        condition_value='every:1h',
        target_agent='coder_agent',
        workspace_id=ws,
        next_trigger_at=due_time
    )
    
    # Evaluate triggers
    fired = await engine.evaluate_due_triggers(current_time=now)
    assert len(fired) >= 1
    found = next((f for f in fired if f['trigger_id'] == t_id), None)
    assert found is not None
    assert found['target_agent'] == 'coder_agent'
    assert 'Weekly status report' in found['content']
    
    # Check pending alerts for coder_agent
    pending = await store.get_pending_triggers_for_agent(target_agent='coder_agent', workspace_id=ws)
    assert any(p['id'] == t_id for p in pending)
    
    # Acknowledge alert
    acked = await store.acknowledge_trigger(t_id)
    assert acked is True
    
    # Pending should now be empty for that trigger
    pending_after = await store.get_pending_triggers_for_agent(target_agent='coder_agent', workspace_id=ws)
    assert not any(p['id'] == t_id for p in pending_after)

@pytest.mark.asyncio
async def test_proactive_api_endpoints():
    transport = ASGITransport(app=app)
    ws = f'ws-api-proactive-{uuid.uuid4()}'
    
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        # 1. Register trigger with inline memory content
        res = await client.post('/proactive/triggers', json={
            'content': 'Check server disk usage every 2 hours.',
            'trigger_type': 'interval',
            'condition_value': 'every:2h',
            'target_agent': 'devops_agent',
            'workspace_id': ws
        })
        assert res.status_code == 200
        data = res.json()
        assert data['status'] == 'created'
        trigger_id = data['trigger_id']
        assert 'next_trigger_at' in data

        # 2. Query pending alerts (initially empty because next_trigger_at is 2h ahead)
        res_pending = await client.get(f'/proactive/pending?target_agent=devops_agent&workspace_id={ws}')
        assert res_pending.status_code == 200
        assert isinstance(res_pending.json(), list)
