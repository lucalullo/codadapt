"""Vectorized addressing and exact incremental sufficient statistics.

The candidate loop only touches arrays of length ``table_size``. Row indices
are grouped once by training; each visited coordinate aggregates its rows once.
"""

import numpy as np

GAIN_RTOL = 1e-12
_CANCELLATION_RTOL = 64 * np.finfo(np.float64).eps


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
    total = np.zeros(z.shape[0], dtype=np.int64)
    for feature, code in zip(features, codes):
        total += code[z[:, feature]].astype(np.int64, copy=False)
    return (total % table_size).astype(np.uint16)


def aggregate(address, h, r, table_size):
    """Aggregate mass A and weighted response B in float64 for one addressing."""
    h, r = np.asarray(h, dtype=np.float64), np.asarray(r, dtype=np.float64)
    a = np.bincount(address, weights=h, minlength=table_size)
    b = np.bincount(address, weights=h * r, minlength=table_size)
    return a, b


def gain(a, b, l2):
    """The maximized regularized quadratic improvement, not exact logistic gain."""
    result = 0.5 * np.dot(b, b / (a + l2))
    if not np.isfinite(result):
        raise FloatingPointError("Non-finite quadratic gain; rescale target or sample_weight.")
    return float(result)


def incremental_stats(a, b, d, e, delta):
    """Move a group's statistics forward by delta cells, without mutating input.

    D/E refer to the current addresses of the group. Negative residual mass is
    clipped only within 64 machine epsilons of the per-cell arithmetic scale;
    larger negative mass signals a broken invariant and raises an exception.
    Zero-mass cancellation in B is corrected only at the same relative scale.
    """
    a, b, d, e = (np.asarray(value, dtype=np.float64) for value in (a, b, d, e))
    remaining_a, remaining_b = a - d, b - e
    mass_tolerance = _CANCELLATION_RTOL * np.maximum(1.0, np.maximum(np.abs(a), np.abs(d)))
    if np.any(remaining_a < -mass_tolerance):
        raise FloatingPointError("Significant negative mass in incremental statistics.")
    remaining_a[remaining_a < 0] = 0.0
    response_tolerance = _CANCELLATION_RTOL * np.maximum(1.0, np.maximum(np.abs(b), np.abs(e)))
    cancelled = (remaining_a == 0) & (np.abs(remaining_b) <= response_tolerance)
    remaining_b[cancelled] = 0.0
    shift = int(delta) % len(a)
    return remaining_a + np.roll(d, shift), remaining_b + np.roll(e, shift)
