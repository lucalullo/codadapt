"""Public contract of the frozen, fully native experimental regression blend."""

import pickle

import joblib
import numpy as np
import pandas as pd
import pytest
from scipy import sparse
from sklearn.base import clone
from sklearn.exceptions import NotFittedError
from sklearn.model_selection import train_test_split

from codadapt import CodAdaptRegressor
from codadapt.experimental import SafeBlendRegressor


@pytest.fixture(scope="module")
def regression_data():
    rng = np.random.default_rng(781)
    x = rng.normal(size=(180, 3))
    y = 2 * x[:, 0] + np.sin(x[:, 1]) + rng.normal(size=len(x)) * 0.15
    return x, y


def test_minimal_api_and_clone():
    model = SafeBlendRegressor(random_state=42, verbosity=0, n_jobs=4)
    assert model.get_params() == {"random_state": 42, "verbosity": 0, "n_jobs": 4}
    assert clone(model).get_params() == model.get_params()
    assert model.set_params(n_jobs=1) is model
    with pytest.raises(ValueError, match="Invalid parameter"):
        model.set_params(alpha=0.5)
    with pytest.raises(TypeError):
        SafeBlendRegressor(alpha=0.5)


def test_deterministic_fit_attributes_and_no_refit(regression_data):
    x, y = regression_data
    a = SafeBlendRegressor(random_state=42).fit(x, y)
    b = clone(a).fit(x, y)
    np.testing.assert_array_equal(a.predict(x), b.predict(x))
    assert a.branch_ == b.branch_
    assert a.alpha_ == (0.3 if a.branch_ == "BLEND" else 0.0)
    assert a.fit_diagnostics_["refit"] is False
    train, val = train_test_split(np.arange(len(x)), test_size=0.25, random_state=142)
    expected = CodAdaptRegressor(categorical_features=[], random_state=42).fit(
        pd.DataFrame(x[train]), y[train], eval_set=(pd.DataFrame(x[val]), y[val])
    )
    np.testing.assert_array_equal(
        a.base_.predict(pd.DataFrame(x)), expected.predict(pd.DataFrame(x))
    )
    assert a.fit_diagnostics_["train_samples"] == len(train)
    assert a.validation_base_rmse_ >= 0 and a.validation_blend_rmse_ >= 0
    assert not any("teacher" in name for name in vars(a))
    assert not any(name in vars(a) for name in ("X_", "y_", "training_data_", "validation_data_"))


def test_tie_chooses_base_and_discards_rational():
    x = np.zeros((40, 2))
    model = SafeBlendRegressor(random_state=7).fit(x, np.full(40, 3.5))
    assert model.branch_ == "BASE"
    assert model.alpha_ == 0
    assert model.rational_ is None
    assert model.validation_base_rmse_ == model.validation_blend_rmse_ == 0
    np.testing.assert_array_equal(model.predict(x), np.full(40, 3.5))


def test_strict_improvement_retains_blend(monkeypatch, regression_data):
    # A controlled validation fixture checks selection and deployment arithmetic;
    # the scientific replay checks actual Rational fits on both real branches.
    from codadapt.experimental._rational import Rational

    x, y = regression_data
    train, val = train_test_split(np.arange(len(x)), test_size=0.25, random_state=142)
    base = CodAdaptRegressor(categorical_features=[], random_state=42).fit(
        pd.DataFrame(x[train]), y[train], eval_set=(pd.DataFrame(x[val]), y[val])
    )
    b = base.predict(pd.DataFrame(x[val]))
    perfect = b + (y[val] - b) / 0.3
    real_predict = Rational.predict

    def validation_fixture(self, frame):
        return perfect.copy() if len(frame) == len(val) else real_predict(self, frame)

    monkeypatch.setattr(Rational, "predict", validation_fixture)
    model = SafeBlendRegressor(random_state=42).fit(x, y)
    assert model.branch_ == "BLEND" and model.rational_ is not None
    assert model.alpha_ == 0.3
    assert model.validation_blend_rmse_ < model.validation_base_rmse_
    prepared = model._prepare(x)
    b = model.base_.predict(prepared)
    np.testing.assert_array_equal(
        model.predict(x), b + 0.3 * (model.rational_.predict(prepared) - b)
    )


