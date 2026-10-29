"""Internal class weights, TRAIN-only boundaries and native estimator contracts."""

import inspect
import pickle

import joblib
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose, assert_array_equal
from sklearn.base import clone
from sklearn.datasets import load_breast_cancer, load_iris, load_wine
from sklearn.exceptions import NotFittedError
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor
from codadapt import classifier as classifier_module
from codadapt._class_weight import training_class_weights

OPTIONS = dict(n_tables=2, table_size=32, early_stopping=False, random_state=42)


def fixture_data(k=2, string=False):
    rng = np.random.RandomState(307)
    counts = [83, 29] if k == 2 else [71, 29, 13]
    codes = np.repeat(np.arange(k), counts)
    x = rng.normal(size=(len(codes), 4)) + codes[:, None] * 0.45
    labels = np.array(["alpha", "beta", "gamma"][:k]) if string else np.arange(k) * 3 - 4
    return x, labels[codes]


def manual_weights(y, weight=None):
    """Independent label-mask formula, without any sklearn balancing helper."""
    base = np.ones(len(y)) if weight is None else np.asarray(weight, dtype=float)
    result = base.copy()
    labels = np.unique(y[base > 0])
    total = base.sum()
    for label in labels:
        rows = y == label
        result[rows] *= total / (len(labels) * base[rows].sum())
    return result


def assert_same_predictive_state(a, b, x, exact=False):
    assert_array_equal(a.classes_, b.classes_)
    assert pickle.dumps(a.encoder_) == pickle.dumps(b.encoder_)
    compare = assert_array_equal if exact else lambda v, w: assert_allclose(
        v, w, rtol=1e-12, atol=1e-12
    )
    compare(a.decision_function(x), b.decision_function(x))
    compare(a.predict_proba(x), b.predict_proba(x))
    assert_array_equal(a.predict(x), b.predict(x))
    if hasattr(a, "_heads_"):
        pairs = zip(a._heads_, b._heads_, strict=True)
        for left, right in pairs:
            compare(left.intercept, right.intercept)
            assert len(left.levels) == len(right.levels)
            for ll, rr in zip(left.levels, right.levels, strict=True):
                assert_array_equal(ll["main_features"], rr["main_features"])
                for key in ("main_tables", "tables"):
                    for lv, rv in zip(ll[key], rr[key], strict=True):
                        compare(lv, rv)
    else:
        compare(a.intercept_, b.intercept_)
        for key in ("main_tables_", "tables_"):
            for lv, rv in zip(getattr(a, key), getattr(b, key), strict=True):
                compare(lv, rv)


@pytest.mark.parametrize("k", [2, 3])
@pytest.mark.parametrize("string", [False, True])
@pytest.mark.parametrize("weighted", [False, True])
def test_balanced_matches_independent_manual_formula(k, string, weighted):
    x, y = fixture_data(k, string)
    w = np.linspace(0.5, 3.0, len(y)) if weighted else None
    a = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(x, y, sample_weight=w)
    b = CodAdaptClassifier(**OPTIONS).fit(x, y, sample_weight=manual_weights(y, w))
    assert_same_predictive_state(a, b, x)


@pytest.mark.parametrize("k", [2, 3])
@pytest.mark.parametrize("weighted", [False, True])
def test_effective_class_mass_is_equal_and_total_preserved(k, weighted):
    _, y = fixture_data(k, True)
    w = np.linspace(0.25, 7, len(y)) if weighted else np.ones(len(y))
    result = training_class_weights(y, w, "balanced")
    for label in np.unique(y):
        assert_allclose(result[y == label].sum(), w.sum() / k, rtol=1e-15)
    assert_allclose(result.sum(), w.sum(), rtol=1e-15)
    assert not np.shares_memory(result, w)


@pytest.mark.parametrize("k", [2, 3])
def test_equal_class_masses_are_identity(k):
    rng = np.random.RandomState(9)
    x = rng.normal(size=(90, 3))
    y = np.arange(90) % k
    a = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(x, y)
    b = CodAdaptClassifier(**OPTIONS).fit(x, y)
    assert_same_predictive_state(a, b, x, exact=True)


@pytest.mark.parametrize("k", [2, 3])
@pytest.mark.parametrize("weighted", [False, True])
def test_internal_validation_uses_only_effective_training_mass(k, weighted):
    x, y = fixture_data(k, True)
    w = np.linspace(0.1, 4.0, len(y)) if weighted else np.ones(len(y))
    w[::11] = 0
    keep = np.flatnonzero(w > 0)
    train, valid = train_test_split(
        keep, test_size=0.23, random_state=42, stratify=y[keep]
    )
    options = {**OPTIONS, "early_stopping": True, "validation_fraction": 0.23}
    internal = CodAdaptClassifier(class_weight="balanced", **options).fit(x, y, sample_weight=w)
    explicit = CodAdaptClassifier(**options).fit(
        x[train], y[train], sample_weight=manual_weights(y[train], w[train]),
        eval_set=(x[valid], y[valid]),
    )
    assert_same_predictive_state(internal, explicit, x)


