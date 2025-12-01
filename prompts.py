# prompts.py
import yaml
from pathlib import Path

BASE_PROMPT = """You are an expert Python developer and unit-test writer.
Given the following Python function, write a clear, human-readable pytest unit test file that:
- uses descriptive test names
- includes docstring explaining what's being tested
- tests normal and an edge case if obvious
- is executable (no external dependencies)
Return only the test file contents (no extra commentary).
"""

FEW_SHOT_EXAMPLES = [
    {
        "func": "def add(a, b):\n    return a + b\n",
        "test": '''def test_add_two_positive_numbers():
    """Check add returns sum of two positive integers."""
    assert add(3, 5) == 8

def test_add_with_zero():
    """Check add returns the other operand if one is zero."""
    assert add(0, 7) == 7
'''
    },
    # add more few-shot examples if desired
]

def build_prompt(func_src: str, include_examples: bool = True, n_examples: int = 1):
    p = BASE_PROMPT + "\n\nFunction:\n" + func_src + "\n\n"
    if include_examples:
        p += "\n\nExamples:\n"
        for ex in FEW_SHOT_EXAMPLES[:n_examples]:
            p += "Function:\n" + ex["func"] + "\n\nTest:\n" + ex["test"] + "\n\n"
    p += "Now write the pytest tests:\n"
    return p
