import pickle

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from scipy import sparse
from sklearn.base import clone
from sklearn.exceptions import NotFittedError

from codadapt.preprocessing import BucketEncoder


def test_numeric_borders_missing_extremes_and_support():
    encoder = BucketEncoder(n_bins=2).fit(np.array([[0.0], [1.0], [2.0], [3.0]]))
    assert_array_equal(encoder.schemas_[0]["thresholds"], [1.5])
    assert_array_equal(
        encoder.transform(np.array([[-100.0], [1.499], [1.5], [100.0], [np.nan]]))[:, 0],
        [0, 0, 1, 1, 2],
    )
    assert_array_equal(encoder.support_[0], [True, True, False])
    assert encoder.n_buckets_ == [3]


def test_constant_and_all_missing_numerics():
    X = np.array([[7.0, np.nan], [7.0, np.nan], [7.0, np.nan]])
    encoder = BucketEncoder(n_bins=32)
    assert_array_equal(encoder.fit_transform(X), [[0, 1], [0, 1], [0, 1]])
    assert encoder.n_buckets_ == [2, 2]
    assert_array_equal(encoder.support_[0], [True, False])
    assert_array_equal(encoder.support_[1], [False, True])
    assert_array_equal(encoder.transform(np.array([[np.nan, 0]])), [[1, 0]])


def test_numeric_thresholds_preserve_float64_precision():
    X = np.array([[1.0], [1 + 1e-10], [1 + 2e-10], [1 + 3e-10]], dtype=np.float64)
    encoder = BucketEncoder(n_bins=4).fit(X)
    assert len(encoder.schemas_[0]["thresholds"]) == 3
    assert encoder.schemas_[0]["thresholds"].dtype == np.float64
    assert len(np.unique(encoder.transform(X))) == 4


def test_discrete_numeric_quantiles_retain_upper_boundary():
    X = np.repeat([0.0, 1.0], [81, 20]).reshape(-1, 1)
    encoder = BucketEncoder(n_bins=32).fit(X)
    assert_array_equal(encoder.schemas_[0]["thresholds"], [1.0])
    assert_array_equal(encoder.transform(np.array([[0.0], [1.0]])), [[0], [1]])
    three_values = np.repeat([0.0, 1.0, 2.0], [60, 25, 15]).reshape(-1, 1)
    encoder.fit(three_values)
    assert len(np.unique(encoder.transform(np.array([[0.0], [1.0], [2.0]])))) == 3


def test_extreme_finite_quantiles_do_not_overflow():
    X = np.array([[-1.7e308], [1.7e308]])
    encoder = BucketEncoder(n_bins=4).fit(X)
    assert np.isfinite(encoder.schemas_[0]["thresholds"]).all()
    assert_array_equal(encoder.transform(X), [[0], [3]])


def test_quantile_sample_reproducible_without_global_rng_mutation():
    X = np.linspace(0, 100, 1000).reshape(-1, 1)
    before = np.random.get_state()
    first = BucketEncoder(n_bins=8, quantile_sample_size=40, random_state=71).fit(X)
    second = BucketEncoder(n_bins=8, quantile_sample_size=40, random_state=71).fit(X)
    other = BucketEncoder(n_bins=8, quantile_sample_size=40, random_state=72).fit(X)
    after = np.random.get_state()
    assert_array_equal(first.schemas_[0]["thresholds"], second.schemas_[0]["thresholds"])
    assert not np.array_equal(first.schemas_[0]["thresholds"], other.schemas_[0]["thresholds"])
    assert before[0] == after[0] and before[2:] == after[2:]
    assert_array_equal(before[1], after[1])


def test_rare_unseen_missing_and_frequency_ties():
    X = pd.DataFrame({"city": ["b", "a", "b", "a", "c", None]})
    encoder = BucketEncoder(max_categories=1).fit(X)
    assert encoder.schemas_[0]["vocabulary"] == {"b": 3}
    assert_array_equal(
        encoder.transform(pd.DataFrame({"city": ["b", "a", "c", "d", None, pd.NA, np.nan]}))[:, 0],
        [3, 1, 1, 2, 0, 0, 0],
    )
    assert_array_equal(encoder.support_[0], [True, True, False, True])
    assert encoder.n_buckets_ == [4]


def test_category_dtype_uses_observed_values_only():
    X = pd.DataFrame(
        {"city": pd.Categorical(["a", "a", None], categories=["a", "validation_only"])}
    )
    encoder = BucketEncoder().fit(X)
    assert list(encoder.schemas_[0]["observed_categories"]) == ["a"]
    assert "validation_only" not in encoder.schemas_[0]["vocabulary"]
    assert_array_equal(encoder.transform(pd.DataFrame({"city": ["validation_only"]})), [[2]])


