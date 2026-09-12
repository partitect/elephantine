import pytest
from httpx import AsyncClient, ASGITransport
from elephantine.api.app import app

@pytest.mark.asyncio
async def test_multi_agent_shared_workspace():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ws_id = "collab-project-x"

        # 1. Coder Agent finds and stores a fix in the workspace
        r1es = await client.post("/remember", json={
            "content": "Fixed authentication by adding JWT header validation.",
            "category": "procedural",
            "source_agent": "coder-agent",
            "workspace_id": ws_id,
            "role_authority": 0.6
        })
        assert r1es.status_code == 200

        # 2. Tester Agent recalls within same workspace_id and immediately finds it
        rec1 = await client.post("/recall", json={
            "query": "authentication JWT header fix",
            "workspace_id": ws_id,
            "source_agent": None,
            "top_k": 3
        })
        assert rec1.status_code == 200
        data1 = rec1.json()
        assert data1["total_found"] >= 1
        assert "jwt header" in data1["memories"][0]["content"].lower()
        assert data1["memories"][0]["source_agent"] == "coder-agent"
        assert data1["memories"][0]["workspace_id"] == ws_id

        # 3. Unrelated workspace should not leak this data
        rec2 = await client.post("/recall", json={
            "query": "authentication JWT header fix",
            "workspace_id": "other-project-yz",
            "top_k": 3
        })
        assert rec2.status_code == 200
        assert rec2.json()["total_found"] == 0


@pytest.mark.asyncio
async def test_role_authority_consensus_protection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ws_id = "auth-consensus-ws"
        e_key = "project:python_version"
        
        # 1. Senior Architect (Authority = 1.0) decides Python 3.13
        arch_res = await client.post("/recall" if False else "/remember", json={
            "content": "Project uses Python 3.13 strictly for free-threading.",
            "category": "config",
            "source_agent": "lead-architect",
            "entity_key": e_key,
            "workspace_id": ws_id,
            "role_authority": 1.0
        })
        assert arch_res.status_code == 200
        arch_id = arch_res.json()["id"]

        # 2. Junior Agent (authority = 0.4) tries to overwrite with Python 3.10
        jr_res = await client.post("/remember", json={
            "content": "Project uses Python 3.10 for legacy support.",
            "category": "config",
            "source_agent": "junior-dev",
            "entity_key": e_key,
            "workspace_id": ws_id,
            "role_authority": 0.4
        })
        assert jr_res.status_code == 200
        # Architect memory should NOT be in conflicts_resolved (because jr auth < arch auth)
        assert arch_id not in jr_res.json()["conflicts_resolved"]

        # 3. Verify recall preserves Architect's authoritative decision
        rec = await client.post("/recall", json={
            "query": "What Python version does the project use?",
            "workspace_id": ws_id,
            "top_k": 3
        })
        assert rec.status_code == 200
        rec_data = rec.json()
        assert rec_data["total_found"] >= 1
        # The active authoritative one must be Python 3.13
        assert "3.13" in rec_data["memories"][0]["content"]
        assert rec_data["memories"][0]["role_authority"] == 1.0


@pytest.mark.asyncio
async def test_ttl_expiry_and_temporal_recall():
    """Verify that memories with expired TTL are filtered out and temporal filters work."""
    import asyncio
    from datetime import datetime, timezone, timedelta
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ws = "ttl-lifecycle-test"

        # 1. Store a short TTL memory (e.g. 0.0001 hours = ~0.36 seconds)
        t_resp = await client.post("/remember", json={
            "content": "Temporary token ABC-123 valid for 5 seconds.",
            "category": "credential_ref",
            "workspace_id": ws,
            "ttl_hours": 0.0001
        })
        assert t_resp.status_code == 200
        mem_id = t_resp.json()["id"]

        # 2. Store a permanent memory
        p_resp = await client.post("/remember", json={
            "content": "Permanent master architecture decision: microkernel design.",
            "category": "architecture",
            "workspace_id": ws
        })
        assert p_resp.status_code == 200

        # Wait 1 second for TTL to expire
        await asyncio.sleep(1.0)

        # 3. Recall: temporary memory must NOT be returned because it expired
        rec = await client.post("/recall", json={
            "query": "Temporary token ABC-123",
            "workspace_id": ws,
            "top_k": 5
        })
        assert rec.status_code == 200
        recalled_ids = [m["id"] for m in rec.json()["memories"]]
        assert mem_id not in recalled_ids

        # Permanent memory must still be recalled
        rec_perm = await client.post("/recall", json={
            "query": "Permanent master architecture decision",
            "workspace_id": ws,
            "top_k": 5
        })
        assert rec_perm.status_code == 200
        assert any("microkernel" in m["content"] for m in rec_perm.json()["memories"])


