"""Public contract for the frozen opt-in regression deployment estimator."""

import gc
import importlib.abc
import pickle
import subprocess
import sys
import weakref
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
import pytest
from scipy import sparse
from sklearn.base import clone, is_regressor
from sklearn.exceptions import NotFittedError
from threadpoolctl import threadpool_limits

from codadapt.experimental import SafeBlendRegressor
from codadapt.experimental import _safe_blend as implementation


@pytest.fixture(scope="module")
def regression_data():
    rng = np.random.default_rng(81077)
    a = rng.normal(size=(160, 2))
    cat = np.asarray(["a", "b", "c"])[rng.integers(3, size=160)]
    y = a[:, 0] ** 2 + 1.8 * a[:, 1] * (cat == "a") + 0.3 * rng.normal(size=160)
    x = pd.DataFrame(dict(first=a[:, 0], second=a[:, 1], category=cat))
    x.loc[[2, 11, 60, 75], "first"] = np.nan
    x.loc[[1, 9, 30], "category"] = None
    return x, y


@pytest.fixture(scope="module")
def fitted(regression_data):
    teacher_module = pytest.importorskip("lightgbm")
    if teacher_module.__version__ != "4.7.0":
        pytest.skip("Frozen fit requires lightgbm==4.7.0")
    x, y = regression_data
    refs = []
    original = implementation.teacher_class

    def factory(**params):
        model = teacher_module.LGBMRegressor(**params)
        refs.append(weakref.ref(model))
        return model

    implementation.teacher_class = lambda: factory
    try:
        with threadpool_limits(limits=4):
            result = SafeBlendRegressor(random_state=123).fit(x, y)
    finally:
        implementation.teacher_class = original
    gc.collect()
    assert refs and all(ref() is None for ref in refs)
    return result


def test_import_opt_in_and_minimal_parameters():
    import codadapt

    assert not hasattr(codadapt, "SafeBlendRegressor")
    model = SafeBlendRegressor(random_state=42, verbosity=0, n_jobs=2)
    assert is_regressor(model)
    assert clone(model).get_params() == dict(random_state=42, verbosity=0, n_jobs=2)
    for forbidden in ["alpha", "capacity", "teacher", "validation_fraction", "safety_threshold"]:
        with pytest.raises(ValueError):
            model.set_params(**{forbidden: 1})


def test_fitted_state_before_fit():
    model = SafeBlendRegressor()
    with pytest.raises(NotFittedError):
        model.predict(np.zeros((8, 2)))
    with pytest.raises(NotFittedError):
        _ = model.branch_


def test_regression_fit_and_diagnostics(fitted, regression_data):
    x, _ = regression_data
    with threadpool_limits(limits=4):
        prediction = fitted.predict(x)
    assert prediction.shape == (160,) and np.isfinite(prediction).all()
    assert fitted.alpha_ == 0.27388247139831357
    assert fitted.n_features_in_ == 3
    assert list(fitted.feature_names_in_) == list(x.columns)
    diagnostics = fitted.fit_diagnostics_
    assert diagnostics["train_rows"] == 120 and diagnostics["validation_rows"] == 40
    assert diagnostics["validation_fraction"] == 0.25 and not diagnostics["refit"]
    assert not diagnostics["teacher_retained"] and not hasattr(fitted, "teacher_")
    assert set(vars(fitted)) == {
        "random_state",
        "verbosity",
        "n_jobs",
        "_artifact",
        "_validation",
        "_fit_record",
    }


def test_deterministic_random_state(fitted, regression_data):
    x, y = regression_data
    with threadpool_limits(limits=4):
        repeated = clone(fitted).fit(x, y)
        assert repeated.predict(x).tobytes() == fitted.predict(x).tobytes()
    assert repeated.branch_ == fitted.branch_


def test_blend_branch_formula(fitted, regression_data):
    x, _ = regression_data
    assert fitted.branch_ == "BLEND"
    assert fitted.compiled_ is fitted.compiler_ and fitted.compiled_ is not None
    with threadpool_limits(limits=4):
        a = fitted._artifact.shared_preprocessing.transform(x)
        b = fitted.base_.predict(a)
        c = implementation.SafeBlendArtifact.__module__  # qualified public deployment state
        assert c.startswith("codadapt.experimental.")
        from codadapt.experimental._safe_blend_runtime import compiler_predict

        expected = b + fitted.alpha_ * (compiler_predict(fitted.compiled_, a) - b)
        assert expected.tobytes() == fitted.predict(x).tobytes()


def test_base_branch_drops_compiler(monkeypatch, fitted, regression_data):
    # Test double exercises the finalization branch only; real safety is tested below
    # and both naturally selected branches are covered by the 90-case research replay.
    x, y = regression_data
    original = implementation.choose_branch

    def force_base(y, base, compiled):
        _, vb, vz = original(y, base, compiled)
        return "BASE", vb, vz

    monkeypatch.setattr(implementation, "choose_branch", force_base)
    with threadpool_limits(limits=4):
        model = SafeBlendRegressor(random_state=123).fit(x, y)
        assert model.branch_ == "BASE"
        assert model.compiled_ is model.compiler_ is None
        assert not hasattr(model._artifact, "compiled")
        assert (
            model.predict(x).tobytes()
            == fitted.base_.predict(fitted._artifact.shared_preprocessing.transform(x)).tobytes()
        )
    assert not hasattr(model, "teacher_")


