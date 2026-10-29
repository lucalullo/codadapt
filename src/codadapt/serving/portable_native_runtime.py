"""PRIVATE same-version fitted-only serving image. Not a sklearn estimator API.

Numerical encoder/addressing/accumulation functions are copied unchanged from
the frozen CodAdapt source. Training, clone, get_params and fit are not exposed.
"""

import hashlib
import json
import pickle
import sys
from enum import Enum
from numbers import Integral, Real
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import (
    infer_dtype,
    is_complex_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
    is_timedelta64_dtype,
)


class _SparseInputs:
    @staticmethod
    def issparse(value):
        # A genuine SciPy object requires its module already loaded by its caller.
        # Delegate the exact public predicate if present; no serving dependency import.
        module = sys.modules.get("scipy.sparse")
        return module.issparse(value) if module is not None else False


sparse = _SparseInputs()


def check_is_fitted(model, attributes=None):
    # Images are always fitted and hash-validated; there is no unfitted constructor.
    names = [attributes] if isinstance(attributes, str) else attributes
    if names is not None and not all(hasattr(model, name) for name in names):
        raise ValueError("Invalid frozen encoder state")
    if not getattr(model, "_is_fitted_", False):
        raise ValueError("Invalid unfitted inference image")


class _BooleanKey(Enum):
    """Avoid Python's equality collision between True/1 and False/0."""

    FALSE = "false"
    TRUE = "true"


class _ResolutionView:
    """Minimal per-level metadata over one shared fitted encoder."""

    def __init__(self, n_buckets, support):
        self.n_buckets_ = n_buckets
        self.support_ = support


def sigmoid(scores):
    """Stable logistic function, including scores whose exponent would overflow."""
    scores = np.asarray(scores, dtype=np.float64)
    result = np.empty_like(scores)
    positive = scores >= 0
    result[positive] = 1.0 / (1.0 + np.exp(-scores[positive]))
    exponent = np.exp(scores[~positive])
    result[~positive] = exponent / (1.0 + exponent)
    return result


def addresses(z, features, codes, table_size):
    """Return compact addresses; ``codes[k]`` belongs to global ``features[k]``.

    Add in int64 before the modulo: compact input code dtypes must not determine
    arithmetic precision. Parameter and feature validation belongs to the API.
    """
    if (
        isinstance(features, (np.ndarray, list, tuple))
        and isinstance(codes, (np.ndarray, list, tuple))
        and len(features)
        and len(codes)
    ):
        total = codes[0][z[:, features[0]]].astype(np.int64, copy=False)
        for feature, code in zip(features[1:], codes[1:]):
            total += code[z[:, feature]].astype(np.int64, copy=False)
    else:
        total = np.zeros(z.shape[0], dtype=np.int64)
        for feature, code in zip(features, codes):
            total += code[z[:, feature]].astype(np.int64, copy=False)
    if table_size > 0 and table_size & table_size - 1 == 0:
        return (total & table_size - 1).astype(np.uint16)
    return (total % table_size).astype(np.uint16)


def predict_coded_memory_buckets(levels, encoders, z_levels, intercept, table_size):
    """Add level memories for already encoded inputs."""
    result = np.full(len(z_levels[0]), intercept, dtype=np.float64)
    for level, encoder, z in zip(levels, encoders, z_levels):
        main_features = level.get("main_features", range(len(level["main_tables"])))
        for feature, values in zip(main_features, level["main_tables"]):
            result += values[z[:, feature]]
        for features, codes, values in zip(level["groups"], level["codes"], level["tables"]):
            index = addresses(z, features, codes, table_size)
            supported = np.ones(len(z), dtype=bool)
            for feature in features:
                supported &= encoder.support_[feature][z[:, feature]]
            result += np.where(supported, values[index], 0.0)
    return result


def decode(value, buffers, memo):
    tag, *rest = value
    if tag == "a":
        dtype, offset, shape = rest
        key = (dtype, offset, tuple(shape))
        if key not in memo:
            length = int(np.prod(shape))
            a = buffers[dtype][offset : offset + length].reshape(shape)
            a.flags.writeable = False
            memo[key] = a
        return memo[key]
    if tag == "p":
        return rest[0]
    if tag == "d":
        return {k: decode(v, buffers, memo) for k, v in rest[0]}
    if tag in ("l", "t"):
        values = [decode(v, buffers, memo) for v in rest[0]]
        return values if tag == "l" else tuple(values)
    if tag == "v":
        result = object.__new__(_ResolutionView)
        result.__dict__.update(decode(rest[0], buffers, memo))
        return result
    raise ValueError("Unsupported artifact tag")


def unpack(wire):
    version, enc, classes, buffers, values, records, table_size, params = wire
    if version != 1 or values.dtype != np.float64:
        raise ValueError("Unsupported artifact schema or coefficient dtype")
    for buffer in [values, *buffers.values()]:
        buffer.flags.writeable = False
    memo = {}
    encoder = object.__new__(BucketEncoder)
    encoder.__dict__.update(decode(enc, buffers, memo))

    def coefficients(ref):
        offset, length = ref
        a = values[offset : offset + length]
        a.flags.writeable = False
        return a

    result = []
    for intercept, levels in records:
        result.append(
            (
                intercept,
                [
                    dict(
                        n_bins=n,
                        main_features=decode(main, buffers, memo),
                        main_tables=[coefficients(a) for a in main_values],
                        groups=[decode(a, buffers, memo) for a in groups],
                        codes=[[decode(a, buffers, memo) for a in group] for group in codes],
                        tables=[coefficients(a) for a in tables],
                    )
                    for n, main, main_values, groups, codes, tables in levels
                ],
            )
        )
    return (encoder, classes, result, table_size, params)


