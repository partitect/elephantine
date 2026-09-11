import pytest
from httpx import AsyncClient, ASGITransport
from elephantine.api.app import app

@pytest.mark.asyncio
async def test_dashboard_graph_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Store a memory with relations
        rem_res = await client.post("/remember", json={
            "content": "Alice uses TypeScript and Bob prefers Python.",
            "category": "fact",
            "workspace_id": "graph-test-ws",
            "source_agent": "test-agent"
        })
        assert rem_res.status_code == 200

        # 2. Query /api/v1/graph/all
        res = await client.get("/api/v1/graph/all?workspace_id=graph-test-ws")
        assert res.status_code == 200
        data = res.json()
        assert "nodes" in data
        assert "edges" in data
        assert "total_triplets" in data
        assert data["total_triplets"] >= 2
        
        # Check node structure
        node_ids = [n["id"] for n in data["nodes"]]
        assert "alice" in node_ids
        assert "typescript" in node_ids
