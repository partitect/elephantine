import pytest
from httpx import AsyncClient, ASGITransport
from elephantine.api.app import create_app

@pytest.mark.asyncio
async def test_dashboard_and_stats():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dash_res = await client.get("/dashboard")
        assert dash_res.status_code == 200
        assert "text/html" in dash_res.headers.get("content-type", "")
        assert "ELEPHANTINE" in dash_res.text

        stats_res = await client.get("/api/v1/stats")
        assert stats_res.status_code == 200
        stats_data = stats_res.json()
        assert "total_memories" in stats_data
        assert "active_memories" in stats_data
        assert "deprecated_memories" in stats_data

        mem_res = await client.get("/api/v1/memories?limit=10")
        assert mem_res.status_code == 200
        assert isinstance(mem_res.json(), list)

        ws_res = await client.get("/api/v1/workspaces")
        assert ws_res.status_code == 200
        assert isinstance(ws_res.json(), list)
        assert len(ws_res.json()) >= 1


@pytest.mark.asyncio
async def test_dashboard_auth_enforcement_in_enterprise_mode(monkeypatch):
    """Verify that when AUTH_ENABLED=True, dashboard API routes reject unauthorized access."""
    from elephantine.config import settings
    from elephantine.enterprise.rbac import api_key_manager

    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    api_key_manager.register_key("test-dash-key", "tenant-alpha", ["admin"])

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Without credentials: must be rejected with 401 Unauthorized
        res_no_auth = await client.get("/api/v1/memories")
        assert res_no_auth.status_code == 401

        # With valid Authorization header: must succeed with 200
        res_auth = await client.get("/api/v1/memories", headers={"Authorization": "Bearer test-dash-key"})
        assert res_auth.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_enterprise_allowed_workspaces_isolation(monkeypatch):
    """Verify that an enterprise caller cannot access forbidden workspaces within the same tenant via dashboard routes."""
    import uuid
    from datetime import datetime, timezone
    from elephantine.config import settings
    from elephantine.enterprise.rbac import api_key_manager
    from elephantine.storage.sqlite_store import SqliteMetadataStore

    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    # Register restricted enterprise key with access only to 'allowed-proj'
    api_key_manager.register_key(
        "restricted-dash-key",
        "tenant-corp",
        ["admin"],
        allowed_workspaces=["allowed-proj"]
    )

    store = SqliteMetadataStore()
    now = datetime.now(timezone.utc)
    uid = uuid.uuid4().hex[:6]
    # Create a memory in allowed workspace
    mem_allowed_id = f"mem-allowed-{uid}"
    await store.insert_memory(
        memory_id=mem_allowed_id,
        content="Corp public roadmap.",
        source_agent="corp-bot",
        entity_key="roadmap",
        category="fact",
        confidence=1.0,
        metadata={},
        created_at=now,
        workspace_id="tenant-corp:allowed-proj"
    )
    # Create a memory in secret/forbidden workspace of the same tenant
    mem_forbidden_id = f"mem-forbidden-{uid}"
    await store.insert_memory(
        memory_id=mem_forbidden_id,
        content="Corp secret acquisition plan.",
        source_agent="corp-bot",
        entity_key="m-and-a",
        category="fact",
        confidence=1.0,
        metadata={},
        created_at=now,
        workspace_id="tenant-corp:forbidden-proj"
    )

    app = create_app()
    transport = ASGITransport(app=app)
    headers = {"Authorization": "Bearer restricted-dash-key"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. /api/v1/workspaces: should return only 'allowed-proj' and NOT 'forbidden-proj'
        ws_res = await client.get("/api/v1/workspaces", headers=headers)
        assert ws_res.status_code == 200
        workspaces = ws_res.json()
        assert "allowed-proj" in workspaces
        assert "forbidden-proj" not in workspaces

        # 2. /api/v1/stats with forbidden workspace must return 403
        stats_forbidden = await client.get("/api/v1/stats?workspace_id=forbidden-proj", headers=headers)
        assert stats_forbidden.status_code == 403

        # stats with allowed workspace must succeed
        stats_allowed = await client.get("/api/v1/stats?workspace_id=allowed-proj", headers=headers)
        assert stats_allowed.status_code == 200

        # 3. /api/v1/memories with forbidden workspace must return 403
        mem_forbidden = await client.get("/api/v1/memories?workspace_id=forbidden-proj", headers=headers)
        assert mem_forbidden.status_code == 403

        # memories with allowed workspace must succeed
        mem_allowed = await client.get("/api/v1/memories?workspace_id=allowed-proj", headers=headers)
        assert mem_allowed.status_code == 200

        # 4. /api/v1/graph/all with forbidden workspace must return 403
        graph_forbidden = await client.get("/api/v1/graph/all?workspace_id=forbidden-proj", headers=headers)
        assert graph_forbidden.status_code == 403

        # 5. DELETE /api/v1/memories/{mem_forbidden_id} must return 403 Forbidden even though same tenant!
        del_forbidden = await client.delete(f"/api/v1/memories/{mem_forbidden_id}", headers=headers)
        assert del_forbidden.status_code == 403

        # DELETE memory in allowed workspace must succeed
        del_allowed = await client.delete(f"/api/v1/memories/{mem_allowed_id}", headers=headers)
        assert del_allowed.status_code == 200