@pytest.mark.parametrize("k", [2, 3])
def test_external_validation_never_changes_class_factors(k):
    x, y = fixture_data(k)
    valid = x[:20] * 50
    a = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(
        x, y, eval_set=(valid, np.resize(np.unique(y), 20))
    )
    b = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(
        x, y, eval_set=(valid, np.full(20, y[-1]))
    )
    c = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(x, y)
    assert_same_predictive_state(a, b, x, exact=True)
    assert_same_predictive_state(a, c, x, exact=True)


@pytest.mark.parametrize("k", [2, 3])
def test_zero_weight_rows_and_zero_mass_classes_do_not_enter_balancing(k):
    x, y = fixture_data(k, True)
    extra_x = np.full((7, x.shape[1]), 1e10)
    full_x = np.vstack((x, extra_x))
    full_y = np.r_[y, np.repeat("zero-mass-only", 7)]
    w = np.r_[np.ones(len(y)), np.zeros(7)]
    a = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(full_x, full_y, w)
    b = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(x, y)
    assert_same_predictive_state(a, b, full_x, exact=True)


def test_multiclass_balancing_is_applied_once_to_original_labels(monkeypatch):
    x, y = fixture_data(3, True)
    seen = []
    original = classifier_module.training_class_weights

    def capture(labels, weight, class_weight):
        result = original(labels, weight, class_weight)
        seen.append((labels.copy(), result.copy()))
        return result

    monkeypatch.setattr(classifier_module, "training_class_weights", capture)
    model = CodAdaptClassifier(
        class_weight="balanced", n_tables=0, main_effects=False,
        early_stopping=False, random_state=42,
    ).fit(x, y)
    assert len(seen) == 1
    assert_array_equal(seen[0][0], y)
    assert_allclose(seen[0][1], manual_weights(y), rtol=1e-15)
    # Rebalancing each binary head would incorrectly make every intercept zero.
    assert_allclose([h.intercept for h in model._heads_], -np.log(2), atol=1e-15)
    assert_allclose(model.predict_proba(x), 1 / 3, atol=1e-15)


@pytest.mark.parametrize("k", [2, 3])
def test_balanced_intercept_uses_weighted_masses_not_raw_counts(k):
    x, y = fixture_data(k)
    w = np.where(y == y[-1], 20.0, 0.25)
    model = CodAdaptClassifier(
        class_weight="balanced", n_tables=0, main_effects=False,
        early_stopping=False, random_state=42,
    ).fit(x, y, sample_weight=w)
    assert_allclose(model.predict_proba(x), 1 / k, atol=1e-15)


@pytest.mark.parametrize("value", ["auto", "Balanced", "", True, False, 1, 0.5, [], [1, 2], np.array([1, 2])])
@pytest.mark.parametrize("k", [2, 3])
def test_invalid_class_weight_rejected_and_failed_refit_is_unfitted(value, k):
    x, y = fixture_data(k)
    model = CodAdaptClassifier(**OPTIONS).fit(x, y).set_params(class_weight=value)
    with pytest.raises(ValueError, match="class_weight"):
        model.fit(x, y)
    with pytest.raises(NotFittedError):
        model.predict(x)
    model.set_params(class_weight="balanced").fit(x, y)
    assert model.predict(x).shape == (len(y),)


@pytest.mark.parametrize("bad", [-1, 0, np.nan, np.inf, True, "2", None, 10**400])
def test_invalid_explicit_class_factors_rejected(bad):
    x, y = fixture_data()
    with pytest.raises(ValueError, match="class_weight"):
        CodAdaptClassifier(class_weight={y[0]: bad}, **OPTIONS).fit(x, y)


@pytest.mark.parametrize("k", [2, 3])
def test_explicit_dictionary_interoperability_matches_sample_weights(k):
    x, y = fixture_data(k, True)
    factors = {y[-1]: 3.25}
    w = np.linspace(0.5, 2, len(y))
    weighted = w * np.array([factors.get(label, 1.0) for label in y])
    a = CodAdaptClassifier(class_weight=factors, **OPTIONS).fit(x, y, w)
    b = CodAdaptClassifier(**OPTIONS).fit(x, y, weighted)
    assert_same_predictive_state(a, b, x, exact=True)
    with pytest.raises(ValueError, match="absent from effective TRAIN"):
        CodAdaptClassifier(class_weight={"typo": 1.0}, **OPTIONS).fit(x, y)


@pytest.mark.parametrize("bad_weight", [np.zeros(112), -np.ones(112), np.full(112, np.inf), np.ones((112, 1)), np.ones(111)])
def test_invalid_sample_weights_retain_existing_contract(bad_weight):
    x, y = fixture_data()
    with pytest.raises(ValueError, match="sample_weight"):
        CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(x, y, bad_weight)


