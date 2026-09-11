import pytest
import numpy as np
from memagent.core.embedder import OnnxCpuEmbedder

def test_embedder_dimensions_and_norm():
    embedder = OnnxCpuEmbedder()
    text = "The database port is set to 5432."
    vector = embedder.embed_text(text)
    
    assert isinstance(vector, list)
    assert len(vector) == 384
    
    # Check normalized L2 norm is ~1.0
    norm = np.linalg.norm(np.array(vector))
    assert np.isclose(norm, 1.0, atol=1e-3)

def test_embedder_batch():
    embedder = OnnxCpuEmbedder()
    texts = [
        "First fact about user preferences.",
        "Second fact about system architecture."
    ]
    vectors = embedder.embed_batch(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384
