"""Single-target regression, baseline learning and parameter validation."""

import numpy as np
import pytest
from numpy.testing import assert_allclose
from sklearn.metrics import mean_squared_error

from codadapt import CodAdaptRegressor


def regressor(**kwargs):
    params = dict(
        n_bins=16, n_tables=2, table_size=32, max_iter=10, early_stopping=False, random_state=19
    )
    return CodAdaptRegressor(**(params | kwargs))


def test_regression_monovariate_holdout_beats_mean():
    rng = np.random.default_rng(901)
    X = rng.uniform(-2, 2, size=(600, 3))
    y = 3 * X[:, 0] + 0.1 * rng.normal(size=len(X))
    model = regressor(n_tables=0).fit(X[:400], y[:400])
    prediction = model.predict(X[400:])
    baseline = np.full(200, y[:400].mean())
    assert mean_squared_error(y[400:], prediction) < 0.25 * mean_squared_error(y[400:], baseline)


def test_constant_target_and_zero_component_baseline():
    X = np.arange(100).reshape(50, 2)
    model = regressor().fit(X, np.full(50, 7.25))
    assert_allclose(model.predict(X), 7.25, atol=1e-12)
    y, weights = np.arange(50), np.arange(1, 51)
    model = regressor(n_tables=0, main_effects=False).fit(X, y, sample_weight=weights)
    assert_allclose(model.predict(X), np.average(y, weights=weights), atol=1e-12)


def test_integer_target_is_still_regression():
    X = np.arange(240, dtype=float).reshape(120, 2)
    y = np.arange(120) // 4
    model = regressor().fit(X, y)
    assert not hasattr(model, "classes_")
    assert not hasattr(model, "predict_proba")
    assert np.issubdtype(model.predict(X).dtype, np.floating)
    assert len(np.unique(model.predict(X))) > 2


def test_weighted_objective_decreases():
    rng = np.random.default_rng(128)
    X = rng.normal(size=(160, 4))
    y, weights = X[:, 0] * X[:, 1], rng.uniform(0.1, 3, 160)
    model = regressor(max_iter=8).fit(X, y, sample_weight=weights)
    objectives = np.array([step["objective"] for step in model.training_history_])
    assert np.isfinite(objectives).all()
    assert np.all(np.diff(objectives) <= 1e-8 * np.maximum(1, np.abs(objectives[:-1])))


@pytest.mark.parametrize(
    "target", [np.ones((12, 2)), [0] * 11, [0] * 11 + [np.nan], [0] * 11 + [np.inf], ["a"] * 12]
)
def test_invalid_targets(target):
    with pytest.raises((ValueError, TypeError)):
        regressor().fit(np.ones((12, 2)), target)


@pytest.mark.parametrize(
    "params",
    [
        {"n_bins": 0},
        {"n_bins": 2.5},
        {"max_categories": 0},
        {"quantile_sample_size": 0},
        {"n_tables": -1},
        {"features_per_table": 0},
        {"table_size": 15},
        {"table_size": 48},
        {"table_size": 8192},
        {"max_iter": 0},
        {"l2": 0},
        {"l2": -1},
        {"l2": np.nan},
        {"adapt_every": 0},
        {"max_code_updates": -1},
        {"n_candidates": 0},
        {"min_code_count": 0},
        {"validation_fraction": 0},
        {"validation_fraction": 1},
        {"patience": 0},
        {"tol": -1},
        {"verbosity": 3},
        {"n_tables": 1000000000},
    ],
)
def test_invalid_parameters_fail_before_large_allocations(params):
    with pytest.raises((ValueError, TypeError)):
        regressor(**params).fit(np.ones((12, 2)), np.arange(12))


@pytest.mark.parametrize(
    "bad_X",
    [
        np.arange(12),
        np.ones((4, 2, 2)),
        np.empty((0, 2)),
        np.empty((12, 0)),
        np.full((12, 2), np.inf),
    ],
)
def test_bad_array_shapes_and_infinities(bad_X):
    with pytest.raises((ValueError, TypeError)):
        regressor().fit(bad_X, np.arange(12))
