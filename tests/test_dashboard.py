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
