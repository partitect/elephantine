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
