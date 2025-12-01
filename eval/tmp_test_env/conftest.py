import sys
from pathlib import Path

# Add functions directory to Python path for pytest
functions_path = Path(__file__).resolve().parent.parent / "functions"
if str(functions_path) not in sys.path:
    sys.path.insert(0, str(functions_path))
