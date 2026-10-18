import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# The pipeline task family's builder code (golden/pipeline/pipetask): hidden from arms, tested here.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "golden" / "pipeline"))

# Fails a full CI run that gets much slower (tests/time_budget.py).
pytest_plugins = ["time_budget"]
