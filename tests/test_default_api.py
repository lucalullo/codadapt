"""The exact minimal public API on automatically handled mixed DataFrames."""

import warnings

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from sklearn.base import clone

from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor


def default_frame():
    rng = np.random.default_rng(49)
    n = 300
    values = rng.normal(size=n)
    frame = pd.DataFrame(
        {
            "numeric": values,
            "nullable_number": pd.array(np.arange(n) % 7, dtype="Int64"),
            "text": np.where(values > 0, "alto", "basso").astype(object),
            "category": pd.Categorical(
                np.where(np.arange(n) % 2, "a", "b"), categories=["a", "b", "declared-unobserved"]
            ),
            "nullable_boolean": pd.array(np.arange(n) % 2 == 0, dtype="boolean"),
            "all_missing": np.full(n, np.nan),
        }
    )
    frame.loc[::11, "numeric"] = np.nan
    frame.loc[::13, "nullable_number"] = pd.NA
    frame.loc[::17, "text"] = None
    frame.loc[::19, "category"] = np.nan
    frame.loc[::23, "nullable_boolean"] = pd.NA
    return frame, (values > 0).astype(int), np.round(4 * values).astype(int)


def test_public_alias_is_explicit():
    assert CodAdapt is CodAdaptClassifier


@pytest.mark.parametrize("binary", [True, False])
def test_exact_minimum_api_handles_mixed_missing_and_unseen_data(binary, capsys):
    X, classification_y, regression_y = default_frame()
    model = (
        CodAdapt(random_state=42, verbosity=0)
        if binary
        else CodAdaptRegressor(random_state=42, verbosity=0)
    )
    y = classification_y if binary else regression_y
    warning_filters_before = list(warnings.filters)
    assert model.fit(X, y) is model
    assert warnings.filters == warning_filters_before
    query = X.iloc[:6].copy()
    query["category"] = query["category"].cat.add_categories(["unseen"])
    query.loc[query.index[0], "category"] = "unseen"
    query.loc[query.index[1], "text"] = "never-seen"
    query.loc[query.index[2], "numeric"] = np.nan
    query.loc[query.index[3], "nullable_boolean"] = pd.NA
    query.loc[query.index[4], "all_missing"] = 123
    prediction = model.predict(query)
    assert prediction.shape == (6,)
    assert np.isfinite(prediction).all()
    if binary:
        assert model.predict_proba(query).shape == (6, 2)
    else:
        assert not hasattr(model, "classes_")
    params = model.get_params()
    assert params["random_state"] == 42 and params["verbosity"] == 0
    assert "verbose" not in params
    cloned = clone(model)
    assert cloned.get_params() == params
    assert not hasattr(cloned, "n_features_in_")
    assert cloned.set_params(verbosity=1) is cloned
    assert cloned.verbosity == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warnings.warn("diagnostic sentinel", UserWarning, stacklevel=1)
    assert len(caught) == 1 and str(caught[0].message) == "diagnostic sentinel"


def test_dataframe_names_realign_and_reject_invalid_schema():
    X, y, _ = default_frame()
    model = CodAdapt(n_tables=1, max_iter=3, random_state=42, verbosity=0).fit(X, y)
    assert_array_equal(model.feature_names_in_, X.columns.to_numpy())
    assert_array_equal(model.predict(X), model.predict(X[X.columns[::-1]]))
    invalid = [X.drop(columns=["text"]), X.assign(extra=1), X.to_numpy()]
    duplicate = X.copy()
    duplicate.columns = [
        "numeric",
        "numeric",
        "text",
        "category",
        "nullable_boolean",
        "all_missing",
    ]
    invalid.append(duplicate)
    for frame in invalid:
        with pytest.raises((ValueError, TypeError)):
            model.predict(frame)