def test_mixed_nullable_dataframe_is_supported_without_mutation():
    X = pd.DataFrame(
        {
            "float": [1.5, np.nan, 3.5, 0],
            "int": pd.Series([1, pd.NA, 3, 0], dtype="Int64"),
            "nullable_float": pd.Series([1, pd.NA, 3, 0], dtype="Float64"),
            "flag": pd.Series([True, False, pd.NA, True], dtype="boolean"),
            "category": pd.Categorical(["x", "y", None, "x"]),
            "object": ["x", None, "y", "z"],
            "text": pd.Series(["x", pd.NA, "y", "z"], dtype="string"),
        }
    )
    original = X.copy(deep=True)
    encoder = BucketEncoder()
    buckets = encoder.fit_transform(X)
    assert buckets.dtype == np.uint16 and buckets.shape == X.shape
    assert_array_equal(buckets, encoder.transform(X))
    pd.testing.assert_frame_equal(X, original)
    assert_array_equal(encoder.categorical_features_, [3, 4, 5, 6])
    assert_array_equal(encoder.feature_names_in_, X.columns)


def test_category_types_are_distinct_including_booleans():
    X = pd.DataFrame({"category": [1, "1", True, 0, False, "True", 1.0, None]})
    encoder = BucketEncoder()
    buckets = encoder.fit_transform(X)[:, 0]
    assert len(set(buckets[:6])) == 6
    assert buckets[0] == buckets[6]
    assert buckets[7] == 0
    assert_array_equal(encoder.transform(X)[:, 0], buckets)
    assert_array_equal(
        encoder.transform(pd.DataFrame({"category": [True, False]}))[:, 0], buckets[[2, 4]]
    )


def test_object_numeric_categories_accept_mixed_integer_float():
    X = pd.DataFrame({"category": pd.Series([1, 1.5, None], dtype=object)})
    encoder = BucketEncoder().fit(X)
    assert encoder.schemas_[0]["kind"] == "categorical"
    assert_array_equal(encoder.transform(X)[:, 0], [3, 4, 0])


def test_all_missing_categorical_and_absence_of_rare_support():
    encoder = BucketEncoder().fit(pd.DataFrame({"a": [None, pd.NA, np.nan]}))
    assert encoder.schemas_[0]["vocabulary"] == {}
    assert_array_equal(encoder.support_[0], [True, False, False])
    assert_array_equal(encoder.transform(pd.DataFrame({"a": ["new", None]})), [[2], [0]])


@pytest.mark.parametrize("selectors", [["a"], [0]])
def test_declare_numeric_dataframe_category(selectors):
    X = pd.DataFrame({"a": [10, 20, 10], "b": [1, 2, 3]})
    encoder = BucketEncoder(categorical_features=selectors).fit(X)
    assert [schema["kind"] for schema in encoder.schemas_] == ["categorical", "numeric"]
    assert encoder.transform(pd.DataFrame({"a": [99], "b": [2]}))[0, 0] == 2


def test_declare_numeric_array_category_and_preserve_array():
    X = np.array([[10, 1], [20, 2], [10, 3]])
    before = X.copy()
    encoder = BucketEncoder(categorical_features=[0]).fit(X)
    assert encoder.schemas_[0]["kind"] == "categorical"
    assert encoder.transform(np.array([[99, 4]]))[0, 0] == 2
    assert_array_equal(X, before)


def test_dataframe_reordering_and_nonstring_names():
    X = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "x"]})
    encoder = BucketEncoder().fit(X)
    assert_array_equal(encoder.transform(X[["b", "a"]]), encoder.transform(X))
    numbered = X.set_axis([10, 20], axis=1)
    encoder.fit(numbered)
    assert not hasattr(encoder, "feature_names_in_")
    assert_array_equal(encoder.transform(numbered[[20, 10]]), encoder.transform(numbered))


@pytest.mark.parametrize("columns", [["a"], ["a", "b", "c"], ["a", "c"], ["a", "a"]])
def test_dataframe_schema_rejects_missing_extra_and_duplicate_columns(columns):
    encoder = BucketEncoder().fit(pd.DataFrame({"a": [1, 2], "b": [3, 4]}))
    with pytest.raises(ValueError):
        encoder.transform(pd.DataFrame(np.ones((2, len(columns))), columns=columns))


def test_duplicate_columns_rejected_during_fit():
    with pytest.raises(ValueError, match="duplicate"):
        BucketEncoder().fit(pd.DataFrame([[1, 2]], columns=["a", "a"]))


