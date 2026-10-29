"""Default wheel location for artifact-contract tests."""
from pathlib import Path
import os
os.environ.setdefault("CODADAPT_TEST_DIST",str(Path(__file__).resolve().parents[1]/"dist"))
