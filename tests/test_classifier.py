"""Binary classification, meaningful holdouts, validation and input contracts."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose, assert_array_equal
from sklearn.exceptions import NotFittedError
from sklearn.metrics import accuracy_score, log_loss

from codadapt import CodAdaptClassifier


def classifier(**kwargs):
    params = dict(
        n_bins=12, n_tables=2, table_size=32, max_iter=10, early_stopping=False, random_state=17
    )
    return CodAdaptClassifier(**(params | kwargs))


def binary_data(n=240):
    rng = np.random.default_rng(74)
    X = rng.normal(size=(n, 3))
    return X, (X[:, 0] > 0).astype(int)


@pytest.mark.parametrize("labels", [[0, 1], [3, 29], ["negativo", "positivo"]])
def test_binary_holdout_and_probability_class_order(labels):
    X, y = binary_data(480)
    labels = np.asarray(labels)
    target = labels[y]
    model = classifier().fit(X[:320], target[:320])
    prediction, probability = model.predict(X[320:]), model.predict_proba(X[320:])
    assert accuracy_score(target[320:], prediction) > 0.85
    assert log_loss(target[320:], probability, labels=model.classes_) < np.log(2)
    assert_array_equal(model.classes_, np.sort(labels))
    assert_array_equal(prediction, model.classes_[np.argmax(probability, axis=1)])
    assert probability.shape == (160, 2)
    assert np.isfinite(probability).all()
    assert ((probability >= 0) & (probability <= 1)).all()
    assert_allclose(probability.sum(axis=1), 1, atol=1e-14)
    decision = model.decision_function(X[320:])
    assert_allclose(probability[:, 1], 1 / (1 + np.exp(-decision)))


def test_xor_holdout_learns_controlled_interaction():
    rng = np.random.default_rng(916)
    X = rng.integers(0, 2, size=(640, 2))
    y = np.logical_xor(X[:, 0], X[:, 1]).astype(int)
    model = classifier(n_tables=4, features_per_table=2, main_effects=False, max_iter=14).fit(
        X[:480], y[:480]
    )
    assert all(len(group) == 2 and len(np.unique(group)) == 2 for group in model.groups_)
    assert accuracy_score(y[480:], model.predict(X[480:])) > 0.9


def test_weighted_intercept_baseline():
    X = np.zeros((8, 2))
    y = np.array([0, 0, 0, 0, 0, 0, 1, 1])
    w = np.array([1, 2, 3, 1, 1, 1, 3, 8], dtype=float)
    model = classifier(n_tables=0, main_effects=False).fit(X, y, sample_weight=w)
    assert_allclose(model.predict_proba(X)[:, 1], np.average(y, weights=w), atol=1e-12)


def test_default_coded_memory_records_bounded_history_and_profiles_screening():
    X, y = binary_data()
    model = classifier(max_iter=8).fit(X, y)
    objective = np.array([step["objective"] for step in model.training_history_])
    assert len(model.training_history_) == model.n_iter_ <= 3
    assert np.all(np.diff(objective) <= 1e-10 * np.maximum(1, np.abs(objective[:-1])))
    assert model.lookup_count_per_sample_ <= model.lookup_budget
    assert model.screening_seconds_ >= 0
    assert model.timings_["candidate_scoring"] == 0


def test_predict_requires_fit():
    for method in ("predict", "predict_proba", "decision_function"):
        with pytest.raises(NotFittedError):
            getattr(classifier(), method)(np.ones((3, 2)))


@pytest.mark.parametrize(
    "bad_y",
    [
        np.zeros(12),
        np.arange(12) % 3,
        np.linspace(0, 1, 12),
        np.ones((12, 2)),
        [0, 1] * 5 + [0, np.nan],
    ],
)
def test_rejects_unsupported_targets(bad_y):
    with pytest.raises((ValueError, TypeError)):
        classifier().fit(np.ones((12, 2)), bad_y)


@pytest.mark.parametrize(
    "weights", [[1] * 11, [-1] + [1] * 11, [np.nan] + [1] * 11, [np.inf] + [1] * 11, [0] * 12]
)
def test_rejects_invalid_sample_weights(weights):
    with pytest.raises(ValueError):
        classifier().fit(np.arange(24).reshape(12, 2), np.arange(12) % 2, sample_weight=weights)


def test_both_classes_need_positive_weight():
    with pytest.raises(ValueError):
        classifier().fit(
            np.ones((12, 2)),
            np.arange(12) % 2,
            sample_weight=(np.arange(12) % 2 == 0).astype(float),
        )


def test_deterministic_and_does_not_mutate_inputs_or_global_rng():
    X, y = binary_data()
    frame = pd.DataFrame(X, columns=["a", "b", "c"])
    weights = np.linspace(0.5, 2, len(y))
    old_frame, old_y, old_weights = frame.copy(deep=True), y.copy(), weights.copy()
    np.random.seed(431)
    old_rng = np.random.get_state()
    first = classifier().fit(frame, y, sample_weight=weights)
    new_rng = np.random.get_state()
    second = classifier().fit(frame, y, sample_weight=weights)
    pd.testing.assert_frame_equal(frame, old_frame)
    assert_array_equal(y, old_y)
    assert_array_equal(weights, old_weights)
    assert old_rng[0] == new_rng[0] and old_rng[2:] == new_rng[2:]
    assert_array_equal(old_rng[1], new_rng[1])
    assert_array_equal(first.predict_proba(frame), second.predict_proba(frame))
    for first_table, second_table in zip(first.codes_, second.codes_, strict=True):
        for first_codes, second_codes in zip(first_table, second_table, strict=True):
            assert_array_equal(first_codes, second_codes)


def test_refit_replaces_old_feature_and_class_state():
    X, y = binary_data()
    model = classifier().fit(X, y)
    model.fit(X[:, :1], np.where(y == 1, "yes", "no"))
    assert model.n_features_in_ == 1
    assert_array_equal(model.classes_, ["no", "yes"])
    assert set(model.predict(X[:, :1])) <= {"no", "yes"}
    with pytest.raises(ValueError):
        model.predict(X)


def test_internal_split_failure_is_actionable():
    with pytest.raises(ValueError, match="early_stopping"):
        classifier(early_stopping=True).fit(np.array([[0], [1], [2]]), [0, 0, 1])