@pytest.mark.asyncio
async def test_immutable_event_ledger_time_travel():
    """Verify that every memory state change is preserved in the immutable ledger."""
    import asyncio
    from datetime import datetime, timezone
    import uuid
    from elephantine.api.routes.memory import get_container
    svc = get_container()
    uid = uuid.uuid4().hex[:8]
    ws = f"time-travel-ws-{uid}"
    key = f"service:deploy_state-{uid}"

    # Step 1: Initial deployment (Version 1)
    now1 = datetime.now(timezone.utc)
    id1 = f"mem-tt-1-{uid}"
    await svc.sqlite_store.insert_memory(
        memory_id=id1,
        content="Deployment status is STAGING.",
        source_agent="devops-lead",
        entity_key=key,
        category="status",
        confidence=1.0,
        metadata={"build": 101},
        created_at=now1,
        workspace_id=ws,
        role_authority=0.8
    )

    await asyncio.sleep(0.05)
    time_checkpoint = datetime.now(timezone.utc).isoformat()
    await asyncio.sleep(0.05)

    # Step 2: Superseded by Production deployment (Version 2)
    id2 = f"mem-tt-2-{uid}"
    now2 = datetime.now(timezone.utc)
    await svc.sqlite_store.deprecate_memory(id1, id2)
    await svc.sqlite_store.insert_memory(
        memory_id=id2,
        content="Deployment status is PRODUCTION.",
        source_agent="release-manager",
        entity_key=key,
        category="status",
        confidence=1.0,
        metadata={"build": 102},
        created_at=now2,
        workspace_id=ws,
        role_authority=1.0
    )

    # Current view: only Version 2 is active
    active = await svc.sqlite_store.get_active_by_entity(key, workspace_id=ws)
    assert len(active) == 1
    assert active[0]["content"] == "Deployment status is PRODUCTION."

    # Time-travel query as of checkpoint: must faithfully return Version 1 (STAGING)
    past_state = await svc.sqlite_store.get_memories_as_of(time_checkpoint, workspace_id=ws)
    assert len(past_state) >= 1
    staging_records = [r for r in past_state if r["entity_key"] == key]
    assert len(staging_records) == 1
    assert staging_records[0]["content"] == "Deployment status is STAGING."
    assert staging_records[0]["event_type"] == "CREATED"


@pytest.mark.asyncio
async def test_server_side_authority_clamping():
    """Verify that caller cannot claim higher authority than allowed by security context."""
    from elephantine.core.auth_interface import TenantContext
    from elephantine.api.routes.memory import remember_endpoint, get_container
    from elephantine.api.schemas import RememberRequest

    svc = get_container()
    # Caller context strictly limits max_role_authority to 0.4 (Junior/Worker)
    restricted_auth = TenantContext(
        tenant_id="test_tenant",
        agent_id="junior_bot",
        roles=["editor"],
        is_enterprise=True,
        max_role_authority=0.4,
        allowed_workspaces=["allowed_ws"]
    )

    # Caller tries to claim role_authority = 1.0 (Admin/Architect)
    req = RememberRequest(
        content="Attempting unauthorized high-authority override.",
        category="security",
        workspace_id="allowed_ws",
        role_authority=1.0
    )

    res = await remember_endpoint(req, svc, _auth=restricted_auth)
    assert res.status_code if hasattr(res, "status_code") else True

    # Check database: stored role_authority must be clamped to 0.4!
    stored = await svc.sqlite_store.get_memory_by_id(res.id)
    assert stored["role_authority"] == 0.4


