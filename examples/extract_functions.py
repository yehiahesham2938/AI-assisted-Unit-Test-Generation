# tools/extract_functions.py
import ast, sys
from pathlib import Path

def extract_funcs(file_path):
    src = open(file_path).read()
    mod = ast.parse(src)
    funcs = []
    for node in mod.body:
        if isinstance(node, ast.FunctionDef):
            start = node.lineno - 1
            end = node.end_lineno
            lines = src.splitlines()[start:end]
            funcs.append("\n".join(lines))
    return funcs

if __name__ == "__main__":
    for f in Path("data/functions").glob("*.py"):
        funcs = extract_funcs(f)
        print(f"\n{'='*60}")
        print(f"File: {f}")
        print(f"Found {len(funcs)} function(s)")
        print(f"{'='*60}")
        for i, func in enumerate(funcs, 1):
            print(f"\nFunction {i}:")
            print(func)
            print("-" * 40)
