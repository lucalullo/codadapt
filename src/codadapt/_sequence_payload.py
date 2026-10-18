"""Bound standard finite array-like metadata without invoking conversion hooks."""

import sys

import numpy as np
import pandas as pd

MAX_SCALAR_VISITS = 20_000_000


def sequence_payload(value):
    """Conservative live-container plus conversion-payload allowance; no copy."""
    if isinstance(value, pd.Index):
        # RangeIndex can be tiny while np.asarray materializes N integer cells.
        return int(value.memory_usage(deep=True)) + len(value) * max(
            16, getattr(value.dtype, "itemsize", 16)
        )
    if type(value) is range:
        count = len(value)
        if count > MAX_SCALAR_VISITS:
            raise ValueError("AUTO sequence profile exceeds bounded scalar visits")
        if count and max(value.start.bit_length(), value.stop.bit_length()) > 1024:
            raise ValueError("AUTO cannot bound oversized integer sequence conversion")
        return sys.getsizeof(value) + count * 16
    if type(value) not in (list, tuple):
        raise ValueError("AUTO cannot bound opaque array-like conversion without invoking it")
    count = len(value)
    nested = count > 0 and type(value[0]) in (list, tuple)
    width = len(value[0]) if nested else 1
    if max(count, count * width) > MAX_SCALAR_VISITS:
        raise ValueError("AUTO sequence profile exceeds bounded scalar visits")
    retained = sys.getsizeof(value)
    text_width = 0
    nontext = False
    numeric_text_width = 128

    def scalar(item):
        nonlocal retained, text_width, nontext, numeric_text_width
        kind = type(item)
        if kind in (str, bytes):
            text_width = max(text_width, len(item), 1)
        elif kind in (bool, int, float, complex) or item is None:
            if kind is int and item.bit_length() > 1024:
                raise ValueError("AUTO cannot bound oversized integer sequence conversion")
            if kind is int:
                numeric_text_width = max(numeric_text_width, item.bit_length() + 3)
            nontext = True
        elif isinstance(item, np.generic) and kind.__module__ == "numpy":
            if item.dtype.kind in "US":
                text_width = max(text_width, len(item), 1)
            elif item.dtype.kind in "biufc" and item.dtype.itemsize <= 16:
                nontext = True
            else:
                raise ValueError("AUTO sequence scalar dtype is not bounded")
        else:
            raise ValueError("AUTO sequence contains nested, cyclic or opaque scalar")
        # Count repeated objects repeatedly: conservative, no O(N) identity set.
        retained += sys.getsizeof(item)

    if nested:
        for row in value:
            if row is value or type(row) not in (list, tuple) or len(row) != width:
                raise ValueError("AUTO sequence must be a noncyclic rectangular 2D input")
            retained += sys.getsizeof(row)
            for item in row:
                scalar(item)
    else:
        for item in value:
            scalar(item)
    cell_bytes = 16
    if text_width:
        # Mixed numeric/text promotion uses uniform Unicode width. A sum of
        # individual string sizes alone would underestimate long-label arrays.
        cell_bytes = max(16, 4 * max(text_width, numeric_text_width if nontext else 1))
    return retained + count * width * cell_bytes
