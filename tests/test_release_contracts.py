"""Release engineering contracts; no predictive-quality selection or tuning."""

from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from codadapt import CodAdaptClassifier, CodAdaptRegressor
from codadapt.experimental import SafeBlendRegressor


def fixture(kind):
    x = np.random.RandomState(411).normal(size=(80, 4))
    if kind == "regression":
        return CodAdaptRegressor(random_state=41), x, x[:, 0] + 0.1 * x[:, 1]
    k = 2 if kind == "binary" else 3
    return CodAdaptClassifier(random_state=41), x, np.arange(len(x)) % k


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
@pytest.mark.parametrize("validation", [0, np.ones(8), np.ones((8, 2, 1))])
def test_validation_shape_has_public_error(kind, validation):
    model, x, y = fixture(kind)
    with pytest.raises((ValueError, TypeError), match="2D|validation|Validation"):
        model.fit(x, y, eval_set=(validation, y[:8]))
    with pytest.raises(NotFittedError):
        check_is_fitted(model)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
@pytest.mark.parametrize("refit", [False, True])
def test_interrupted_logging_never_marks_fit_successful(kind, refit, monkeypatch):
    model, x, y = fixture(kind)
    if refit:
        model.fit(x, y)
    model.set_params(verbosity=1)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt("simulated interruption at final logging")

    monkeypatch.setattr("builtins.print", interrupt)
    with pytest.raises(KeyboardInterrupt):
        model.fit(x, y)
    with pytest.raises(NotFittedError):
        check_is_fitted(model)
    with pytest.raises(NotFittedError):
        model.predict(x)


@pytest.mark.parametrize("n", [2, 10])
def test_safeblend_large_finite_target_validation_is_warning_free(n):
    # Only input validation: large finite integer-valued floats must not trigger
    # an out-of-range float-to-int cast. Fitting extreme losses is a separate limit.
    y = np.linspace(1e20, 2e20, n)
    with np.errstate(all="raise"):
        np.testing.assert_array_equal(SafeBlendRegressor._target(y, len(y)), y)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression", "safe_base", "safe_blend"])
def test_concurrent_predictions_preserve_state(kind):
    if kind.startswith("safe"):
        if kind == "safe_base":
            x, y, seed = np.zeros((40, 2)), np.full(40, 3.5), 7
        else:
            rng = np.random.RandomState(82)
            x = rng.normal(size=(160, 4))
            y = 2 * x[:, 0] + x[:, 1] ** 2 + 0.01 * rng.normal(size=len(x))
            seed = 82
        model = SafeBlendRegressor(random_state=seed).fit(x, y)
        assert model.branch_ == ("BASE" if kind == "safe_base" else "BLEND")
    else:
        model, x, y = fixture(kind)
        model.fit(x, y)
    params = model.get_params(deep=True)
    expected = model.predict(x)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for actual in pool.map(model.predict, [x] * 12):
            assert actual.tobytes() == expected.tobytes()
        if hasattr(model, "predict_proba"):
            probability = model.predict_proba(x)
            for actual in pool.map(model.predict_proba, [x] * 12):
                assert actual.tobytes() == probability.tobytes()
    assert model.get_params(deep=True) == params
    assert model.predict(x).tobytes() == expected.tobytes()


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
@pytest.mark.parametrize(
    "bad_x", [np.empty((0, 4)), np.empty((80, 0)), np.ones(80), np.ones((80, 4, 1))]
)
def test_invalid_input_after_successful_fit_is_unfitted(kind, bad_x):
    model, x, y = fixture(kind)
    model.fit(x, y)
    with pytest.raises((ValueError, TypeError)):
        model.fit(bad_x, y)
    with pytest.raises(NotFittedError):
        check_is_fitted(model)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
def test_memory_preflight_rejects_without_stale_fit(kind):
    model, x, y = fixture(kind)
    # A fixed cap must reject independently of machine headroom; AUTO may admit.
    model.set_params(memory_budget_mb=512)
    model.fit(x, y)
    # A broadcast view avoids allocating a large test matrix. The guard must
    # reject before training/encoding materializes it.
    huge = np.broadcast_to(np.zeros(1), (100000, 500))
    labels = np.arange(len(huge)) % (3 if kind == "multiclass" else 2)
    with pytest.raises(ValueError, match="budget|allocation|memory"):
        model.fit(huge, labels)
    with pytest.raises(NotFittedError):
        check_is_fitted(model)


@pytest.mark.parametrize("kind", ["binary", "multiclass", "regression"])
def test_integer_dataframe_schema_and_refit(kind):
    model, x, y = fixture(kind)
    frame = pd.DataFrame(x, columns=[10, 20, 30, 40])
    model.fit(frame, y)
    assert not hasattr(model, "feature_names_in_")
    np.testing.assert_array_equal(model.predict(frame), model.predict(frame[[40, 30, 20, 10]]))
    with pytest.raises(ValueError):
        model.predict(frame.rename(columns={10: 11}))
    clone(model).fit(x, y)
