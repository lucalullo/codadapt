"""Resource admission changes never change the predictive recipe."""

import pickle

import joblib
import numpy as np
import pytest
from sklearn.base import clone
from sklearn.exceptions import NotFittedError
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted

from codadapt import CodAdaptClassifier, CodAdaptRegressor


def fixture(kind, dtype=np.float64):
    x = np.random.RandomState(811).normal(size=(96, 4)).astype(dtype)
    y = (
        x[:, 0] + x[:, 1]
        if kind == "regression"
        else np.arange(len(x)) % (3 if kind == "multiclass" else 2)
    )
    cls = CodAdaptRegressor if kind == "regression" else CodAdaptClassifier
    return cls(random_state=81), x, y


@pytest.mark.parametrize("value", [0, -1, None, True, False, 1.5, np.nan, np.inf, "1024"])
def test_invalid_budget_rejected_at_fit(value):
    model, x, y = fixture("binary")
    model.set_params(memory_budget_mb=value)
    with pytest.raises(ValueError, match="memory_budget_mb.*positive integer"):
        model.fit(x, y)
    with pytest.raises(NotFittedError):
        check_is_fitted(model)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_budget_clone_pipeline_and_bitwise_predictions(kind, dtype):
    a, x, y = fixture(kind, dtype)
    b = clone(a).set_params(memory_budget_mb=1024)
    a.fit(x, y)
    b.fit(x, y)
    assert a.predict(x).tobytes() == b.predict(x).tobytes()
    if kind != "regression":
        assert a.predict_proba(x).tobytes() == b.predict_proba(x).tobytes()
    assert a.estimated_memory_bytes_ == b.estimated_memory_bytes_
    assert clone(b).get_params() == b.get_params()
    assert Pipeline([("model", b)]).get_params()["model__memory_budget_mb"] == 1024


def test_formula_default_dtype_and_external_validation_accounting():
    model = CodAdaptClassifier(memory_budget_mb=512)
    n, p = 699635, 21
    expected = n * (40 * p + 96) + 24 * (p + 24) * 131 + 65536
    with pytest.raises(ValueError, match="624.72 MiB.*512 MiB"):
        model._check_memory_budget(n, p)
    model.set_params(memory_budget_mb=1024)
    assert model._check_memory_budget(n, p) == expected
    for dtype in (np.float32, np.float64):
        xv = np.zeros((5, p), dtype=dtype)
        assert model._check_memory_budget(n, p, (xv, np.zeros(5))) == expected + 5 * (40 * p + 96)


def test_exact_budget_boundary_admitted_then_one_row_rejected():
    # 400 bytes/row + 6336 metadata bytes reaches exactly 11 MiB at 28820 rows.
    model = CodAdaptClassifier(n_tables=0, max_categories=30, memory_budget_mb=11)
    last, p = 28820, 8
    assert model._check_memory_budget(last - 1, p) < 11 * 2**20
    assert model._check_memory_budget(last, p) == 11 * 2**20
    with pytest.raises(ValueError, match="exceeds"):
        model._check_memory_budget(last + 1, p)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
@pytest.mark.parametrize("budget", [1, np.int64(512), 1024])
def test_supported_budget_values_are_resource_only(kind, budget):
    model, x, y = fixture(kind)
    model.set_params(memory_budget_mb=budget).fit(x, y)
    assert model.memory_budget_mb == budget
    assert model.estimated_memory_bytes_ <= int(budget) * 2**20
    assert np.isfinite(model.predict(x)).all()


@pytest.mark.parametrize("budget", [np.int64(2**63 - 1), 2**256])
def test_large_positive_integer_budget_does_not_overflow_or_allocate(budget):
    model = CodAdaptClassifier(memory_budget_mb=budget)
    model._validate_parameters()
    # The budget is a comparison threshold, never an allocation dimension.
    assert model._check_memory_budget(100, 4) == CodAdaptClassifier()._check_memory_budget(100, 4)


def test_external_validation_exact_boundary_then_rejection():
    model = CodAdaptClassifier(n_tables=0, max_categories=30, memory_budget_mb=11)
    validation = (np.zeros((1, 8)), np.zeros(1))
    assert model._check_memory_budget(28819, 8, validation) == 11 * 2**20
    with pytest.raises(ValueError, match="1 external validation rows"):
        model._check_memory_budget(28820, 8, validation)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
@pytest.mark.parametrize("refit", [False, True])
def test_large_reject_atomicity_without_large_allocation(kind, refit, monkeypatch):
    model, x, y = fixture(kind)
    model.set_params(memory_budget_mb=512)
    if refit:
        model.fit(x, y)
    from codadapt.preprocessing import BucketEncoder

    def forbidden(*args, **kwargs):
        pytest.fail("preflight must reject before encoding")

    monkeypatch.setattr(BucketEncoder, "fit_transform_levels", forbidden)
    huge = np.broadcast_to(np.zeros(1), (699635, 21))
    labels = np.arange(len(huge)) % (3 if kind == "multiclass" else 2)
    with pytest.raises(ValueError, match="699635 training rows.*21 features"):
        model.fit(huge, labels)
    with pytest.raises(NotFittedError):
        check_is_fitted(model)
    with pytest.raises(NotFittedError):
        model.predict(x)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
def test_external_validation_guard_precedes_encoding(kind, monkeypatch):
    model, x, y = fixture(kind)
    model.set_params(memory_budget_mb=512)
    model.fit(x, y)
    xv = np.broadcast_to(np.zeros(1), (3000000, 4))
    with pytest.raises(ValueError, match="3000000 external validation rows"):
        model.fit(x, y, eval_set=(xv, np.broadcast_to(0, (len(xv),))))
    with pytest.raises(NotFittedError):
        check_is_fitted(model)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
def test_persistence_and_legacy_parameter_default(kind, tmp_path):
    model, x, y = fixture(kind)
    model.set_params(memory_budget_mb=1024).fit(x, y)
    expected = model.predict(x)
    for fmt in ("pickle", "joblib"):
        if fmt == "pickle":
            restored = pickle.loads(pickle.dumps(model))
        else:
            path = tmp_path / "model.joblib"
            joblib.dump(model, path)
            restored = joblib.load(path)
        assert restored.memory_budget_mb == 1024
        assert restored.predict(x).tobytes() == expected.tobytes()
    del model.memory_budget_mb
    restored = pickle.loads(pickle.dumps(model))
    assert restored.memory_budget_mb == 512
    assert restored.predict(x).tobytes() == expected.tobytes()
    clone(restored).fit(x, y)
