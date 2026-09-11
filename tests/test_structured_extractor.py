import pytest
from elephantine.core.structured_extractor import (
    ExtractedFactItem,
    ExtractionOutputSchema,
    GroundingValidator,
    StructuredMemoryExtractor
)

def test_pydantic_schema_validation():
    # Valid item
    item = ExtractedFactItem(
        fact="The database server runs on port 5432.",
        entity_key="config:port",
        category="config",
        confidence=0.95,
        grounding_tokens=["database", "server", "port", "5432"]
    )
    assert item.fact == "The database server runs on port 5432."
    assert item.confidence == 0.95

    # Test blank fact rejection
    with pytest.raises(ValueError):
        ExtractedFactItem(fact="   ", confidence=0.8)

def test_grounding_validator_blocks_hallucination():
    validator = GroundingValidator()
    raw_prompt = "I live in Berlin and work with Python and PostgreSQL."
    
    # Grounded fact
    grounded_item = ExtractedFactItem(
        fact="User lives in Berlin and develops with Python.",
        confidence=0.9
    )
    assert validator.verify_grounding(raw_prompt, grounded_item) is True

    # Hallucinated fact (model generated information not in prompt)
    hallucinated_item = ExtractedFactItem(
        fact="User is a senior manager at Apple in Cupertino with 15 years experience.",
        confidence=0.95
    )
    assert validator.verify_grounding(raw_prompt, hallucinated_item) is False

def test_structured_extractor_pipeline():
    extractor = StructuredMemoryExtractor()
    
    # 1. Fact with high grounding
    res = extractor.extract_with_grounding("My favorite database is PostgreSQL 16.")
    assert len(res) >= 1
    assert res[0].confidence >= 0.8
    assert "postgresql" in res[0].fact.lower()

    # 2. Trivial chitchat should produce 0 memories
    empty_res = extractor.extract_with_grounding("Hello! Okay thanks.")
    assert len(empty_res) == 0

def test_json_schema_export():
    extractor = StructuredMemoryExtractor()
    schema = extractor.get_json_schema()
    assert "properties" in schema
    assert "facts" in schema["properties"]
    assert "has_meaningful_memory" in schema["properties"]
