"""Training-only quantile and categorical buckets, separate from learned codes."""

from enum import Enum
from numbers import Integral, Real

import numpy as np
import pandas as pd
from pandas.api.types import (
    infer_dtype,
    is_bool_dtype,
    is_complex_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
    is_string_dtype,
    is_timedelta64_dtype,
)
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils import check_random_state
from sklearn.utils.validation import check_is_fitted


class _BooleanKey(Enum):
    """Avoid Python's equality collision between True/1 and False/0."""

    FALSE = "false"
    TRUE = "true"


class _ResolutionView:
    """Minimal per-level metadata over one shared fitted encoder."""

    def __init__(self, n_buckets, support):
        self.n_buckets_ = n_buckets
        self.support_ = support


class BucketEncoder(TransformerMixin, BaseEstimator):
    """Encode supported features into compact, deterministic integer buckets.

    Numeric thresholds use linear training quantiles in float64. Values equal
    to a threshold enter the interval on its right; finite extremes enter the
    outer intervals. The final numeric bucket is reserved for missing values.
    Categorical buckets 0, 1 and 2 mean missing, observed-rare and unseen.
    Frequency ties preserve first observation order. Strings, booleans and
    numbers are distinct; equal integers/floats describe the same category.
    ``schemas_`` stores thresholds/vocabularies but never training rows.
    """

    def __init__(
        self,
        n_bins=32,
        max_categories=128,
        quantile_sample_size=20000,
        categorical_features=None,
        random_state=None,
    ):
        self.n_bins = n_bins
        self.max_categories = max_categories
        self.quantile_sample_size = quantile_sample_size
        self.categorical_features = categorical_features
        self.random_state = random_state

    def _validate_parameters(self):
        for name, upper in (
            ("n_bins", 4096),
            ("max_categories", 4096),
            ("quantile_sample_size", 1_000_000),
        ):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
                raise ValueError(f"{name} must be an integer between 1 and {upper}.")
            if not 1 <= value <= upper:
                raise ValueError(f"{name} must be between 1 and {upper}.")

    @staticmethod
    def _validate_input(X):
        if sparse.issparse(X):
            raise TypeError(
                "Sparse input is not supported; provide dense numeric arrays or a DataFrame."
            )
        if isinstance(X, pd.DataFrame):
            if X.columns.has_duplicates:
                raise ValueError("DataFrame feature names must not contain duplicate columns.")
        else:
            try:
                X = np.asarray(X)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "X must be a two-dimensional numeric array or a DataFrame."
                ) from exc
            if X.ndim != 2:
                raise ValueError(
                    f"Expected 2D array, got {X.ndim}D array instead. Reshape your data."
                )
            if X.dtype.kind == "c":
                raise ValueError("Complex data not supported.")
            if X.dtype.kind not in "biuf":
                raise TypeError(
                    "NumPy arrays must contain real numeric values; use a DataFrame for categories."
                )
        if X.shape[0] == 0:
            raise ValueError(
                f"Found array with 0 sample(s) (shape={X.shape}); a minimum of 1 is required."
            )
        if X.shape[1] == 0:
            raise ValueError(
                f"Found array with 0 feature(s) (shape={X.shape}); a minimum of 1 is required."
            )
        if int(X.shape[0]) * int(X.shape[1]) * np.dtype(np.uint16).itemsize > 512 * 1024**2:
            raise ValueError(
                "Encoded input would exceed the 512 MiB bucket allocation limit; use smaller batches."
            )
        return X

    @staticmethod
    def _column(X, j):
        return X.iloc[:, j] if isinstance(X, pd.DataFrame) else pd.Series(X[:, j], copy=False)

    @staticmethod
    def _check_dtype(series, feature):
        dtype = series.dtype
        if is_complex_dtype(dtype):
            raise ValueError(f"Complex data not supported in feature {feature!r}.")
        if is_datetime64_any_dtype(dtype) or is_timedelta64_dtype(dtype):
            raise TypeError(
                f"Date/time feature {feature!r} must be transformed explicitly before fitting."
            )

    def _categorical_indices(self, X):
        declared = self.categorical_features
        indices = set()
        if declared is not None:
            if isinstance(declared, (str, bytes)):
                raise ValueError(
                    "categorical_features must be a sequence of column names or indices."
                )
            try:
                declared = list(declared)
            except TypeError as exc:
                raise ValueError(
                    "categorical_features must be a sequence of column names or indices."
                ) from exc
            for feature in declared:
                if isinstance(feature, (bool, np.bool_)):
                    raise ValueError(
                        "categorical_features entries must be names or integer indices, not booleans."
                    )
                if isinstance(feature, Integral):
                    j = int(feature)
                    if not 0 <= j < X.shape[1]:
                        raise ValueError(f"Categorical feature index {j} is out of range.")
                elif isinstance(feature, str) and isinstance(X, pd.DataFrame):
                    if feature not in X.columns:
                        raise ValueError(f"Unknown categorical feature name {feature!r}.")
                    j = X.columns.get_loc(feature)
                else:
                    raise ValueError(
                        "Use column names or integer indices for DataFrames, and indices for arrays."
                    )
                if j in indices:
                    raise ValueError(f"Categorical feature {feature!r} is declared more than once.")
                indices.add(j)
        for j in range(X.shape[1]):
            series = self._column(X, j)
            self._check_dtype(series, j)
            dtype = series.dtype
            if is_bool_dtype(dtype) or isinstance(dtype, pd.CategoricalDtype):
                indices.add(j)
            elif is_object_dtype(dtype) or is_string_dtype(dtype):
                indices.add(j)
            elif not is_numeric_dtype(dtype):
                raise TypeError(f"Unsupported dtype {dtype!r} in feature {j}.")
        return indices

    @staticmethod
    def _numeric_values(series, feature):
        BucketEncoder._check_dtype(series, feature)
        if not is_numeric_dtype(series.dtype):
            inferred = infer_dtype(series, skipna=True)
            if not is_object_dtype(series.dtype) or inferred not in (
                "empty",
                "integer",
                "floating",
                "mixed-integer-float",
                "boolean",
            ):
                raise TypeError(
                    f"Numeric feature {feature!r} received nonnumeric or ambiguous values."
                )
        try:
            values = series.to_numpy(dtype=np.float64, na_value=np.nan, copy=True)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"Feature {feature!r} cannot be converted to finite float64 values."
            ) from exc
        if np.isinf(values).any():
            raise ValueError(
                f"Input contains infinity in feature {feature!r}; infinities are not supported."
            )
        return values

    @staticmethod
    def _categorical_values(series, feature):
        BucketEncoder._check_dtype(series, feature)
        values = series.to_numpy(dtype=object, na_value=None, copy=True)
        missing = pd.isna(series).to_numpy(dtype=bool)
        try:
            observed = pd.unique(values[~missing])
        except TypeError as exc:
            raise TypeError(
                f"Feature {feature!r} contains unsupported nonscalar categories."
            ) from exc
        for value in observed:
            if isinstance(value, (str, bool, np.bool_, Integral)):
                continue
            if isinstance(value, Real):
                if not np.isfinite(value):
                    raise ValueError(f"Input contains infinity in categorical feature {feature!r}.")
                continue
            raise TypeError(
                f"Feature {feature!r} contains unsupported category type {type(value).__name__}; "
                "only strings, finite numbers, booleans and missing values are supported."
            )
        inferred = infer_dtype(values, skipna=True)
        if inferred == "boolean":
            truth = series.to_numpy(dtype=bool, na_value=False)
            values[~missing & truth] = _BooleanKey.TRUE
            values[~missing & ~truth] = _BooleanKey.FALSE
        elif inferred in ("mixed", "mixed-integer"):
            # Native pandas string operations preserve boolean/number identity
            # even though Python equality and pandas.unique collapse True/1.
            objects = pd.Series(values, copy=False)
            strings = objects.str.fullmatch(r"(?s).*", na=False).to_numpy(dtype=bool)
            text = objects.astype("string")
            true = text.eq("True").fillna(False).to_numpy(dtype=bool) & ~strings
            false = text.eq("False").fillna(False).to_numpy(dtype=bool) & ~strings
            numeric_kind = infer_dtype(objects[~missing & ~strings & ~true & ~false], skipna=True)
            if numeric_kind not in ("empty", "integer", "floating", "mixed-integer-float"):
                raise TypeError(
                    f"Feature {feature!r} contains unsupported or ambiguous scalar categories."
                )
            values[true], values[false] = _BooleanKey.TRUE, _BooleanKey.FALSE
        return pd.Series(values, dtype=object, copy=False), missing

    def _fit_numeric(self, series, feature, sample):
        values = self._numeric_values(series, feature)
        sampled = values if sample is None else values[sample]
        sampled = np.sort(sampled[~np.isnan(sampled)])
        thresholds = np.empty(0, dtype=np.float64)
        if sampled.size > 1 and sampled[0] != sampled[-1] and self.n_bins > 1:
            positions = np.linspace(0, 1, self.n_bins + 1)[1:-1] * (sampled.size - 1)
            left = positions.astype(np.intp)
            fraction = positions - left
            right = np.minimum(left + 1, sampled.size - 1)
            # Convex interpolation avoids overflow in (right_value-left_value).
            thresholds = np.unique((1 - fraction) * sampled[left] + fraction * sampled[right])
            thresholds = thresholds[(thresholds > sampled[0]) & (thresholds <= sampled[-1])]
        schema = {
            "kind": "numeric",
            "thresholds": thresholds,
            "missing_bucket": len(thresholds) + 1,
        }
        buckets = self._transform_numeric(values, schema)
        return schema, buckets, len(thresholds) + 2

    @staticmethod
    def _transform_numeric(values, schema):
        buckets = np.searchsorted(schema["thresholds"], values, side="right").astype(np.uint16)
        buckets[np.isnan(values)] = schema["missing_bucket"]
        return buckets

    def _fit_categorical(self, series, feature):
        values, missing = self._categorical_values(series, feature)
        counts = (
            values[~missing].value_counts(sort=False).sort_values(ascending=False, kind="stable")
        )
        if len(counts) > 1_000_000:
            raise ValueError(
                f"Feature {feature!r} exceeds the 1,000,000 observed-category membership limit."
            )
        vocabulary = {key: j + 3 for j, key in enumerate(counts.index[: self.max_categories])}
        schema = {
            "kind": "categorical",
            "vocabulary": vocabulary,
            "observed_categories": counts.index.copy(),
            "missing_bucket": 0,
            "rare_bucket": 1,
            "unknown_bucket": 2,
            "n_rare_categories": max(0, len(counts) - len(vocabulary)),
        }
        return schema, self._transform_categorical(values, missing, schema), len(vocabulary) + 3

    @staticmethod
    def _transform_categorical(values, missing, schema):
        mapped = values.map(schema["vocabulary"])
        buckets = mapped.fillna(schema["unknown_bucket"]).to_numpy(dtype=np.uint16)
        if schema["n_rare_categories"]:
            rare = mapped.isna().to_numpy() & values.isin(schema["observed_categories"]).to_numpy()
            buckets[rare] = schema["rare_bucket"]
        buckets[missing] = schema["missing_bucket"]
        return buckets

    def fit_transform(self, X, y=None, **fit_params):
        """Learn representation and return buckets without retaining input rows."""
        if fit_params:
            raise TypeError("BucketEncoder does not accept additional fit parameters.")
        if hasattr(self, "_is_fitted_"):
            del self._is_fitted_
        self._validate_parameters()
        X = self._validate_input(X)
        categorical = self._categorical_indices(X)
        rng = (
            np.random.RandomState()
            if self.random_state is None
            else check_random_state(self.random_state)
        )
        sample = None
        if X.shape[0] > self.quantile_sample_size:
            sample = rng.choice(X.shape[0], size=self.quantile_sample_size, replace=False)
        transformed = np.empty(X.shape, dtype=np.uint16)
        schemas, support, sizes = [], [], []
        for j in range(X.shape[1]):
            series = self._column(X, j)
            feature = X.columns[j] if isinstance(X, pd.DataFrame) else j
            if j in categorical:
                schema, buckets, size = self._fit_categorical(series, feature)
            else:
                schema, buckets, size = self._fit_numeric(series, feature, sample)
            transformed[:, j] = buckets
            schemas.append(schema)
            support.append(np.bincount(buckets, minlength=size) > 0)
            sizes.append(size)
        self.n_features_in_ = X.shape[1]
        self._fit_dataframe_ = isinstance(X, pd.DataFrame)
        self._columns_ = X.columns.copy() if self._fit_dataframe_ else None
        if hasattr(self, "feature_names_in_"):
            del self.feature_names_in_
        if self._fit_dataframe_ and all(isinstance(name, str) for name in X.columns):
            self.feature_names_in_ = X.columns.to_numpy(dtype=object, copy=True)
        self.schemas_, self.support_, self.n_buckets_ = schemas, support, sizes
        self.categorical_features_ = np.array(sorted(categorical), dtype=np.intp)
        self._is_fitted_ = True
        return transformed

    def fit(self, X, y=None):
        """Fit exclusively on the effective training rows supplied by the caller."""
        self.fit_transform(X, y)
        return self

    def transform(self, X):
        """Apply the frozen representation; unseen categorical buckets stay unsupported."""
        check_is_fitted(self, "_is_fitted_")
        X = self._validate_input(X)
        if isinstance(X, pd.DataFrame) != self._fit_dataframe_:
            raise ValueError(
                "Input must use the same DataFrame/array representation as during fit."
            )
        if X.shape[1] != self.n_features_in_:
            raise ValueError(
                f"X has {X.shape[1]} features, but BucketEncoder is expecting {self.n_features_in_} features as input."
            )
        if self._fit_dataframe_:
            order = X.columns.get_indexer(self._columns_)
            if np.any(order < 0):
                raise ValueError(
                    "DataFrame columns must match the fitted schema; missing or additional features found."
                )
            if not X.columns.equals(self._columns_):
                X = X.iloc[:, order]
        transformed = np.empty(X.shape, dtype=np.uint16)
        for j, schema in enumerate(self.schemas_):
            series = self._column(X, j)
            feature = X.columns[j] if self._fit_dataframe_ else j
            if schema["kind"] == "numeric":
                transformed[:, j] = self._transform_numeric(
                    self._numeric_values(series, feature), schema
                )
            else:
                values, missing = self._categorical_values(series, feature)
                transformed[:, j] = self._transform_categorical(values, missing, schema)
        return transformed

    def fit_transform_levels(self, X, resolutions):
        """Fit one finest representation and derive nested integer bucket levels."""
        finest = self.fit_transform(X)
        self.resolution_bins_ = [int(value) for value in resolutions]
        self.level_mappings_, self.level_views_ = [], []
        levels = []
        for resolution in self.resolution_bins_:
            transformed = np.empty_like(finest)
            mappings, sizes, support = [], [], []
            for feature, schema in enumerate(self.schemas_):
                if schema["kind"] == "numeric":
                    finite_count = int(schema["missing_bucket"])
                    level_count = max(1, min(resolution, finite_count))
                    mapping = np.empty(finite_count + 1, dtype=np.uint16)
                    mapping[:finite_count] = (
                        np.arange(finite_count, dtype=np.int64) * level_count // finite_count
                    ).astype(np.uint16)
                    mapping[finite_count] = level_count
                    size = level_count + 1
                else:
                    size = self.n_buckets_[feature]
                    mapping = np.arange(size, dtype=np.uint16)
                transformed[:, feature] = mapping[finest[:, feature]]
                mappings.append(mapping)
                sizes.append(size)
                support.append(np.bincount(transformed[:, feature], minlength=size) > 0)
            self.level_mappings_.append(mappings)
            self.level_views_.append(_ResolutionView(sizes, support))
            levels.append(transformed)
        return levels

    def transform_levels(self, X):
        """Transform once at the finest resolution, then apply cached integer maps."""
        check_is_fitted(self, "level_mappings_")
        finest = self.transform(X)
        levels = []
        for mappings in self.level_mappings_:
            transformed = np.empty_like(finest)
            for feature, mapping in enumerate(mappings):
                transformed[:, feature] = mapping[finest[:, feature]]
            levels.append(transformed)
        return levels
