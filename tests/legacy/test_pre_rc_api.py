"""Deliberate pre-1.0 API cleanup; prediction internals remain unchanged."""

import inspect
import pickle

import joblib
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from sklearn.base import clone
from sklearn.exceptions import NotFittedError
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

import codadapt
import codadapt.experimental as experimental
import codadapt.preprocessing as preprocessing
from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor
from codadapt.preprocessing import BucketEncoder

REMOVED = (
    "max_iter",
    "adapt_codes",
    "adapt_every",
    "max_code_updates",
    "n_candidates",
    "min_code_count",
    "patience",
)


@pytest.mark.parametrize("estimator", [CodAdaptClassifier, CodAdaptRegressor])
@pytest.mark.parametrize("name", REMOVED)
def test_removed_noop_rejected_in_constructor_and_set_params(estimator, name):
    with pytest.raises(TypeError, match=name):
        estimator(**{name: 1})
    model = estimator()
    assert name not in model.get_params()
    with pytest.raises(ValueError, match=name):
        model.set_params(**{name: 1})


@pytest.mark.parametrize("estimator", [CodAdaptClassifier, CodAdaptRegressor])
def test_keyword_only_constructor_prevents_silent_positional_shift(estimator):
    assert all(
        p.kind is inspect.Parameter.KEYWORD_ONLY
        for p in inspect.signature(estimator).parameters.values()
    )
    with pytest.raises(TypeError, match="positional"):
        estimator(8)
    model = estimator(n_bins=8, features_per_table=2, l2=3.0)
    assert clone(model).get_params() == model.get_params()
    assert model.set_params(l2=4.0) is model
    pipeline = Pipeline([("model", model)])
    assert pipeline.set_params(model__l2=5.0)["model"].l2 == 5.0


def test_root_alias_and_private_encoder_exposure_contract():
    assert CodAdapt is CodAdaptClassifier
    assert set(codadapt.__all__) == {
        "CodAdapt",
        "CodAdaptClassifier",
        "CodAdaptRegressor",
        "__version__",
    }
    assert "BucketEncoder" not in experimental.__all__
    assert not hasattr(codadapt, "BucketEncoder")
    assert preprocessing.__all__ == []
    assert BucketEncoder.__module__ == "codadapt.preprocessing"


@pytest.mark.parametrize("estimator", [CodAdaptClassifier, CodAdaptRegressor])
def test_resource_only_parameter_preserves_predictions(estimator):
    rng = np.random.RandomState(429)
    x = rng.normal(size=(80, 4))
    y = np.arange(80) % 2 if estimator is CodAdaptClassifier else x[:, 0] + x[:, 1] ** 2
    options = dict(n_tables=2, table_size=32, random_state=429, early_stopping=False)
    a = estimator(features_per_table=1, **options).fit(x, y)
    b = estimator(features_per_table=4, **options).fit(x, y)
    assert a.estimated_memory_bytes_ < b.estimated_memory_bytes_
    assert_array_equal(a.predict(x), b.predict(x))
    if hasattr(a, "predict_proba"):
        assert_array_equal(a.predict_proba(x), b.predict_proba(x))


def test_internal_encoder_pipeline_persistence_and_failure_guard(tmp_path):
    # Diagnostic internal coverage does not promise a standalone stable API.
    x = pd.DataFrame(
        {"numeric": [0.0, 1.0, np.nan, 3.0] * 10, "category": ["a", "b", None, "a"] * 10}
    )
    y = np.arange(len(x)) % 2
    pipeline = Pipeline([("encoder", BucketEncoder(n_bins=4)), ("model", LogisticRegression())])
    pipeline.fit(x, y)
    expected = pipeline.predict_proba(x)
    for kind in ("pickle", "joblib"):
        path = tmp_path / kind
        if kind == "pickle":
            path.write_bytes(pickle.dumps(pipeline, protocol=5))
            restored = pickle.loads(path.read_bytes())
        else:
            joblib.dump(pipeline, path)
            restored = joblib.load(path)
        assert_array_equal(restored.predict_proba(x), expected)
    encoder = pipeline["encoder"]
    assert clone(encoder).get_params() == encoder.get_params()
    encoder.set_params(n_bins=0)
    with pytest.raises(ValueError, match="n_bins"):
        encoder.fit(x)
    with pytest.raises(NotFittedError):
        encoder.transform(x)
    encoder.set_params(n_bins=4).fit(x.iloc[:1])
    assert encoder.transform(x.iloc[:1]).shape == (1, 2)
