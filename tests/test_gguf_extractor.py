import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from elephantine.core.gguf_extractor import LlamaCppEngine
from elephantine.core.structured_extractor import (
    StructuredMemoryExtractor,
    ExtractedFactItem,
    ExtractionOutputSchema
)

def test_gguf_engine_availability_check():
    engine = LlamaCppEngine(model_path=None)
    assert not engine.is_available

    fake_path = Path("./non_existent_model.gguf")
    engine_fake = LlamaCppEngine(model_path=fake_path)
    assert not engine_fake.is_available

def test_structured_extractor_graceful_fallback():
    # When GGUF is not configured, fallback to heuristic extraction must succeed
    extractor = StructuredMemoryExtractor()
    facts = extractor.extract_with_grounding("I prefer postgresql for production databases.")
    assert len(facts) >= 1
    assert "postgresql" in facts[0].fact.lower()
    assert facts[0].entity_key.startswith("pref:")

def test_gguf_engine_mocked_inference():
    mock_llm = MagicMock()
    mock_llm.create_completion.return_value = {
        "choices": [
            {
                "text": '{"has_meaningful_memory": true, "facts": [{"fact": "The user preference for database is postgresql", "entity_key": "pref:db", "category": "preference", "confidence": 0.95, "grounding_tokens": ["postgresql", "database"]}]}'
            }
        ]
    }

    with patch("elephantine.core.gguf_extractor.LlamaCppEngine.is_available", True):
        engine = LlamaCppEngine(model_path=Path("dummy.gguf"))
        engine._llm = mock_llm

        facts = engine.extract_memories("I want postgresql as my primary database")
        assert len(facts) == 1
        assert facts[0].fact == "The user preference for database is postgresql"
        assert facts[0].entity_key == "pref:db"
