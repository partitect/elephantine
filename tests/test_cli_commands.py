import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
from elephantine.cli import run_remember_cli, run_recall_cli

def test_run_remember_cli(capsys):
    mock_client = MagicMock()
    mock_client.remember.return_value = {
        "id": "mem-12345",
        "conflicts_resolved": []
    }
    
    with patch("elephantine.client.ElephantineClient", return_value=mock_client):
        args = Namespace(
            content="Testing elephantine remember CLI",
            category="testing",
            workspace="test-ws",
            authority=0.9,
            entity_key="test:key",
            source_agent="cli-test",
            base_url="http://127.0.0.1:8765"
        )
        run_remember_cli(args)
        
        captured = capsys.readouterr()
        assert "Memory stored successfully" in captured.out
        assert "mem-12345" in captured.out
        assert "test-ws" in captured.out

def test_run_recall_cli(capsys):
    mock_client = MagicMock()
    mock_client.recall.return_value = {
        "query": "database preferences",
        "latency_ms": 32.5,
        "memories": [
            {
                "category": "architecture",
                "role_authority": 1.0,
                "similarity_score": 0.95,
                "content": "Use PostgreSQL 16"
            }
        ],
        "graph_triplets": [
            {"subject": "project", "predicate": "uses", "object": "postgresql"}
        ]
    }
    
    with patch("elephantine.client.ElephantineClient", return_value=mock_client):
        args = Namespace(
            query="database preferences",
            workspace="test-ws",
            category=None,
            top_k=3,
            base_url="http://127.0.0.1:8765"
        )
        run_recall_cli(args)
        
        captured = capsys.readouterr()
        assert "Elephantine Recall" in captured.out
        assert "Use PostgreSQL 16" in captured.out
        assert "uses" in captured.out
