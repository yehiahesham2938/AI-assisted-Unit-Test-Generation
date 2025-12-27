import pytest
from sample_function import add, is_even, divide

def test_add_basic():
    """Test add function with basic inputs."""
    assert add(3, 5) == 8
    assert add(0, 0) == 0
    assert add(-1, 1) == 0

def test_is_even_true():
    """Test is_even returns True for even numbers."""
    assert is_even(4) is True
    assert is_even(0) is True
    assert is_even(-2) is True

def test_is_even_false():
    """Test is_even returns False for odd numbers."""
    assert is_even(5) is False
    assert is_even(1) is False
    assert is_even(-1) is False

def test_divide_normal():
    """Test divide with normal inputs."""
    assert divide(10, 2) == 5.0
    assert divide(20, 4) == 5.0
    assert divide(7, 2) == 3.5

def test_divide_zero():
    """Test divide raises ValueError on division by zero."""
    with pytest.raises(ValueError, match="division by zero"):
        divide(1, 0)
