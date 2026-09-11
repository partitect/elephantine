import pytest
from httpx import AsyncClient, ASGITransport, Client
from elephantine.api.app import app
from elephantine import ElephantineClient, AsyncElephantineClient
from elephantine.client.adapters.langchain_adapter import ElephantineLangChainMemory

@pytest.mark.asyncio
async def test_async_client_with_transport():
    transport = ASGITransport(app=app)
    client = AsyncElephantineClient(base_url="http://test")
    client._client = AsyncClient(transport=transport, base_url="http://test")

    # Test remember
    res = await client.remember(
        content="Developer David likes Neovim and Python.",
        category="preference",
        source_agent="sdk-test",
        entity_key="david:editor"
    )
    assert res["status"] == "stored"

    # Test recall
    rec = await client.recall(query="What editor does David use?", top_k=3)
    assert rec["total_found"] >= 1
    assert "neovim" in rec["memories"][0]["source_agent"] or "neovim" in rec["memories"][0]["content"].lower()

    # Test query_graph
    graph = await client.query_graph(entity="david", max_hops=1)
    assert "entity" in graph
    assert graph["total_triplets"] >= 1

    await client.close()


def test_sync_client_and_langchain_adapter():
    from starlette.testclient import TestClient
    client = ElephantineClient(base_url="http://test")
    client._client = TestClient(app=app, base_url="http://test")

    memory = ElephantineLangChainMemory(client=client, source_agent="sdk-test")
    assert memory.memory_variables == ["history"]

    # Save context
    memory.save_context(
        inputs={"input": "I want to build a CPU-native app"},
        outputs={"output": "Elephantine is the ideal choice."}
    )

    # Load memory variables
    vars = memory.load_memory_variables({"input": "CPU-native"})
    assert "history" in vars
    client.close()