def test_rare_class_warnings_and_small_split_failures_remain_explicit():
    x = np.arange(42).reshape(14, 3)
    y = np.array([0] * 8 + [1] * 4 + [2] * 2)
    with pytest.warns(UserWarning, match="Rare class"):
        CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(x, y)
    y[-1] = 1
    with pytest.raises(ValueError, match="Insufficient data"):
        CodAdaptClassifier(class_weight="balanced", random_state=42).fit(x, y)


@pytest.mark.parametrize("k", [2, 3])
@pytest.mark.parametrize("class_weight", [None, "balanced", {-4: 1.25}])
def test_clone_pipeline_and_persistence(k, class_weight, tmp_path):
    x, y = fixture_data(k)
    estimator = CodAdaptClassifier(class_weight=class_weight, **OPTIONS)
    assert clone(estimator).get_params() == estimator.get_params()
    assert clone(estimator).set_params(class_weight="balanced").class_weight == "balanced"
    pipeline = make_pipeline(StandardScaler(), estimator).fit(x, y)
    expected = pipeline.predict_proba(x)
    restored = pickle.loads(pickle.dumps(pipeline))
    assert_array_equal(restored.predict_proba(x), expected)
    path = tmp_path / "weighted.joblib"
    joblib.dump(pipeline, path)
    assert_array_equal(joblib.load(path).predict_proba(x), expected)
    assert_array_equal(clone(pipeline).fit(x, y).predict_proba(x), expected)


@pytest.mark.parametrize("k", [2, 3])
def test_legacy_state_without_parameter_restores_none(k):
    x, y = fixture_data(k)
    model = CodAdaptClassifier(**OPTIONS).fit(x, y)
    state = model.__getstate__()
    state.pop("class_weight")
    restored = CodAdaptClassifier.__new__(CodAdaptClassifier)
    restored.__setstate__(state)
    assert restored.class_weight is None
    assert_same_predictive_state(model, restored, x, exact=True)
    assert clone(restored).class_weight is None


def test_refit_binary_multiclass_transitions_and_user_input_not_mutated():
    model = CodAdaptClassifier(class_weight="balanced", **OPTIONS)
    for k in (2, 3, 2):
        x, y = fixture_data(k)
        w = np.linspace(0.5, 1.5, len(y))
        before = (x.copy(), y.copy(), w.copy())
        model.fit(x, y, w)
        direct = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(x, y, w)
        assert_same_predictive_state(model, direct, x, exact=True)
        for old, new in zip(before, (x, y, w), strict=True):
            assert_array_equal(old, new)


def test_regressor_has_no_class_weight_parameter_and_none_returns_same_vector():
    assert "class_weight" not in inspect.signature(CodAdaptRegressor).parameters
    assert "class_weight" not in CodAdaptRegressor().get_params()
    with pytest.raises(TypeError, match="class_weight"):
        CodAdaptRegressor(class_weight="balanced")
    weights = np.array([1.0, 2.0])
    assert training_class_weights(np.array([0, 1]), weights, None) is weights
    assert CodAdapt is CodAdaptClassifier


def test_normalization_avoids_overflowing_explicit_inverse_factors():
    w = np.array([1e-300, 1e300])
    assert_allclose(training_class_weights(np.array([0, 1]), w, "balanced"), [5e299, 5e299])
    with pytest.raises(ValueError, match="class_weight"):
        training_class_weights(np.array([0, 0, 1]), np.array([1e-300, 1e300, 1.0]), "balanced")


@pytest.mark.parametrize("k", [2, 3])
def test_large_representable_integer_factors_keep_numeric_training_weights(k):
    x, y = fixture_data(k)
    factors = {label: 10**100 for label in np.unique(y)}
    weights = np.full(len(y), 1e-100)
    manual = weights * float(10**100)
    a = CodAdaptClassifier(class_weight=factors, **OPTIONS).fit(x, y, weights)
    b = CodAdaptClassifier(**OPTIONS).fit(x, y, manual)
    assert_same_predictive_state(a, b, x, exact=True)


@pytest.mark.parametrize("loader", [load_breast_cancer, load_iris, load_wine])
def test_real_packaged_dataset_engineering_sanity_and_cv(loader):
    # Source-packaged datasets, engineering only: no new independent quality claim.
    data = loader()
    model = CodAdaptClassifier(class_weight="balanced", **OPTIONS)
    scores = cross_val_score(
        model, data.data, data.target, cv=StratifiedKFold(3, shuffle=True, random_state=42),
        scoring="balanced_accuracy", error_score="raise",
    )
    assert scores.shape == (3,) and np.isfinite(scores).all()
    assert np.all((scores >= 0) & (scores <= 1))


def test_dataframe_categorical_and_missing_values_remain_supported():
    x, y = fixture_data(3, True)
    frame = pd.DataFrame(x, columns=list("abcd"))
    frame["text"] = np.where(x[:, 0] > 0, "yes", "no")
    frame.loc[::13, "a"] = np.nan
    a = CodAdaptClassifier(class_weight="balanced", **OPTIONS).fit(frame, y)
    b = CodAdaptClassifier(**OPTIONS).fit(frame, y, manual_weights(y))
    assert_same_predictive_state(a, b, frame)
