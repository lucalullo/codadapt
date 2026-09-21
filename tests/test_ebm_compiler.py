"""Optional integration tests against real EBM; no research-private dependencies."""

import copy
import importlib.util
import os
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone, is_classifier, is_regressor
from sklearn.exceptions import NotFittedError

from codadapt.experimental import CompilationError, compile_ebm

ebm = pytest.importorskip("interpret.glassbox")


@pytest.fixture(scope="module", params=[False, True], ids=["regression", "binary"])
def case(request):
    rng = np.random.default_rng(42)
    x = pd.DataFrame(
        {
            "number": rng.normal(size=320),
            "category": pd.Categorical(rng.choice(["a", "b", "c"], 320)),
        }
    )
    y = x.number.to_numpy() + (x.category == "a").to_numpy() * 0.7
    x.loc[::17, "number"] = np.nan
    x.loc[::19, "category"] = np.nan
    binary = request.param
    cls = ebm.ExplainableBoostingClassifier if binary else ebm.ExplainableBoostingRegressor
    labels = np.where(y > 0, "yes", "no") if binary else y
    t = cls(
        interactions=0, max_bins=16, outer_bags=1, max_rounds=25, n_jobs=1, random_state=42
    ).fit(x.iloc[:240], labels[:240])
    return t, x.iloc[240:].copy(), binary


def test_fidelity_labels_metadata_and_sklearn(case):
    t, x, binary = case
    m = compile_ebm(t, X_verify=x)
    for n in [0, 1, 8, 32, 33, 128, 1001]:
        z = x.iloc[np.arange(n) % len(x)]
        expected = t.decision_function(z) if binary and n else None
        if n:
            raw = m.decision_function(z) if binary else m.predict(z)
            expected = expected if binary else t.predict(z)
            np.testing.assert_array_equal(raw.view("u8"), expected.view("u8"))
        assert m.predict(z).shape == (n,)
    if binary:
        np.testing.assert_allclose(m.predict_proba(x), t.predict_proba(x), atol=1e-15, rtol=0)
        np.testing.assert_array_equal(m.predict(x), t.predict(x))
        np.testing.assert_array_equal(m.classes_, t.classes_)
        assert is_classifier(m)
    else:
        assert is_regressor(m)
        assert not hasattr(m, "predict_proba")
    assert m.compiler_status_ == "SAFE"
    assert m.compiled_state_count_ == m.required_capacity_
    assert m.estimated_memory_bytes_ > 0
    assert m.verification_error_["raw_bit_mismatches"] == 0
    assert m.n_features_in_ == 2
    assert not any(v is t for v in vars(m).values())
    with pytest.raises(NotFittedError):
        clone(m).predict(x)
    with pytest.raises(TypeError, match="not trainable"):
        m.fit(x)


def test_missing_unseen_reorder_and_persistence(case):
    t, x, binary = case
    m = compile_ebm(t, X_verify=x)
    z = x.iloc[:6].copy()
    z["category"] = ["unseen", None, "a", "b", "c", "a"]
    z.loc[z.index[0], "number"] = np.nan
    z = z.iloc[:, ::-1]
    raw = m.decision_function(z) if binary else m.predict(z)
    ref = t.decision_function(z) if binary else t.predict(z)
    np.testing.assert_array_equal(raw.view("u8"), ref.view("u8"))
    restored = pickle.loads(pickle.dumps(m))
    np.testing.assert_array_equal(restored.predict(z), m.predict(z))
    assert restored._runtime_.cache == {} or len(restored._runtime_.cache) <= 2
    for num, edges, values in restored._runtime_.specs:
        if num:
            assert np.shares_memory(values, restored._runtime_.value_buffer)
            assert edges.size == 0 or np.shares_memory(edges, restored._runtime_.edge_buffer)


def test_capacity_and_schema_rejections(case):
    t, x, _ = case
    m = compile_ebm(t, X_verify=x)
    for cap in [-1, True, 1.5, m.required_capacity_ - 1]:
        with pytest.raises(CompilationError, match="REJECT"):
            compile_ebm(t, X_verify=x, max_states=cap)
    assert compile_ebm(t, X_verify=x, max_states=m.required_capacity_).compiler_status_ == "SAFE"
    for bad in [x.iloc[:0], x.to_numpy(), x.iloc[:, ::-1], x.rename(columns={"number": "oops"})]:
        with pytest.raises(CompilationError):
            compile_ebm(t, X_verify=bad)
    for bad in [
        x.assign(extra=0),
        x.drop(columns="number"),
        x.assign(number="invalid"),
        x.assign(number=1j),
        x.assign(category=123),
    ]:
        with pytest.raises(ValueError):
            m.predict(bad)
    with pytest.raises(CompilationError):
        compile_ebm(object(), X_verify=x)


