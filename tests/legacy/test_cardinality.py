"""Exact metadata cardinality fast path and unchanged generic fallbacks."""

import numpy as np
import pytest

from codadapt._multiclass import XCache
from codadapt._training import _combination_count


@pytest.mark.parametrize("n", [0, 1, 2, 257, 10000])
@pytest.mark.parametrize("layout", ["C", "F", "strided"])
def test_uint16_distinct_tuple_counts(n, layout):
    z = np.random.default_rng(90).integers(0, 65536, size=(n, 6), dtype=np.uint16)
    if layout == "F":
        z = np.asfortranarray(z)
    elif layout == "strided":
        z = z[::2]
    before = z.tobytes()
    for features in [[0], [0, 1], [1, 0], [1, 1], [0, 2, 4]]:
        assert _combination_count(z, features) == np.unique(z[:, features], axis=0).shape[0]
    assert z.tobytes() == before


@pytest.mark.parametrize(
    "dtype",
    [
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint32,
        np.uint64,
        np.float32,
        np.float64,
        bool,
    ],
)
def test_non_uint16_fallback(dtype):
    z = np.array([[0, 0], [0, 1], [1, 0], [1, 1], [0, 1]], dtype=dtype)
    assert _combination_count(z, [0, 1]) == np.unique(z, axis=0).shape[0]


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_float_nan_infinity_and_signed_zero_fallback(dtype):
    z = np.array([[0, -0.0], [-0.0, 0], [np.nan, 1], [np.nan, 1], [np.inf, -np.inf]], dtype=dtype)
    assert _combination_count(z, [0, 1]) == np.unique(z, axis=0).shape[0]


@pytest.mark.parametrize("dtype", [np.int64, np.uint64])
def test_large_integer_fallback(dtype):
    limit = np.iinfo(dtype)
    z = np.array(
        [[limit.min, limit.max], [limit.max, limit.min], [limit.max, limit.max]], dtype=dtype
    )
    assert _combination_count(z, [0, 1]) == 3


def test_uint16_injective_extremes_and_repetition():
    z = np.array([[0, 0], [0, 65535], [65535, 0], [65535, 65535], [65535, 65535]], dtype=np.uint16)
    assert _combination_count(z, [0, 1]) == 4
    assert _combination_count(np.zeros((100, 2), np.uint16), [0, 1]) == 1


def test_object_axis_behavior_unchanged():
    z = np.array([["a", None], ["b", "c"]], dtype=object)
    with pytest.raises(TypeError):
        np.unique(z, axis=0)
    with pytest.raises(TypeError):
        _combination_count(z, [0, 1])


def test_ovr_count_cache_uses_same_keys():
    cache = XCache(1)
    z = np.array([[0, 1], [2, 3], [0, 1]], dtype=np.uint16)
    assert cache.combination_count(z, [0, 1]) == 2
    assert cache.combination_count(z, [0, 1]) == 2
    assert list(cache.combinations) == [(id(z), (0, 1))]
