"""Persistence must preserve predictions without retaining the training set."""

import os
import pickle
import subprocess
import sys

import joblib
import numpy as np
import pytest
from numpy.testing import assert_allclose

from codadapt import CodAdaptClassifier, CodAdaptRegressor


def fitted(binary=True, n=193):
    rng = np.random.default_rng(544)
    X = rng.normal(size=(n, 3))
    y = (X[:, 0] > 0).astype(int) if binary else X[:, 0] - X[:, 1]
    estimator = CodAdaptClassifier if binary else CodAdaptRegressor
    model = estimator(
        n_bins=8, n_tables=2, table_size=32, max_iter=4, early_stopping=False, random_state=8
    ).fit(X, y)
    return model, X


def retained_arrays(value, seen=None):
    seen = set() if seen is None else seen
    if id(value) in seen:
        return
    seen.add(id(value))
    if isinstance(value, np.ndarray):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from retained_arrays(item, seen)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from retained_arrays(item, seen)
    elif type(value).__module__.startswith("codadapt") and hasattr(value, "__dict__"):
        yield from retained_arrays(vars(value), seen)


@pytest.mark.parametrize("binary", [True, False])
def test_model_does_not_retain_dataset_sized_arrays(binary):
    model, X = fitted(binary)
    arrays = list(retained_arrays(model))
    assert arrays
    assert not any(len(X) in array.shape for array in arrays)
    larger, _ = fitted(binary, n=1931)
    assert len(pickle.dumps(larger)) < 2 * len(pickle.dumps(model)) + 4096


@pytest.mark.parametrize("binary", [True, False])
@pytest.mark.parametrize("serializer", ["pickle", "joblib"])
def test_roundtrip_in_new_process_without_refit(binary, serializer, tmp_path):
    model, X = fitted(binary)
    model_path = tmp_path / f"model.{serializer}"
    if serializer == "pickle":
        model_path.write_bytes(pickle.dumps(model))
    else:
        joblib.dump(model, model_path)
    query_path, output_path = tmp_path / "query.npy", tmp_path / "prediction.npy"
    np.save(query_path, X[:13])
    script = tmp_path / "load_and_predict.py"
    script.write_text(
        "import sys, pickle, joblib, numpy as np\n"
        "from codadapt import CodAdaptClassifier, CodAdaptRegressor\n"
        "def forbidden_fit(*args, **kwargs):\n    raise AssertionError('Loading must not fit')\n"
        "CodAdaptClassifier.fit = forbidden_fit\nCodAdaptRegressor.fit = forbidden_fit\n"
        "path, kind, query, output = sys.argv[1:]\n"
        "if kind == 'pickle':\n    with open(path, 'rb') as f:\n        model = pickle.load(f)\n"
        "else:\n    model = joblib.load(path)\n"
        "X = np.load(query)\n"
        "prediction = model.predict_proba(X) if hasattr(model, 'predict_proba') else model.predict(X)\n"
        "np.save(output, prediction)\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            str(script),
            str(model_path),
            serializer,
            str(query_path),
            str(output_path),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    expected = model.predict_proba(X[:13]) if binary else model.predict(X[:13])
    assert_allclose(np.load(output_path), expected, rtol=0, atol=0)