@pytest.mark.parametrize("kind", ["object", "category", "boolean", "nullable_boolean"])
def test_mixed_missing_unseen_and_schema(kind, regression_data):
    values, y = regression_data
    x = pd.DataFrame({"value": values[:, 0], "label": np.where(values[:, 1] > 0, "a", "b")})
    if kind == "category":
        x["label"] = x.label.astype("category")
    elif "boolean" in kind:
        x["label"] = values[:, 1] > 0
        if kind == "nullable_boolean":
            x["label"] = x.label.astype("boolean")
    x.loc[::13, "value"] = np.nan
    if kind != "boolean":
        x.loc[::17, "label"] = None
    model = SafeBlendRegressor(random_state=42).fit(x, y)
    expected = model.predict(x)
    np.testing.assert_array_equal(model.predict(x[["label", "value"]]), expected)
    assert model.feature_names_in_.tolist() == ["value", "label"]
    unseen = x.iloc[:4].copy()
    if kind in {"object", "category"}:
        unseen["label"] = ["never-seen", None, "a", "b"]
    assert np.isfinite(model.predict(unseen)).all()
    with pytest.raises(ValueError, match="schema"):
        model.predict(x.rename(columns={"value": "different"}))
    with pytest.raises(ValueError, match="features"):
        model.predict(x.assign(extra=0))
    with pytest.raises(ValueError, match="representation"):
        model.predict(values[:, :2])


def test_pickle_joblib_reload_does_not_fit(tmp_path, monkeypatch, regression_data):
    x, y = regression_data
    model = SafeBlendRegressor(random_state=42).fit(x, y)
    expected = model.predict(x)
    data = pickle.dumps(model)
    path = tmp_path / "native.joblib"
    joblib.dump(model, path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Reload must not fit")

    monkeypatch.setattr(SafeBlendRegressor, "fit", forbidden)
    for restored in (pickle.loads(data), joblib.load(path)):
        np.testing.assert_array_equal(restored.predict(x), expected)


@pytest.mark.parametrize(
    "y",
    [
        np.arange(30) % 2,
        np.arange(30) % 3,
        np.array(["a", "b", "c"] * 10),
        np.ones((30, 2)),
        np.ones((30, 1)),
        np.full(30, np.nan),
        np.full(30, np.inf),
        np.full(30, True),
        np.full(30, 1 + 2j),
    ],
)
def test_unsupported_targets(y):
    with pytest.raises(ValueError):
        SafeBlendRegressor().fit(np.ones((30, 2)), y)


@pytest.mark.parametrize(
    "x",
    [
        sparse.eye(30),
        np.zeros((30, 2), dtype=complex),
        np.full((30, 2), "a"),
        np.full((30, 2), np.inf),
    ],
)
def test_unsupported_inputs(x):
    with pytest.raises((ValueError, TypeError)):
        SafeBlendRegressor().fit(x, np.linspace(0.1, 5.5, 30))


@pytest.mark.parametrize(
    "params",
    [
        {"n_jobs": 0},
        {"n_jobs": -1},
        {"n_jobs": True},
        {"verbosity": -1},
        {"verbosity": 3},
        {"random_state": True},
        {"random_state": -1},
    ],
)
def test_parameter_errors(params, regression_data):
    with pytest.raises(ValueError):
        SafeBlendRegressor(**params).fit(*regression_data)


def test_not_fitted_and_failed_refit(regression_data):
    model = SafeBlendRegressor(random_state=42)
    with pytest.raises(NotFittedError):
        model.predict(regression_data[0])
    model.fit(*regression_data)
    with pytest.raises(ValueError):
        model.fit(regression_data[0], np.full(len(regression_data[0]), np.nan))
    with pytest.raises(NotFittedError):
        model.predict(regression_data[0])


def test_continuous_integer_regression_is_supported():
    x = np.arange(40, dtype=float).reshape(-1, 1)
    assert np.isfinite(
        SafeBlendRegressor(random_state=4).fit(x, 100 + np.arange(40)).predict(x)
    ).all()


def test_unseeded_fit_and_random_state_instance(regression_data):
    x, y = regression_data
    for seed in (None, np.random.RandomState(4)):
        model = SafeBlendRegressor(random_state=seed).fit(x, y)
        assert np.isfinite(model.predict(x)).all()