@pytest.mark.asyncio
async def test_memory_events_immutable_triggers():
    """Verify SQLite triggers prevent any UPDATE or DELETE on memory_events."""
    import aiosqlite
    import pytest
    from elephantine.api.routes.memory import get_container
    svc = get_container()

    async with aiosqlite.connect(str(svc.sqlite_store.db_path)) as db:
        # Pick any existing event
        cursor = await db.execute("SELECT event_id FROM memory_events LIMIT 1")
        row = await cursor.fetchone()
        if not row:
            pytest.skip("No events in table yet")
        ev_id = row[0]

        # Attempt UPDATE on memory_events
        with pytest.raises(Exception) as exc_update:
            await db.execute("UPDATE memory_events SET content = 'tampered' WHERE event_id = ?", (ev_id,))
        assert "immutable append-only" in str(exc_update.value).lower()

        # Attempt DELETE on memory_events
        with pytest.raises(Exception) as exc_delete:
            await db.execute("DELETE FROM memory_events WHERE event_id = ?", (ev_id,))
        assert "immutable append-only" in str(exc_delete.value).lower()


@pytest.mark.asyncio
async def test_api_key_manager_context_mapping():
    """Verify ApiKeyManager properly maps allowed_workspaces and max_role_authority from config."""
    import json
    from elephantine.enterprise.rbac import ApiKeyManager

    cfg = {
        "key-junior-1": {
            "tenant_id": "tenant-corp",
            "agent_id": "junior-agent",
            "roles": ["editor"],
            "allowed_workspaces": ["frontend", "docs"],
            "max_role_authority": 0.45
        }
    }
    mgr = ApiKeyManager(keys_json=json.dumps(cfg))
    ctx = mgr.authenticate("key-junior-1")
    assert ctx is not None
    assert ctx.tenant_id == "tenant-corp"
    assert ctx.max_role_authority == 0.45
    assert set(ctx.allowed_workspaces) == {"frontend", "docs"}


@pytest.mark.asyncio
async def test_recall_as_of_and_changed_since_end_to_end():
    """Verify /recall endpoint faithfully performs time-travel as_of and audit changed_since."""
    import asyncio
    import uuid
    from datetime import datetime, timezone
    from elephantine.api.routes.memory import remember_endpoint, recall_endpoint, get_container
    from elephantine.api.schemas import RememberRequest, RecallRequest

    svc = get_container()
    uid = uuid.uuid4().hex[:8]
    ws = f"audit-ws-{uid}"
    key = f"feature:payment_gateway-{uid}"

    t_start = datetime.now(timezone.utc)

    # 1. Version 1: Stripe (created)
    req1 = RememberRequest(
        content="Primary payment gateway is Stripe v1.",
        category="decision",
        entity_key=key,
        workspace_id=ws,
        role_authority=0.8
    )
    res1 = await remember_endpoint(req1, svc)
    v1_id = res1.id

    await asyncio.sleep(0.05)
    t_v1_checkpoint = datetime.now(timezone.utc)
    await asyncio.sleep(0.05)

    # 2. Version 2: Adyen (supersedes Stripe)
    req2 = RememberRequest(
        content="Primary payment gateway migrated to Adyen v2.",
        category="decision",
        entity_key=key,
        workspace_id=ws,
        role_authority=0.9
    )
    res2 = await remember_endpoint(req2, svc)
    v2_id = res2.id

    # Time-travel query as of t_v1_checkpoint: Must return Stripe v1 even though it is superseded today!
    rec_past = await recall_endpoint(RecallRequest(
        query="payment gateway",
        workspace_id=ws,
        as_of=t_v1_checkpoint
    ), svc)
    assert len(rec_past.memories) >= 1
    assert any("Stripe" in m.content for m in rec_past.memories)
    assert not any("Adyen" in m.content for m in rec_past.memories)

    # Audit query changed_since t_start: Must return both CREATED and SUPERSEDED events!
    rec_audit = await recall_endpoint(RecallRequest(
        query="payment",
        workspace_id=ws,
        changed_since=t_start
    ), svc)
    assert len(rec_audit.memories) >= 2
    event_types = [m.metadata.get("_event_type") for m in rec_audit.memories]
    assert "CREATED" in event_types
    assert "SUPERSEDED" in event_types

