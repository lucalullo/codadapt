"""Addressing is integer addition modulo M, independent of Python hashing."""

import numpy as np
import pytest


def brute_addresses(z, features, codes, size):
    return np.array(
        [
            sum(int(codes[k][z[row, feature]]) for k, feature in enumerate(features)) % size
            for row in range(len(z))
        ],
        dtype=np.uint16,
    )


@pytest.mark.parametrize("size", [16, 256, 4096])
@pytest.mark.parametrize("seed", range(8))
def test_addresses_match_wide_integer_reference(size, seed):
    from codadapt._core import addresses

    rng = np.random.default_rng(seed)
    z = rng.integers(6, size=(90, 35), dtype=np.uint16)
    features = rng.choice(35, size=33, replace=False)
    codes = [rng.integers(size, size=6, dtype=np.uint16) for _ in features]
    result = addresses(z, features, codes, size)
    np.testing.assert_array_equal(result, brute_addresses(z, features, codes, size))
    assert result.dtype == np.uint16
    assert result.min() >= 0 and result.max() < size


def test_address_sum_uses_wide_accumulator_and_input_is_unchanged():
    from codadapt._core import addresses

    z = np.zeros((2, 40), dtype=np.uint16)
    codes = [np.array([4095], dtype=np.uint16) for _ in range(40)]
    result = addresses(z, np.arange(40), codes, 4096)
    np.testing.assert_array_equal(result, [(4095 * 40) % 4096] * 2)
    np.testing.assert_array_equal(z, np.zeros_like(z))
    assert all(code[0] == 4095 for code in codes)


def test_sigmoid_is_stable_at_extreme_scores():
    from codadapt._core import sigmoid

    with np.errstate(over="raise", invalid="raise"):
        result = sigmoid(np.array([-1000, -100, -1, 0, 1, 100, 1000], dtype=float))
    assert np.all(np.isfinite(result))
    assert result[0] == 0 and result[-1] == 1 and result[3] == 0.5
    np.testing.assert_allclose(result, 1 - result[::-1], atol=1e-15)
