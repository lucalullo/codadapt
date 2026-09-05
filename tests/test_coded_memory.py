"""Contracts for shared multi-resolution coded memory."""

import numpy as np
import pandas as pd
from numpy.testing import assert_allclose

from codadapt import CodAdaptClassifier, CodAdaptRegressor
from codadapt._training import predict_coded_memory_buckets


def test_default_core_is_additive_and_records_accepted_levels():
    rng = np.random.default_rng(301)
    X = rng.normal(size=(320, 4))
    y = 2.0 * X[:, 0] - X[:, 1] + 0.4 * X[:, 2] * X[:, 3]
    model = CodAdaptRegressor(
        n_bins=32, n_tables=3, table_size=64, early_stopping=False, random_state=42
    ).fit(X, y)
    assert model.resolution_bins_ == [4, 8, 16]
    assert len(model.levels_) == len(model.level_history_) == model.n_iter_
    buckets = model.shared_encoder_.transform_levels(X)
    expected = predict_coded_memory_buckets(
        model.levels_, model.encoders_, buckets, model.intercept_, model.table_size
    )
    assert_allclose(model.predict(X), expected, rtol=0, atol=0)
    objectives = [row["objective"] for row in model.level_history_]
    assert np.all(np.diff(objectives) <= 1e-10 * np.maximum(1.0, np.abs(objectives[:-1])))


def test_default_core_uses_nested_shared_levels():
    rng = np.random.default_rng(302)
    X = rng.uniform(-2, 2, size=(240, 3))
    y = X[:, 0] * X[:, 1] + 0.2 * X[:, 2]
    model = CodAdaptRegressor(early_stopping=False, random_state=7).fit(X, y)
    levels = model.shared_encoder_.transform_levels(X)
    assert len(levels) == 3
    assert all(level.dtype == np.uint16 for level in levels)
    assert model.encoder_ is model.shared_encoder_


def test_default_core_keeps_native_categories_and_stable_missing_buckets():
    X = pd.DataFrame(
        {
            "value": [0.0, 1.0, np.nan, 2.0, -1.0, np.nan] * 20,
            "kind": ["a", "b", None, "a", "c", "b"] * 20,
        }
    )
    y = np.tile([0, 1, 0, 1, 0, 1], 20)
    model = CodAdaptClassifier(n_tables=1, early_stopping=False, random_state=42).fit(X, y)
    query = pd.DataFrame({"value": [np.nan, 0.5], "kind": ["unseen", None]})
    assert np.isfinite(model.predict_proba(query)).all()
    levels = model.shared_encoder_.transform_levels(query)
    for level, view in zip(levels, model.encoders_, strict=True):
        assert level[0, 0] == view.n_buckets_[0] - 1
        assert level[0, 1] == model.shared_encoder_.schemas_[1]["unknown_bucket"]
        assert level[1, 1] == model.shared_encoder_.schemas_[1]["missing_bucket"]


def test_public_params_have_no_architecture_selector():
    params = CodAdaptClassifier().get_params()
    assert "experimental_strategy" not in params
    assert "multi_resolution_levels" not in params
    assert "adaptive_ablation" not in params
    model = CodAdaptClassifier().set_params(random_state=42, verbosity=0)
    assert model.random_state == 42 and model.verbosity == 0