def test_numeric_array_fit(regression_data):
    pytest.importorskip("lightgbm")
    x, y = regression_data
    a = x.iloc[:, :2].to_numpy()
    with threadpool_limits(limits=4):
        model = SafeBlendRegressor(random_state=123).fit(a, y)
        assert np.isfinite(model.predict(a)).all()
    assert model.n_features_in_ == 2


@pytest.mark.parametrize("format", ["pickle", "joblib"])
def test_persistence_without_teacher(fitted, regression_data, tmp_path, format):
    x, _ = regression_data
    model_path, data_path = tmp_path / "model", tmp_path / "data.pkl"
    data_path.write_bytes(pickle.dumps(x))
    with threadpool_limits(limits=4):
        np.save(tmp_path / "expected.npy", fitted.predict(x))
    if format == "pickle":
        model_path.write_bytes(pickle.dumps(fitted, protocol=5))
    else:
        joblib.dump(fitted, model_path)
    script = """import importlib.abc,pickle,sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'lightgbm','research'+'_private'} or fullname in {'codadapt.experimental._safe_blend_training','codadapt.experimental._safe_blend_queries'}:
            raise ImportError('fit/teacher/research unavailable')
sys.meta_path.insert(0,Block())
import joblib,numpy as np
from pathlib import Path
from threadpoolctl import threadpool_limits
from codadapt.experimental import SafeBlendRegressor
def forbid(*args,**kwargs): raise AssertionError('reload must not fit')
SafeBlendRegressor.fit=forbid
root=Path(sys.argv[1])
model=pickle.loads((root/'model').read_bytes()) if sys.argv[2]=='pickle' else joblib.load(root/'model')
x=pickle.loads((root/'data.pkl').read_bytes())
with threadpool_limits(limits=4):
    assert model.predict(x).tobytes()==np.load(root/'expected.npy').tobytes()
assert not any(k.split('.')[0] in {'lightgbm','research'+'_private'} for k in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), format],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_and_categorical_unseen(fitted, regression_data):
    x, _ = regression_data
    x = x.iloc[:12].copy()
    x.loc[x.index[:3], "category"] = ["new", None, "a"]
    x.iloc[4, 0] = np.nan
    with threadpool_limits(limits=4):
        assert np.isfinite(fitted.predict(x)).all()
        categorical = x.copy()
        categorical["category"] = pd.Categorical(categorical["category"])
        assert fitted.predict(categorical).tobytes() == fitted.predict(x).tobytes()


def test_frozen_safety_tie_loss_and_win():
    y = np.arange(10, dtype=float)
    assert implementation.choose_branch(y, y, y)[0] == "BASE"
    assert implementation.choose_branch(y, y, y + 1)[0] == "BASE"
    assert implementation.choose_branch(y, y + 1, y)[0] == "BLEND"


def test_missing_teacher_dependency(monkeypatch):
    class Block(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".")[0] == "lightgbm":
                raise ImportError("teacher unavailable")

    monkeypatch.delitem(sys.modules, "lightgbm", raising=False)
    monkeypatch.setattr(sys, "meta_path", [Block(), *sys.meta_path])
    with pytest.raises(ImportError, match=r"Install codadapt\[safeblend\]"):
        SafeBlendRegressor().fit(np.zeros((12, 2)), np.arange(12, dtype=float))


def test_wrong_teacher_version(monkeypatch):
    monkeypatch.setitem(sys.modules, "lightgbm", SimpleNamespace(__version__="4.6.0"))
    with pytest.raises(RuntimeError, match="lightgbm==4.7.0"):
        implementation.teacher_class()


@pytest.mark.parametrize(
    "y",
    [
        np.arange(12) % 2,
        np.ones(12, dtype=bool),
        np.array(list("abc") * 4),
        pd.Series(pd.Categorical(list("abc") * 4)),
        np.zeros((12, 2)),
        np.full(12, np.nan),
    ],
)
def test_unsupported_target(y):
    with pytest.raises(ValueError):
        SafeBlendRegressor().fit(np.zeros((12, 2)), y)


def test_numeric_counts_not_automatically_classified():
    # Numeric multiclass IDs and integer counts cannot be distinguished by the API.
    _, y, _ = implementation.validate_training_input(np.zeros((12, 2)), np.arange(12) % 3)
    assert y.dtype == np.float64


@pytest.mark.parametrize(
    "params",
    [
        dict(random_state=None),
        dict(random_state=True),
        dict(n_jobs=0),
        dict(n_jobs=5),
        dict(verbosity=2),
    ],
)
def test_invalid_parameters(params):
    with pytest.raises(ValueError):
        SafeBlendRegressor(**params).fit(np.zeros((12, 2)), np.arange(12, dtype=float))


def test_malformed_schema(fitted, regression_data):
    x, _ = regression_data
    for probe in [
        x.iloc[:0],
        x.iloc[:, ::-1],
        x.iloc[:, :-1],
        sparse.csr_matrix((12, 3)),
        np.ones(12),
    ]:
        with pytest.raises(ValueError):
            fitted.predict(probe)
