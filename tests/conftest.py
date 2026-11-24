"""Use the built wheel for distribution-bound regression checks."""
from pathlib import Path
import os

os.environ.setdefault("CODADAPT_TEST_DIST", str(Path(__file__).resolve().parents[1] / "dist"))
