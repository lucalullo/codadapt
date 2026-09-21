"""Resolve installed runtime dependencies for isolated offline subprocess tests."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def dependency_paths():
    # Only dependency directories: never inject the CodAdapt source into wheel tests.
    paths = []
    for name in ("numpy", "pandas", "scipy", "sklearn", "joblib", "threadpoolctl"):
        spec = importlib.util.find_spec(name)
        folder = Path(spec.origin).resolve().parent
        paths.append(str(folder.parent if spec.submodule_search_locations else folder))
    return list(dict.fromkeys(paths))
