# eval/test_metrics_utils.py
import pytest
from metrics_utils import embedding_cosine, bleu_score

def test_embedding_cosine_identical():
    """Test that identical strings have high cosine similarity."""
    score = embedding_cosine("test function", "test function")
    assert score > 0.99, f"Expected high similarity for identical strings, got {score}"

def test_embedding_cosine_different():
    """Test that different strings have lower cosine similarity."""
    score = embedding_cosine("apple orange", "cat dog")
    assert score < 0.5, f"Expected low similarity for different strings, got {score}"

def test_bleu_score_identical():
    """Test BLEU score for identical strings."""
    score = bleu_score("this is a test", "this is a test")
    assert score == 1.0, f"Expected BLEU=1.0 for identical strings, got {score}"

def test_bleu_score_partial():
    """Test BLEU score for partially matching strings."""
    score = bleu_score("this is a test", "this is a test function")
    assert 0 < score < 1.0, f"Expected BLEU between 0 and 1 for partial match, got {score}"

def test_bleu_score_different():
    """Test BLEU score for completely different strings."""
    score = bleu_score("apple orange", "cat dog")
    assert score == 0.0, f"Expected BLEU=0 for completely different strings, got {score}"
