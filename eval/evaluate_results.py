# eval/evaluate_results.py
import subprocess, json, os, glob
from pathlib import Path
import coverage
import importlib.util
import sys

def run_pytest_on_generated_tests(generated_dir="data/generated_tests", functions_dir="data/functions"):
    # We will copy functions files into a temp test runner dir so pytest can import them
    tmpdir = Path("eval/tmp_test_env")
    tmpdir.mkdir(parents=True, exist_ok=True)
    # copy functions
    for f in Path(functions_dir).glob("*.py"):
        (tmpdir / f.name).write_text(f.read_text())
    # copy generated tests
    for t in Path(generated_dir).glob("*.py"):
        (tmpdir / t.name).write_text(t.read_text())
    # run pytest in that directory and capture results
    cmd = [sys.executable, "-m", "pytest", str(tmpdir), "--maxfail=1", "-q", "--disable-warnings"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + "\n" + proc.stderr

if __name__ == "__main__":
    rc, out = run_pytest_on_generated_tests()
    print("Return code:", rc)
    print(out)
