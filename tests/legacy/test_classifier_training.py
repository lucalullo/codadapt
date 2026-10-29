"""Classifier training uses one explicit engine and only fit-local OVR caches."""

import inspect

import numpy as np
import pytest
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from codadapt import CodAdaptClassifier, _multiclass, _training


def data(k):
    rng = np.random.RandomState(702)
    x = rng.normal(size=(120, 4))
    y = np.arange(len(x)) % k
    return x, y


@pytest.mark.parametrize("k", [2, 3, 10])
def test_training_does_not_require_source_inspection(monkeypatch, k):
    def unavailable(*args, **kwargs):
        raise OSError("Source text is unavailable in this installation")

    monkeypatch.setattr(inspect, "getsource", unavailable)
    x, y = data(k)
    model = CodAdaptClassifier(random_state=72).fit(x, y)
    assert model.predict_proba(x).shape == (len(x), k)
    check_is_fitted(model)


def test_ovr_calls_explicit_shared_trainer_with_fit_local_cache(monkeypatch):
    calls = []
    original = _training.train_coded_memory

    def record(model, z, y, weight, zv, yv, rng, *, cache=None):
        assert isinstance(cache, _multiclass.XCache)
        assert cache.weight is weight
        calls.append((cache, model, y.copy()))
        return original(model, z, y, weight, zv, yv, rng, cache=cache)

    monkeypatch.setattr(_multiclass, "train_coded_memory", record)
    x, y = data(3)
    model = CodAdaptClassifier(random_state=72).fit(x, y)
    assert len(calls) == 3
    assert all(c[0] is calls[0][0] for c in calls)
    assert len({id(c[1]) for c in calls}) == 3
    assert not np.array_equal(calls[0][2], calls[1][2])
    assert all(head.shared_state is model._ovr_artifact_.shared_state for head in model._heads_)
    assert not any(isinstance(v, _multiclass.XCache) for v in vars(model).values())
    model.fit(x, y)
    assert len(calls) == 6 and calls[3][0] is not calls[0][0]


@pytest.mark.parametrize("k", [2, 3])
def test_failed_fit_and_cross_mode_refit_have_no_stale_success(k):
    x, y = data(k)
    model = CodAdaptClassifier(random_state=72)
    with pytest.raises(NotFittedError):
        check_is_fitted(model)
    for _ in range(2):
        with pytest.raises(ValueError, match="inconsistent numbers"):
            model.fit(x, y[:-1])
        with pytest.raises(NotFittedError):
            check_is_fitted(model)
        model.fit(x, y)
        check_is_fitted(model)
    other = np.arange(len(x)) % (3 if k == 2 else 2)
    model.fit(x, other)
    assert len(model.classes_) == len(np.unique(other))
    assert hasattr(model, "_ovr_artifact_") == (k == 2)
    np.testing.assert_array_equal(
        model.predict_proba(x),
        CodAdaptClassifier(random_state=72).fit(x, other).predict_proba(x),
    )
