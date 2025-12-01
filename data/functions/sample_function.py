def add(a, b):
    """Return the sum of a and b."""
    return a + b

def is_even(n):
    """Return True if n is even."""
    return n % 2 == 0

def divide(a, b):
    """Divide a by b, raising ValueError on division by zero."""
    if b == 0:
        raise ValueError("division by zero")
    return a / b
