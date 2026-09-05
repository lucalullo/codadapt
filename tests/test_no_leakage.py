"""Keep representation and every training decision independent of validation."""

import pickle

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose, assert_array_equal
from sklearn.metrics import log_loss, mean_squared_error
from sklearn.model_selection import train_test_split

from codadapt import CodAdaptClassifier, CodAdaptRegressor


def assert_same_state(first, second):
    assert pickle.dumps(first.encoder_) == pickle.dumps(second.encoder_)
    assert_allclose(first.intercept_, second.intercept_, atol=1e-12, rtol=0)
    for name in ("groups_", "main_tables_", "tables_"):
        left, right = getattr(first, name), getattr(second, name)
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            assert_array_equal(a, b)
    for left_table, right_table in zip(first.codes_, second.codes_, strict=True):
        for left, right in zip(left_table, right_table, strict=True):
            assert_array_equal(left, right)


def mixed_training(n=160):
    rng = np.random.default_rng(776)
    value = rng.normal(size=n)
    frame = pd.DataFrame({"value": value, "category": np.where(value > 0, "train-a", "train-b")})
    return frame, (value > 0).astype(int), 2 * value


@pytest.mark.parametrize(
    "estimator,target_index", [(CodAdaptClassifier, 1), (CodAdaptRegressor, 2)]
)
def test_validation_features_and_labels_do_not_change_training_decisions(estimator, target_index):
    data = mixed_training()
    X, y = data[0], data[target_index]
    params = dict(
        n_bins=8, n_tables=3, table_size=32, max_iter=7, early_stopping=False, random_state=7
    )
    valid = pd.DataFrame(
        {"value": np.linspace(-1e9, 1e9, 40), "category": ["validation-only"] * 40}
    )
    y_valid = np.arange(40) % 2 if target_index == 1 else np.linspace(-20, 20, 40)
    first = estimator(**params).fit(X, y, eval_set=(valid, y_valid))
    second = estimator(**params).fit(
        X, y, eval_set=(valid, -y_valid if target_index == 2 else 1 - y_valid)
    )
    third = estimator(**params).fit(X, y)
    assert_same_state(first, second)
    assert_same_state(first, third)
    for left, right in zip(first.training_history_, second.training_history_, strict=True):
        for key in ("objective", "train_loss", "coordinates_examined", "accepted_moves"):
            assert left[key] == right[key]
    assert first.n_iter_ == second.n_iter_ <= 3
    assert all(np.isfinite(step["validation_loss"]) for step in first.training_history_)
    probe = pd.DataFrame({"value": [1e12], "category": ["another-new-category"]})
    assert_array_equal(
        first.encoder_.transform(valid.iloc[:1])[:, 1], first.encoder_.transform(probe)[:, 1]
    )


@pytest.mark.parametrize(
    "estimator,target_index", [(CodAdaptClassifier, 1), (CodAdaptRegressor, 2)]
)
def test_zero_weight_rows_removed_before_internal_split_and_encoding(estimator, target_index):
    data = mixed_training(300)
    X, y = data[0], data[target_index]
    excluded = np.arange(0, len(y), 11)
    weights = np.ones(len(y))
    weights[excluded] = 0
    X.loc[excluded, "value"] = 1e25
    X.loc[excluded, "category"] = "zero-weight-only"
    params = dict(n_tables=1, table_size=32, max_iter=4, early_stopping=True, random_state=31)
    first = estimator(**params).fit(X, y, sample_weight=weights)
    keep = weights > 0
    second = estimator(**params).fit(X.loc[keep], y[keep], sample_weight=weights[keep])
    assert_same_state(first, second)
    assert_allclose(first.predict(X), second.predict(X))


def test_internal_validation_is_split_before_quantiles_and_category_vocabulary():
    X, y, _ = mixed_training(200)
    train, valid = train_test_split(np.arange(len(y)), test_size=0.2, random_state=29, stratify=y)
    X.loc[valid, "value"] = 1e20
    X.loc[valid, "category"] = "internal-validation-only"
    params = dict(n_tables=2, table_size=32, max_iter=5, random_state=29, validation_fraction=0.2)
    internal = CodAdaptClassifier(**params).fit(X, y)
    explicit = CodAdaptClassifier(**params).fit(
        X.iloc[train], y[train], eval_set=(X.iloc[valid], y[valid])
    )
    assert_same_state(internal, explicit)


@pytest.mark.parametrize(
    "estimator,binary", [(CodAdaptClassifier, True), (CodAdaptRegressor, False)]
)
def test_early_stopping_restores_complete_best_state(estimator, binary):
    rng = np.random.default_rng(123)
    X = rng.normal(size=(260, 2))
    signal = X[:, 0] + 0.3 * X[:, 1]
    y = (signal > 0).astype(int) if binary else signal
    X_train, X_valid = X[:200], X[200:]
    y_train = y[:200]
    y_valid = 1 - y[200:] if binary else -y[200:]
    model = estimator(n_tables=3, n_bins=8, table_size=32, patience=2, tol=0, random_state=44).fit(
        X_train, y_train, eval_set=(X_valid, y_valid)
    )

    accepted = [row for row in model.allocation_history_ if row["accepted"]]
    rejected = [row for row in model.allocation_history_ if not row["accepted"]]
    assert rejected
    assert model.best_iteration_ == model.n_iter_ == len(accepted)
    if binary:
        restored_loss = log_loss(y_valid, model.predict_proba(X_valid), labels=model.classes_)
        initial_score = np.full(len(y_valid), model.intercept_)
        initial_loss = np.mean(np.logaddexp(0.0, initial_score) - y_valid * initial_score)
    else:
        restored_loss = mean_squared_error(y_valid, model.predict(X_valid))
        initial_loss = mean_squared_error(y_valid, np.full(len(y_valid), model.intercept_))
    expected_loss = accepted[-1]["validation_loss"] if accepted else initial_loss
    assert_allclose(restored_loss, expected_loss, atol=1e-12, rtol=1e-12)


def test_predictions_do_not_refit_or_update_encoder():
    X, y, _ = mixed_training()
    model = CodAdaptClassifier(n_tables=1, max_iter=3, early_stopping=False, random_state=9).fit(
        X, y
    )
    state = pickle.dumps(
        (model.encoder_, model.codes_, model.main_tables_, model.tables_, model.intercept_)
    )
    query = pd.DataFrame({"value": [np.nan, -1e50, 1e50], "category": [None, "new-a", "new-b"]})
    model.predict(query)
    model.predict_proba(query)
    assert (
        pickle.dumps(
            (model.encoder_, model.codes_, model.main_tables_, model.tables_, model.intercept_)
        )
        == state
    )
