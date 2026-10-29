"""PRIVATE exact ordinary-float64 DataFrame column access, fitted-only.

No learned-state/format change; every bucket and validation remains required.
Other inputs retain the original code, including custom helpers and categories.
"""

import copy
import sys

import numpy as np
import pandas as pd

from . import composed_runtime as parent
from . import portable_native_runtime as native
from . import validated_native_format as framing

check_is_fitted = native.check_is_fitted
_F64 = np.dtype("float64")
_MANAGER = getattr(sys.modules.get("pandas.core.internals.managers"), "BlockManager", None)
_BLOCK = getattr(sys.modules.get("pandas.core.internals.blocks"), "NumpyBlock", None)
_HELPERS = {
    name: getattr(native.BucketEncoder, name)
    for name in [
        "_column",
        "_numeric_values",
        "_check_dtype",
        "_transform_numeric",
        "transform",
        "transform_levels",
    ]
}


def _ordinary_helpers(encoder):
    return not any(name in vars(encoder) for name in _HELPERS) and all(
        getattr(native.BucketEncoder, name) is fn for name, fn in _HELPERS.items()
    )


def _direct_columns(x, encoder):
    if type(x) is not pd.DataFrame or not _ordinary_helpers(encoder):
        return None
    manager = x._mgr
    if _MANAGER is None or type(manager) is not _MANAGER or len(manager.blocks) != 1:
        return None
    block = manager.blocks[0]
    if _BLOCK is None or type(block) is not _BLOCK:
        return None
    values = block.values
    if (
        type(values) is not np.ndarray
        or values.dtype != _F64
        or values.shape != (x.shape[1], x.shape[0])
    ):
        return None
    if not np.array_equal(block.mgr_locs.as_array, np.arange(x.shape[1])):
        return None
    return values


class NumericFrameEncoder(native.BucketEncoder):
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
        direct_columns = _direct_columns(X, self)
        numeric_array = isinstance(X, np.ndarray) and all(
            (schema["kind"] == "numeric" for schema in self.schemas_)
        )
        for j, schema in enumerate(self.schemas_):
            if direct_columns is not None and schema["kind"] == "numeric":
                values = direct_columns[j]
                if np.isinf(values).any():
                    feature = X.columns[j] if self._fit_dataframe_ else j
                    raise ValueError(
                        f"Input contains infinity in feature {feature!r}; infinities are not supported."
                    )
                transformed[:, j] = self._transform_numeric(values, schema)
                continue
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


class ServingModel(parent.ServingModel):
    def __init__(self, image):
        super().__init__(image)
        self._numeric_only = type(image.encoder) is native.BucketEncoder and all(
            s["kind"] == "numeric" for s in image.encoder.schemas_
        )

    def _view(self, x):
        if (
            not self._numeric_only
            or type(x) is not pd.DataFrame
            or type(self.image.encoder) is not native.BucketEncoder
            or not _ordinary_helpers(self.image.encoder)
        ):
            return super()._view(x)
        encoder = object.__new__(NumericFrameEncoder)
        encoder.__dict__.update(vars(self.image.encoder))
        image = copy.copy(self.image)
        image.encoder = encoder
        return image


def load(path):
    return ServingModel(framing.load(path))
