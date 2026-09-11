import pytest
from httpx import AsyncClient, ASGITransport
from memagent.api.app import app
from memagent.core.graph_extractor import RuleBasedGraphExtractor

def test_graph_extractor_patterns():
    extractor = RuleBasedGraphExtractor()
    text = 'Alice prefers PostgreSQL and Bob works at Google. The backend service depends on Redis.'
    triplets = extractor.extract_triplets(text)
    
    assert len(triplets) >= 2
    pairs = [(t.subject, t.predicate, t.object) for t in triplets]
    assert ('alice', 'uses', 'postgresql') in pairs
    assert ('bob', 'works_at', 'google') in pairs

@pytest.mark.asyncio
async def test_graph_api_and_enrichment():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        # 1. Remember fact with triplet relationships
        rem_res = await client.post('/remember', json={
            'content': 'Developer Charlie uses Rust for systems programming.',
            'category': 'fact',
            'source_agent': 'graph-agent',
            'entity_key': 'charlie:skills'
        })
        assert rem_res.status_code == 200

        # 2. Query knowledge graph neighborhood for charlie
        graph_res = await client.post('/graph/query', json={
            'entity': 'charlie',
            'max_hops': 1
        })
        assert graph_res.status_code == 200
        g_data = graph_res.json()
        assert g_data['entity'] == 'charlie'
        assert g_data['total_triplets'] >= 1
        trip = g_data['triplets'][0]
        assert trip['subject'] == 'charlie'
        assert trip['predicate'] == 'uses'
        assert trip['object'] == 'rust'

        # 3. Test recall graph enrichment
        recall_res = await client.post('/recall', json={
            'query': 'Tell me about charlie and programming',
            'top_k': 3
        })
        assert recall_res.status_code == 200
        r_data = recall_res.json()
        assert 'graph_triplets' in r_data
        assert any(t['subject'] == 'charlie' for t in r_data['graph_triplets'])