def probabilities(logits):
    p = sigmoid(logits)
    total = p.sum(axis=1, keepdims=True)
    if not np.isfinite(p).all() or np.any(total <= 0):
        raise FloatingPointError("Invalid OVR probability mass; no silent uniform repair")
    return p / total


class BucketEncoder:
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
                f"Feature {feature!r} contains unsupported category type {type(value).__name__}; only strings, finite numbers, booleans and missing values are supported."
            )
        inferred = infer_dtype(values, skipna=True)
        if inferred == "boolean":
            truth = series.to_numpy(dtype=bool, na_value=False)
            values[~missing & truth] = _BooleanKey.TRUE
            values[~missing & ~truth] = _BooleanKey.FALSE
        elif inferred in ("mixed", "mixed-integer"):
            objects = pd.Series(values, copy=False)
            strings = objects.str.fullmatch("(?s).*", na=False).to_numpy(dtype=bool)
            text = objects.astype("string")
            true = text.eq("True").fillna(False).to_numpy(dtype=bool) & ~strings
            false = text.eq("False").fillna(False).to_numpy(dtype=bool) & ~strings
            numeric_kind = infer_dtype(objects[~missing & ~strings & ~true & ~false], skipna=True)
            if numeric_kind not in ("empty", "integer", "floating", "mixed-integer-float"):
                raise TypeError(
                    f"Feature {feature!r} contains unsupported or ambiguous scalar categories."
                )
            values[true], values[false] = (_BooleanKey.TRUE, _BooleanKey.FALSE)
        return (pd.Series(values, dtype=object, copy=False), missing)

    @staticmethod
    def _transform_numeric(values, schema):
        buckets = np.searchsorted(schema["thresholds"], values, side="right").astype(np.uint16)
        buckets[np.isnan(values)] = schema["missing_bucket"]
        return buckets

    @staticmethod
    def _transform_categorical(values, missing, schema):
        mapped = values.map(schema["vocabulary"])
        buckets = mapped.fillna(schema["unknown_bucket"]).to_numpy(dtype=np.uint16)
        if schema["n_rare_categories"]:
            rare = mapped.isna().to_numpy() & values.isin(schema["observed_categories"]).to_numpy()
            buckets[rare] = schema["rare_bucket"]
        buckets[missing] = schema["missing_bucket"]
        return buckets

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
        numeric_array = isinstance(X, np.ndarray) and all(
            (schema["kind"] == "numeric" for schema in self.schemas_)
        )
        for j, schema in enumerate(self.schemas_):
            if numeric_array:
                values = np.array(X[:, j], dtype=np.float64, copy=True)
                if np.isinf(values).any():
                    raise ValueError(
                        f"Input contains infinity in feature {j!r}; infinities are not supported."
                    )
                transformed[:, j] = self._transform_numeric(values, schema)
                continue
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


class NativeImage:
    """Opaque fitted-only image; public estimator/clone/fit API is not replaced."""

    def __init__(self, payload):
        if payload.get("schema") != 1 or payload.get("version") != "1.1.0rc1":
            raise ValueError("Unsupported native inference image")
        self.task = payload["task"]
        if payload["kind"] == "multiclass_wire":
            self.encoder, self.classes_, records, self.table_size, _ = unpack(payload["wire"])
            self.heads = records
        elif payload["kind"] == "single":
            self.encoder = object.__new__(BucketEncoder)
            self.encoder.__dict__.update(payload["encoder"])
            self.table_size = payload["table_size"]
            self.heads = [(payload["intercept"], payload["levels"])]
            if self.task != "regression":
                self.classes_ = payload["classes"]
        else:
            raise ValueError("Unsupported native image kind")
        check_is_fitted(self.encoder, "level_mappings_")
        self.n_features_in_ = self.encoder.n_features_in_

    def decision_function(self, X):
        z = self.encoder.transform_levels(X)
        scores = [
            predict_coded_memory_buckets(
                levels, self.encoder.level_views_, z, intercept, self.table_size
            )
            for intercept, levels in self.heads
        ]
        return np.column_stack(scores) if self.task == "multiclass" else scores[0]

    def predict_proba(self, X):
        if self.task == "regression":
            raise AttributeError("Regression image has no probability output")
        scores = self.decision_function(X)
        if self.task == "multiclass":
            return probabilities(scores)
        positive = sigmoid(scores)
        return np.column_stack((1.0 - positive, positive))

    def predict(self, X):
        if self.task == "regression":
            return self.decision_function(X)
        if self.task == "multiclass":
            return self.classes_[self.predict_proba(X).argmax(1)]
        score = self.decision_function(X)
        return self.classes_[(score > 0.0).astype(np.intp)]


def load_image(folder):
    folder = Path(folder)
    metadata = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    blob = (folder / "model.image.pkl").read_bytes()
    if hashlib.sha256(blob).hexdigest() != metadata["payload_SHA256"]:
        raise ValueError("Native image hash mismatch")
    # Trusted artifacts only. Compression/compilation does not secure pickle.
    return NativeImage(pickle.loads(blob))
