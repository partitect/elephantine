import pytest
from httpx import AsyncClient, ASGITransport
from memagent.api.app import app

@pytest.mark.asyncio
async def test_remember_and_recall_pipeline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        # 2. Remember a preference
        remember_resp1 = await client.post("/remember", json={
            "content": "User prefers dark mode and postgresql for database.",
            "category": "preference",
            "source_agent": "agent-test",
            "entity_key": "user_preference:theme"
        })
        assert remember_resp1.status_code == 200
        data1 = remember_resp1.json()
        assert data1["status"] == "stored"
        mem_id_1 = data1["id"]

        # 3. Remember an updated preference (Conflict / LWW testing)
        remember_resp2 = await client.post("/remember", json={
            "content": "User prefers light mode and sqlite for embedded work.",
            "category": "preference",
            "source_agent": "agent-test",
            "entity_key": "user_preference:theme"
        })
        assert remember_resp2.status_code == 200
        data2 = remember_resp2.json()
        assert mem_id_1 in data2["conflicts_resolved"]

        # 4. Recall memory
        recall_resp = await client.post("/recall", json={
            "query": "What are user's theme and database preferences?",
            "top_k": 3
        })
        assert recall_resp.status_code == 200
        rec = recall_resp.json()
        assert rec["total_found"] >= 1
        # The active memory must be the light mode one, not the deprecated dark mode one
        top_mem = rec["memories"][0]
        assert "light mode" in top_mem["content"]
        assert rec["latency_ms"] < 200.0  # Latency under threshold
