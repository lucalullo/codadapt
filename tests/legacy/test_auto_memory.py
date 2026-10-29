"""Public AUTO contracts and adversarial inputs on the integrated C1 runtime."""

import json
import subprocess
import sys

import joblib
import numpy as np
import pytest
from sklearn.base import clone
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor


def case(kind):
    x = np.random.RandomState(117).normal(size=(96, 4))
    y = x[:, 0] if kind == "regression" else np.arange(len(x)) % (3 if kind == "multi" else 2)
    cls = CodAdaptRegressor if kind == "regression" else CodAdaptClassifier
    return cls(random_state=42), x, y


@pytest.mark.parametrize("kind", ["binary", "multi", "regression"])
def test_auto_default_clone_and_exact_integer_control(kind, tmp_path):
    model, x, y = case(kind)
    assert model.memory_budget_mb == "auto"
    assert CodAdapt is CodAdaptClassifier
    control = clone(model).set_params(memory_budget_mb=512).fit(x, y)
    model.fit(x, y)
    assert clone(model).memory_budget_mb == "auto"
    assert model.predict(x).tobytes() == control.predict(x).tobytes()
    if kind != "regression":
        assert model.predict_proba(x).tobytes() == control.predict_proba(x).tobytes()
    assert model.effective_memory_budget_mb_ == 512
    assert model.memory_admission_available_bytes_ is None
    assert not model.memory_admission_safety_certificate_
    assert not model.memory_admission_resource_qualified_
    joblib.dump(model, tmp_path / "auto.joblib")
    restored = joblib.load(tmp_path / "auto.joblib")
    assert restored.memory_budget_mb == "auto"
    assert restored.predict(x).tobytes() == model.predict(x).tobytes()


@pytest.mark.parametrize("value", ["AUTO", "Auto", " auto", "auto ", "", np.bool_(True)])
def test_only_exact_auto_or_positive_integer_is_accepted(value):
    with pytest.raises(ValueError, match="memory_budget_mb"):
        CodAdaptClassifier(memory_budget_mb=value)._validate_parameters()


@pytest.mark.parametrize("kind", ["binary", "multi", "regression"])
def test_lazy_legacy_path_never_imports_resource_modules(kind):
    code = f"""
import sys, json, numpy as np
from codadapt import CodAdaptClassifier, CodAdaptRegressor
x=np.random.RandomState(7).normal(size=(96,4))
y=x[:,0] if {kind!r}=='regression' else np.arange(len(x))%(3 if {kind!r}=='multi' else 2)
cls=CodAdaptRegressor if {kind!r}=='regression' else CodAdaptClassifier
m=cls(random_state=42).fit(x,y)
assert m.memory_budget_mb=='auto'
assert not any(n in sys.modules for n in ('codadapt._memory_admission','codadapt._resource_snapshot','codadapt._memory_policy'))
print(json.dumps({{'status':'PASS'}}))
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "PASS"


class ArrayLike:
    def __init__(self, value):
        self.value = value
        self.conversions = 0

    def __array__(self, dtype=None, copy=None):
        self.conversions += 1
        return np.asarray(self.value, dtype=dtype)

    def __len__(self):
        return len(self.value)


@pytest.mark.parametrize("kind", ["binary", "multi", "regression"])
@pytest.mark.parametrize("container", [ArrayLike, list, tuple])
def test_existing_array_like_conversion_and_external_validation(kind, container):
    model, x, y = case(kind)
    train, valid = container(x[:72]), container(x[72:])
    model.fit(train, y[:72], eval_set=(valid, y[72:]))
    control = (
        clone(model).set_params(memory_budget_mb=512).fit(x[:72], y[:72], eval_set=(x[72:], y[72:]))
    )
    assert model.predict(x).tobytes() == control.predict(x).tobytes()
    if container is ArrayLike:
        assert train.conversions == valid.conversions == 1


@pytest.mark.parametrize("kind", ["binary", "multi", "regression"])
def test_unknown_resource_extension_rejects_refit_before_encoding(kind, monkeypatch):
    from codadapt import _memory_admission as guard
    from codadapt.preprocessing import BucketEncoder

    model, x, y = case(kind)
    model.fit(x, y)
    monkeypatch.setattr(guard, "observe", lambda: {"status": "UNOBSERVED"})
    monkeypatch.setattr(guard, "observe_virtual", lambda s: {"status": "UNKNOWN"})
    monkeypatch.setattr(
        BucketEncoder, "fit_transform_levels", lambda *a, **k: pytest.fail("encoded rejected fit")
    )
    # Broadcast shape tests admission without materializing a large training matrix.
    huge = np.broadcast_to(x[:1, :1], (699635, 21))
    labels = np.arange(len(huge)) % (3 if kind == "multi" else 2)
    with pytest.raises(ValueError, match="AUTO memory admission rejected"):
        model.fit(huge, labels)
    with pytest.raises(NotFittedError):
        check_is_fitted(model)
    with pytest.raises(NotFittedError):
        model.predict(x)


def test_dispatch_failure_also_invalidates_previously_fitted_classifier():
    model, x, y = case("multi")
    model.fit(x, y)

    class BrokenTarget:
        def __array__(self, dtype=None, copy=None):
            raise ValueError("conversion failed")

    with pytest.raises(ValueError, match="conversion failed"):
        model.fit(x, BrokenTarget())
    with pytest.raises(NotFittedError):
        check_is_fitted(model)