@pytest.mark.parametrize("problem", ["interaction", "multiclass", "nonfinite", "cuts", "link"])
def test_unsupported_structure(case, problem):
    t, x, _ = case
    t = copy.deepcopy(t)
    if problem == "interaction":
        t.term_features_[0] = (0, 1)
    elif problem == "multiclass":
        t.intercept_ = np.zeros(3)
    elif problem == "nonfinite":
        t.term_scores_[0][1] = np.nan
    elif problem == "cuts":
        t.bins_[0][0] = np.array([1.0, 0.0])
    else:
        t.link_ = "unsupported"
    with pytest.raises(CompilationError):
        compile_ebm(t, X_verify=x)


def test_verification_rejects_teacher_output_mismatch(case, monkeypatch):
    t, x, binary = case
    t = copy.deepcopy(t)
    method = "decision_function" if binary else "predict"
    original = getattr(t, method)
    monkeypatch.setattr(t, method, lambda x: original(x) + 1)
    with pytest.raises(CompilationError, match="raw-score verification"):
        compile_ebm(t, X_verify=x)


def test_probability_verification_rejects_mismatch(case, monkeypatch):
    t, x, binary = case
    if not binary:
        return
    t = copy.deepcopy(t)
    monkeypatch.setattr(t, "predict_proba", lambda x: np.zeros((len(x), 2)))
    with pytest.raises(CompilationError, match="probability verification"):
        compile_ebm(t, X_verify=x)


def test_categorical_only_and_nullable_numeric():
    x = pd.DataFrame({"category": ["a", "b", None] * 30})
    y = np.arange(90) % 3
    t = ebm.ExplainableBoostingRegressor(interactions=0, outer_bags=1, max_rounds=5, n_jobs=1).fit(
        x, y
    )
    m = compile_ebm(t, X_verify=x)
    np.testing.assert_array_equal(m.predict(x), t.predict(x))
    x = pd.DataFrame({"number": pd.array([1, 2, None] * 30, dtype="Int64")})
    t.fit(x, y)
    m = compile_ebm(t, X_verify=x)
    np.testing.assert_array_equal(m.predict(x), t.predict(x))


def test_new_process_without_teacher_import(case, tmp_path, dependency_paths):
    t, x, binary = case
    m = compile_ebm(t, X_verify=x)
    payload = tmp_path / "compiled.pkl"
    payload.write_bytes(pickle.dumps((m, x, m.predict(x))))
    root = Path(importlib.util.find_spec("codadapt").origin).parents[1]
    script = tmp_path / "standalone.py"
    script.write_text(
        "import sys, importlib.abc, pickle\n"
        f"sys.path[:0] = {dependency_paths!r}\n"
        f"sys.path.insert(0, {str(root)!r})\n"
        "class Block(importlib.abc.MetaPathFinder):\n"
        " def find_spec(self, fullname, path=None, target=None):\n"
        "  if fullname.split('.')[0] == 'interpret': raise ImportError('blocked teacher')\n"
        "sys.meta_path.insert(0, Block())\n"
        'with open(sys.argv[1], "rb") as f: m,x,p=pickle.load(f)\n'
        "import numpy as np\nnp.testing.assert_array_equal(m.predict(x),p)\n"
        "assert not any(k.startswith('interpret') for k in sys.modules)\n",
        encoding="utf8",
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    p = subprocess.run(
        [sys.executable, "-I", str(script), str(payload)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0, p.stdout + p.stderr


def test_numeric_boundaries_and_float_bits(case):
    t, x, binary = case
    t = copy.deepcopy(t)
    cuts = t.bins_[0][0]
    a = np.r_[
        cuts,
        np.nextafter(cuts, -np.inf),
        np.nextafter(cuts, np.inf),
        -np.inf,
        np.inf,
        np.nan,
        -0.0,
        0.0,
        -1e308,
        1e308,
    ]
    z = pd.DataFrame({"number": a, "category": ["a"] * len(a)})
    # Equal adjacent cells can be coalesced; opposite signed zeros cannot.
    t.term_scores_[0][1:5] = [0.0, -0.0, 0.25, 0.25]
    m = compile_ebm(t, X_verify=z)
    for n in (1, 32, 33, 10000):
        probe = z.iloc[np.arange(n) % len(z)]
        raw = m.decision_function(probe) if binary else m.predict(probe)
        ref = t.decision_function(probe) if binary else t.predict(probe)
        np.testing.assert_array_equal(raw.view("u8"), ref.view("u8"))
