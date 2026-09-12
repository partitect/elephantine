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
