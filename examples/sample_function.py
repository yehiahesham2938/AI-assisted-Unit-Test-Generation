# examples/sample_function.py
def add(a, b):
    """Return sum of a and b"""
    return a + b

def is_even(n):
    return n % 2 == 0

def divide(a, b):
    if b == 0:
        raise ValueError("division by zero")
    return a / b
