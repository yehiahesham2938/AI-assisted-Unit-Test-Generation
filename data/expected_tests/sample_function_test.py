from sample_function import add, is_even, divide
import pytest

def test_add_basic():
    assert add(3, 5) == 8

def test_is_even_true():
    assert is_even(4) is True

def test_is_even_false():
    assert is_even(5) is False

def test_divide_normal():
    assert divide(10, 2) == 5

def test_divide_zero():
    with pytest.raises(ValueError):
        divide(1, 0)
