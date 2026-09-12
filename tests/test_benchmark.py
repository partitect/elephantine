import time
import pytest
from httpx import AsyncClient, ASGITransport
from elephantine.api.app import app

@pytest.mark.asyncio
async def test_benchmark_recall_latency():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed test memories
        for i in range(10):
            await client.post("/remember", json={
                "content": f"System operational checkpoint {i}: service running smoothly on node {i}.",
                "category": "fact",
                "source_agent": "benchmark"
            })

        # Warmup query
        await client.post("/recall", json={"query": "checkpoint service", "top_k": 5})

        # Run 30 recall iterations and measure latency
        latencies = []
        for _ in range(30):
            t0 = time.perf_counter()
            resp = await client.post("/recall", json={
                "query": "checkpoint service running node",
                "top_k": 5
            })
            t1 = time.perf_counter()
            assert resp.status_code == 200
            latencies.append((t1 - t0) * 1000.0)

        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        
        print(f"\n--- Benchmark Results ---")
        print(f"p50 latency: {p50:.2f} ms")
        print(f"p95 latency: {p95:.2f} ms")
        # CPU threshold target (< 350ms for full hybrid search + time decay in virtualized CI runners like macOS)
        assert p50 < 350.0, f"p50 latency too high: {p50:.2f} ms"
