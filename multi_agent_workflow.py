import datetime
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from generate_tests import load_config, generate_tests_for_source, log_jsonl


def _static_safety_checks(tests: str) -> Dict[str, Any]:
    """Lightweight, rule-based safety and quality checks for generated tests.

    Returns a dict with:
      - safe: bool
      - reasons: List[str]
      - warnings: List[str]
      - hallucination: bool  # e.g. meaningless assertions
    """
    unsafe_patterns = [
        "import os",
        "import subprocess",
        "open(",
        "os.remove",
        "shutil.rmtree",
        "requests.",
        "httpx.",
        "import socket",
    ]
    reasons: List[str] = []
    warnings: List[str] = []
    hallucination: bool = False

    lowered = tests.lower()
    for pattern in unsafe_patterns:
        if pattern.lower() in lowered:
            reasons.append(f"Detected potentially unsafe pattern: {pattern}")

    if "assert " not in tests:
        warnings.append("No assert statements found in generated tests.")

    # Detect trivial / meaningless assertions such as plain "assert True"
    if "assert True" in tests:
        hallucination = True
        reasons.append("Meaningless assertion detected: 'assert True' found in generated tests.")

    safe = not reasons
    return {"safe": safe, "reasons": reasons, "warnings": warnings, "hallucination": hallucination}


def _run_pytest_in_temp(source_code: str, tests: str) -> Tuple[bool, str]:
    """Run pytest in a temporary sandbox on the generated tests.

    This is used by the validator agent to get execution feedback.
    """
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        module_path = tmpdir / "module_under_test.py"
        test_path = tmpdir / "test_module_under_test.py"
        module_path.write_text(source_code, encoding="utf-8")
        test_path.write_text(tests, encoding="utf-8")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(tmpdir),
            "-q",
            "--disable-warnings",
            "--maxfail=1",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        passed = proc.returncode == 0
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return passed, out[:4000]


def generate_tests_validated(
    source_code: str,
    cfg: Optional[Dict[str, Any]] = None,
    run_pytest: bool = True,
) -> Dict[str, Any]:
    """Generator–validator pipeline around `generate_tests_for_source`.

    Steps:
      1. Generator agent calls the existing LLM-based generator.
      2. Validator agent performs:
         - Syntax check
         - Static safety heuristics
         - Optional pytest run in a sandbox
      3. Returns tests, prompt, generator metadata, and a governance report.
    """
    if cfg is None:
        cfg = load_config("config.yaml")

    # Generator agent
    tests, prompt, gen_metadata = generate_tests_for_source(source_code, cfg)

    # Syntax validation
    syntax_ok = True
    syntax_error = None
    try:
        compile(tests, "<generated_tests>", "exec")
    except SyntaxError as e:
        syntax_ok = False
        syntax_error = str(e)

    # Static safety checks
    safety = _static_safety_checks(tests)

    # Optional execution-based validation
    pytest_passed: Optional[bool] = None
    pytest_output: Optional[str] = None
    if run_pytest and syntax_ok:
        try:
            pytest_passed, pytest_output = _run_pytest_in_temp(source_code, tests)
        except Exception as e:
            safety["warnings"].append(f"Pytest validation failed to run: {e}")

    governance = {
        "safe": bool(safety["safe"] and syntax_ok),
        "syntax_ok": syntax_ok,
        "syntax_error": syntax_error,
        "reasons": safety["reasons"],
        "warnings": safety["warnings"],
        "pytest_passed": pytest_passed,
        "hallucination": bool(safety.get("hallucination")),
    }

    # Log for accountability & analysis
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "source_len": len(source_code),
        "tests_len": len(tests),
        "generator_metadata": gen_metadata,
        "governance": governance,
    }
    # Ensure logs directory exists for accountability logging
    log_path = Path("logs") / "multi_agent_workflow.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_jsonl(entry, str(log_path))

    return {
        "tests": tests,
        "prompt": prompt,
        "generator_metadata": gen_metadata,
        "governance": governance,
        "pytest_output": pytest_output,
    }
