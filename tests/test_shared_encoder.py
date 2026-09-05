"""Contracts for the shared encoder used by the official core."""

import numpy as np
import pandas as pd
from numpy.testing import assert_array_equal

from codadapt import CodAdaptClassifier, CodAdaptRegressor
from codadapt.preprocessing import BucketEncoder


def test_shared_encoder_derives_nested_levels_with_stable_missing_and_categories():
    X = pd.DataFrame(
        {"value": [0.0, 1.0, 2.0, 3.0, np.nan] * 20, "kind": ["a", "b", None, "a", "c"] * 20}
    )
    encoder = BucketEncoder(n_bins=16, random_state=42)
    levels = encoder.fit_transform_levels(X, [4, 8, 16])
    assert len(levels) == 3
    assert all(level.dtype == np.uint16 and level.shape == X.shape for level in levels)
    assert_array_equal(levels, encoder.transform_levels(X))
    assert_array_equal(levels[0][:, 1], levels[1][:, 1])
    assert_array_equal(levels[1][:, 1], levels[2][:, 1])
    for level, view in zip(levels, encoder.level_views_, strict=True):
        assert level[4, 0] == view.n_buckets_[0] - 1


def test_default_calls_shared_transform_once_per_prediction(monkeypatch):
    rng = np.random.default_rng(501)
    X = rng.normal(size=(300, 5))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    model = CodAdaptClassifier(lookup_budget=16, early_stopping=False, random_state=42).fit(X, y)
    calls = 0
    original = model.shared_encoder_.transform

    def counted(values):
        nonlocal calls
        calls += 1
        return original(values)

    monkeypatch.setattr(model.shared_encoder_, "transform", counted)
    probability = model.predict_proba(X[:40])
    assert calls == 1 and np.isfinite(probability).all()


def test_default_obeys_budget_and_stops_features():
    rng = np.random.default_rng(502)
    X = rng.normal(size=(420, 14))
    y = 4 * X[:, 0] - X[:, 1] + 0.1 * rng.normal(size=len(X))
    model = CodAdaptRegressor(lookup_budget=12, early_stopping=False, random_state=42).fit(X, y)
    assert model.lookup_count_per_sample_ <= 12
    assert model.prefilter_discarded_ > 0
    assert model.feature_level_stopping_ > 0
    assert model.fully_screened_candidates_ < X.shape[1] * 3
    assert model.screening_seconds_ >= 0


def test_default_coded_memory_is_deterministic():
    rng = np.random.default_rng(503)
    X = rng.normal(size=(240, 4))
    y = X[:, 0] * X[:, 1]
    params = dict(lookup_budget=10, early_stopping=False, random_state=42)
    first = CodAdaptRegressor(**params).fit(X, y)
    second = CodAdaptRegressor(**params).fit(X, y)
    assert_array_equal(first.predict(X), second.predict(X))
    assert hasattr(first, "shared_encoder_")
    assert first.resolution_bins_ == [4, 8, 16]