def test_dataframe_and_array_representation_are_not_interchangeable():
    array = np.array([[1, 2], [3, 4]])
    frame = pd.DataFrame(array, columns=["a", "b"])
    with pytest.raises(ValueError, match="same DataFrame/array"):
        BucketEncoder().fit(frame).transform(array)
    with pytest.raises(ValueError, match="same DataFrame/array"):
        BucketEncoder().fit(array).transform(frame)


@pytest.mark.parametrize(
    "X",
    [
        np.ones((2, 1), dtype=complex),
        pd.DataFrame({"a": [1 + 2j, 0j]}),
        pd.DataFrame({"a": pd.date_range("2020-01-01", periods=2)}),
        pd.DataFrame({"a": pd.to_timedelta([1, 2], unit="D")}),
        pd.DataFrame({"a": [[1], [2]]}),
        pd.DataFrame({"a": [{"x": 1}, {"x": 2}]}),
        pd.DataFrame({"a": [object(), object()]}),
        pd.DataFrame({"a": pd.Series([1, 1 + 0j, "a"], dtype=object)}),
        np.array([["a"]], dtype=object),
        sparse.csr_matrix(np.eye(2)),
    ],
)
def test_unsupported_inputs_are_rejected(X):
    with pytest.raises((ValueError, TypeError)):
        BucketEncoder().fit(X)


@pytest.mark.parametrize(
    "X", [np.array([[np.inf]]), np.array([[-np.inf]]), pd.DataFrame({"a": ["a", np.inf]})]
)
def test_infinity_is_rejected_in_numeric_and_categorical_data(X):
    with pytest.raises(ValueError, match="infinity"):
        BucketEncoder().fit(X)


def test_new_numeric_missing_is_allowed_but_strings_are_rejected():
    encoder = BucketEncoder().fit(pd.DataFrame({"a": [0.0, 1.0]}))
    assert (
        encoder.transform(pd.DataFrame({"a": [None]}))[0, 0]
        == encoder.schemas_[0]["missing_bucket"]
    )
    with pytest.raises(TypeError, match="nonnumeric"):
        encoder.transform(pd.DataFrame({"a": ["1"]}))


@pytest.mark.parametrize(
    "selectors", ["a", [True], [-1], [2], ["missing"], [0, 0], [0, "a"], [0.5]]
)
def test_invalid_categorical_declarations(selectors):
    with pytest.raises(ValueError):
        BucketEncoder(categorical_features=selectors).fit(pd.DataFrame({"a": [1, 2]}))


@pytest.mark.parametrize(
    "name,value",
    [
        ("n_bins", 0),
        ("n_bins", 4097),
        ("n_bins", 2.5),
        ("n_bins", True),
        ("max_categories", 0),
        ("max_categories", 4097),
        ("quantile_sample_size", 0),
        ("quantile_sample_size", 1_000_001),
    ],
)
def test_parameter_limits(name, value):
    with pytest.raises(ValueError, match=name):
        BucketEncoder(**{name: value}).fit(np.ones((2, 1)))


def test_high_cardinality_long_strings_frequent_cap_and_frozen_vocabulary():
    values = [f"{j:05d}-" + "long-category" * 20 for j in range(2000)]
    encoder = BucketEncoder(max_categories=5).fit(pd.DataFrame({"a": values + values[:10]}))
    before = pickle.dumps(encoder)
    assert len(encoder.schemas_[0]["vocabulary"]) == 5
    assert len(encoder.schemas_[0]["observed_categories"]) == 2000
    assert encoder.transform(pd.DataFrame({"a": [values[-1], "unseen"]})).tolist() == [[1], [2]]
    assert pickle.dumps(encoder) == before


def test_refit_clone_not_fitted_and_pickle():
    X = pd.DataFrame({"a": [1, "1", True, None]})
    encoder = BucketEncoder(n_bins=4, random_state=4).fit(X)
    with pytest.raises(NotFittedError):
        clone(encoder).transform(X)
    assert clone(encoder).get_params() == encoder.get_params()
    restored = pickle.loads(pickle.dumps(encoder))
    assert_array_equal(restored.transform(X), encoder.transform(X))
    encoder.fit(np.array([[1.0], [2.0]]))
    assert not hasattr(encoder, "feature_names_in_")
    assert encoder.schemas_[0]["kind"] == "numeric"
    assert not any(isinstance(value, pd.DataFrame) for value in vars(encoder).values())


@pytest.mark.parametrize(
    "X", [np.array([1, 2]), np.ones((0, 2)), np.ones((2, 0)), np.ones((2, 2, 2))]
)
def test_invalid_dimensions_and_empty_input(X):
    with pytest.raises(ValueError):
        BucketEncoder().fit(X)


def test_bucket_allocation_rejected_before_large_output():
    X = np.broadcast_to(np.array(1.0), (2**20, 257))
    with pytest.raises(ValueError, match="512 MiB"):
        BucketEncoder().fit(X)
