"""Contracts for adaptive level allocation in the official coded-memory core."""

import numpy as np
import pytest

from codadapt import CodAdaptClassifier, CodAdaptRegressor


def test_coded_memory_respects_lookup_budget_and_reports_allocation():
    rng = np.random.default_rng(401)
    X = rng.normal(size=(360, 8))
    y = 3 * X[:, 0] - X[:, 1] + 0.2 * rng.normal(size=len(X))
    model = CodAdaptRegressor(lookup_budget=12, early_stopping=False, random_state=42).fit(X, y)
    assert model.lookup_count_per_sample_ <= 12
    assert model.effective_levels_ == len(model.levels_) == model.n_iter_
    assert len(model.level_history_) == model.n_iter_
    assert all(0 <= row["collision_rate"] <= 1 for row in model.level_history_)


def test_adaptive_feature_allocation_concentrates_on_signal():
    rng = np.random.default_rng(402)
    X = rng.normal(size=(420, 12))
    y = 5 * X[:, 0] + 0.05 * rng.normal(size=len(X))
    model = CodAdaptRegressor(
        lookup_budget=9, n_tables=0, early_stopping=False, random_state=42
    ).fit(X, y)
    selected = [level["main_features"].tolist() for level in model.levels_]
    assert selected
    assert all(0 in features for features in selected)
    assert model.feature_level_stopping_ > 0


def test_validation_stopping_discards_noninformative_level():
    X_train = np.linspace(-2, 2, 240).reshape(-1, 1)
    y_train = X_train[:, 0]
    X_valid = np.linspace(-2, 2, 80).reshape(-1, 1)
    y_valid = -X_valid[:, 0]
    model = CodAdaptRegressor(n_tables=0, lookup_budget=6, random_state=42).fit(
        X_train, y_train, eval_set=(X_valid, y_valid)
    )
    assert model.allocation_history_
    assert not model.allocation_history_[0]["accepted"]
    assert model.levels_ == []
    assert model.predict(X_valid) == pytest.approx(np.full(len(X_valid), model.intercept_))


def test_classifier_uses_validation_without_test_data():
    rng = np.random.default_rng(403)
    X = rng.normal(size=(300, 5))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    model = CodAdaptClassifier(random_state=42).fit(
        X[:240], y[:240], eval_set=(X[240:270], y[240:270])
    )
    assert model.n_iter_ <= 3
    assert np.isfinite(model.predict_proba(X[270:])).all()


@pytest.mark.parametrize("budget", [0, 4097, 1.5, True])
def test_lookup_budget_is_bounded_integer(budget):
    with pytest.raises(ValueError, match="lookup_budget"):
        CodAdaptRegressor(lookup_budget=budget).fit(np.ones((8, 2)), np.arange(8))
