# eval/evaluate_coverage.py
import subprocess
import sys
from pathlib import Path

def run_coverage(functions_dir="data/functions", tests_dir="data/generated_tests"):
    """Run coverage on generated tests using coverage.py."""
    
    # Create output directory
    output_dir = Path("analysis/coverage_html")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use coverage run to execute pytest and track coverage
    proc = subprocess.run(
        [sys.executable, "-m", "coverage", "run", "--source=" + functions_dir, "-m", "pytest", tests_dir, "-q"],
        capture_output=True,
        text=True
    )
    
    print("Pytest output:")
    print(proc.stdout)
    if proc.stderr:
        print("Stderr:", proc.stderr)
    
    if proc.returncode != 0:
        print(f"⚠️ Tests failed with exit code {proc.returncode}")
    else:
        print("✅ Tests passed")
    
    # Generate coverage report
    report_proc = subprocess.run(
        [sys.executable, "-m", "coverage", "html", "-d", str(output_dir)],
        capture_output=True,
        text=True
    )
    
    if report_proc.returncode == 0:
        print(f"✅ Coverage report generated in {output_dir}/index.html")
    else:
        print(f"⚠️ Error generating report: {report_proc.stderr}")
    
    # Also print text report
    print("\n" + "="*60)
    print("Coverage Summary:")
    print("="*60)
    text_report = subprocess.run([sys.executable, "-m", "coverage", "report"], capture_output=True, text=True)
    print(text_report.stdout)

if __name__ == "__main__":
    run_coverage()
