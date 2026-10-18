"""Bounded trusted payload prechecks; never invoke opaque metadata hooks."""

import numpy as np
import pandas as pd

MAX_OBJECT_VISITS = 20_000_000
SCALARS = {str, bytes, int, float, bool, complex, type(None)}
SCALARS.update(
    np.dtype(code).type
    for code in [
        "?",
        "i1",
        "i2",
        "i4",
        "i8",
        "u1",
        "u2",
        "u4",
        "u8",
        "f2",
        "f4",
        "f8",
        "c8",
        "c16",
        "U",
        "S",
    ]
)
SHADOWS = {"memory_usage", "items", "to_numpy", "__array__", "_constructor_sliced", "_values"}
INDEX_TYPES = {
    pd.Index,
    pd.RangeIndex,
    pd.CategoricalIndex,
    pd.DatetimeIndex,
    pd.TimedeltaIndex,
    pd.PeriodIndex,
    pd.MultiIndex,
}
ARRAY_TYPES = {
    getattr(pd.arrays, name)
    for name in [
        "IntegerArray",
        "FloatingArray",
        "BooleanArray",
        "StringArray",
        "Categorical",
        "DatetimeArray",
        "TimedeltaArray",
        "PeriodArray",
    ]
    if hasattr(pd.arrays, name)
}
ARROW_TYPES = {
    getattr(pd.arrays, name)
    for name in ["ArrowStringArray", "ArrowExtensionArray"]
    if hasattr(pd.arrays, name)
}


def ensure_trusted(value):
    """Validate object scalars before existing deep-size operations, streaming."""
    visits = 0

    def scan(array):
        nonlocal visits
        if type(array) is not np.ndarray:
            raise ValueError("AUTO opaque array metadata is unqualified")
        if not array.dtype.hasobject:
            return
        visits += array.size
        if visits > MAX_OBJECT_VISITS:
            raise ValueError("AUTO trusted-object profile exceeds bounded visits")
        for item in array.flat:
            if type(item) not in SCALARS and item is not pd.NA and item is not pd.NaT:
                raise ValueError("AUTO opaque scalar metadata is unqualified")

    def array_data(array):
        kind = type(array)
        if kind is np.ndarray:
            scan(array)
        elif kind in ARROW_TYPES:
            # Native Arrow buffers contain no arbitrary Python object scalars.
            return
        elif kind in ARRAY_TYPES:
            if kind is pd.Categorical:
                index_data(array.categories)
            elif hasattr(array, "_ndarray"):
                scan(array._ndarray)
            elif hasattr(array, "_data") and type(array._data) is np.ndarray:
                scan(array._data)
            else:
                raise ValueError("AUTO extension payload metadata is unqualified")
        else:
            raise ValueError("AUTO custom extension metadata is unqualified")

    def index_data(index):
        kind = type(index)
        if kind not in INDEX_TYPES or SHADOWS.intersection(vars(index)):
            raise ValueError("AUTO opaque Index metadata is unqualified")
        if kind is pd.RangeIndex:
            return
        if kind is pd.MultiIndex:
            for level in index.levels:
                index_data(level)
            return
        array_data(index._values)

    kind = type(value)
    if kind is np.ndarray:
        scan(value)
    elif kind is pd.DataFrame:
        if SHADOWS.intersection(vars(value)):
            raise ValueError("AUTO overridden DataFrame metadata is unqualified")
        index_data(value.index)
        for _, series in pd.DataFrame.items(value):
            if type(series) is not pd.Series or SHADOWS.intersection(vars(series)):
                raise ValueError("AUTO custom column metadata is unqualified")
            array_data(series._values)
    elif kind is pd.Series:
        if SHADOWS.intersection(vars(value)):
            raise ValueError("AUTO overridden Series metadata is unqualified")
        index_data(value.index)
        array_data(value._values)
    elif kind in INDEX_TYPES:
        index_data(value)
    elif kind in (list, tuple, range):
        # Existing bounded sequence helper validates its own scalar types.
        return
    else:
        raise ValueError("AUTO opaque array-like metadata is unqualified")
