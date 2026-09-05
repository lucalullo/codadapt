"""Mathematical and estimator-level contracts for the official coded-memory core."""

import numpy as np
import pytest


def brute_stats(address, h, r, size):
    a, b = np.zeros(size, dtype=np.float64), np.zeros(size, dtype=np.float64)
    for row in range(len(address)):
        cell = int(address[row])
        a[cell] += float(h[row])
        b[cell] += float(h[row]) * float(r[row])
    return a, b


def brute_gain(a, b, l2):
    return sum(0.5 * float(b[cell]) ** 2 / (float(a[cell]) + l2) for cell in range(len(a)))


def brute_move(address, rows, delta, h, r, size):
    shifted = address.copy()
    for row in rows:
        shifted[row] = (int(address[row]) + delta) % size
    return shifted, *brute_stats(shifted, h, r, size)


@pytest.mark.parametrize("seed", range(24))
def test_incremental_matches_full_reaggregation_after_successive_moves(seed):
    from codadapt._core import aggregate, gain, incremental_stats

    rng = np.random.default_rng(seed)
    size, n = (16, 32, 256)[seed % 3], 11 + seed * 3
    address = rng.integers(size // 2, size=n, dtype=np.uint16)
    h, r = rng.lognormal(0, 1.5, n), rng.normal(size=n)
    a, b = aggregate(address, h, r, size)
    np.testing.assert_allclose((a, b), brute_stats(address, h, r, size), rtol=1e-14)
    for delta in [0, 1, size - 1, size // 2, 3, size + 2]:
        rows = np.flatnonzero(rng.random(n) < 0.45)
        d, e = aggregate(address[rows], h[rows], r[rows], size)
        new_a, new_b = incremental_stats(a, b, d, e, delta)
        moved, expected_a, expected_b = brute_move(address, rows, delta, h, r, size)
        np.testing.assert_allclose(new_a, expected_a, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(new_b, expected_b, rtol=1e-12, atol=1e-12)
        assert gain(new_a, new_b, 2.5) == pytest.approx(
            brute_gain(expected_a, expected_b, 2.5), rel=1e-12, abs=1e-12
        )
        address, a, b = moved, new_a, new_b


def test_incremental_is_nonmutating_and_rejects_significant_negative_mass():
    from codadapt._core import incremental_stats

    a, b, d, e = (np.array(x, dtype=float) for x in ([1, 0], [2, 0], [1 + 1e-15, 0], [2, 0]))
    snapshots = [x.copy() for x in (a, b, d, e)]
    new_a, _ = incremental_stats(a, b, d, e, 1)
    assert new_a[0] == 0
    for original, snapshot in zip((a, b, d, e), snapshots):
        np.testing.assert_array_equal(original, snapshot)
    with pytest.raises(FloatingPointError, match="negative"):
        incremental_stats(a, b, d + [1e-4, 0], e, 1)


@pytest.mark.parametrize("seed", range(12))
def test_logistic_majorant_and_closed_form_block_do_not_increase_surrogate(seed):
    from codadapt._core import aggregate, sigmoid

    rng, size, n = np.random.default_rng(seed), 16, 90
    address = rng.integers(size, size=n, dtype=np.uint16)
    old_v, q = rng.normal(size=size), rng.normal(size=n) * 3
    y, weights, l2 = rng.integers(2, size=n), rng.lognormal(size=n), 2.0
    old_f = q + old_v[address]
    displacement = rng.normal(size=n) * 9
    old_loss = np.logaddexp(0, old_f) - y * old_f
    actual = np.logaddexp(0, old_f + displacement) - y * (old_f + displacement)
    majorant = old_loss + (sigmoid(old_f) - y) * displacement + displacement**2 / 8
    assert np.all(actual <= majorant + 1e-12)
    h = weights / 4
    response = old_v[address] + 4 * (y - sigmoid(old_f))
    a, b = aggregate(address, h, response, size)
    new_v = b / (a + l2)
    old_surrogate = 0.5 * np.sum(h * (response - old_v[address]) ** 2) + l2 / 2 * (old_v @ old_v)
    new_surrogate = 0.5 * np.sum(h * (response - new_v[address]) ** 2) + l2 / 2 * (new_v @ new_v)
    assert new_surrogate <= old_surrogate + 1e-10 * max(1, abs(old_surrogate))


@pytest.mark.parametrize("seed", range(8))
def test_regression_block_is_exact_regularized_quadratic_optimum(seed):
    from codadapt._core import aggregate, gain

    rng, size, n, l2 = np.random.default_rng(seed), 16, 31, 1.5
    address = rng.integers(8, size=n, dtype=np.uint16)
    h, residual = rng.uniform(0.2, 3, n), rng.normal(size=n)
    a, b = aggregate(address, h, residual, size)
    values = b / (a + l2)
    optimum = 0.5 * np.sum(h * (residual - values[address]) ** 2) + l2 / 2 * (values @ values)
    assert optimum == pytest.approx(
        0.5 * np.sum(h * residual**2) - gain(a, b, l2), rel=1e-13, abs=1e-13
    )
    np.testing.assert_allclose((a + l2) * values - b, 0, atol=1e-13)
    assert np.all(values[a == 0] == 0)


@pytest.mark.parametrize("binary", [False, True])
@pytest.mark.parametrize("seed", [2, 7, 19])
def test_full_coded_memory_passes_do_not_increase_regularized_objective(binary, seed):
    from codadapt import CodAdaptClassifier, CodAdaptRegressor

    rng = np.random.default_rng(seed)
    x = rng.normal(size=(180, 4))
    latent = 2 * x[:, 0] - 1.5 * x[:, 1] * x[:, 2] + rng.normal(size=len(x)) * 0.2
    y = (latent > 0).astype(int) if binary else latent
    weights = rng.uniform(0.1, 3, len(x))
    weights[::13] = 0
    cls = CodAdaptClassifier if binary else CodAdaptRegressor
    model = cls(
        n_bins=8,
        n_tables=3,
        features_per_table=3,
        table_size=32,
        early_stopping=False,
        random_state=seed,
    ).fit(x, y, sample_weight=weights)
    objectives = np.array([row["objective"] for row in model.training_history_])
    assert np.all(np.diff(objectives) <= 1e-10 * np.maximum(1, np.abs(objectives[:-1])))
    raw = model.decision_function(x) if binary else model.predict(x)
    data_term = (
        weights @ (np.logaddexp(0, raw) - y * raw) if binary else 0.5 * (weights @ (y - raw) ** 2)
    )
    penalty = 0.5 * model.l2 * sum(v @ v for v in model.main_tables_ + model.tables_)
    assert data_term + penalty == pytest.approx(objectives[-1], rel=1e-12, abs=1e-10)
    assert model.n_iter_ == len(model.training_history_) <= 3
    assert all(row["coordinates_examined"] == 0 for row in model.training_history_)


@pytest.mark.parametrize("binary", [False, True])
def test_default_core_has_no_legacy_trainer_dispatch(binary):
    from codadapt import CodAdaptClassifier, CodAdaptRegressor, _training

    rng = np.random.default_rng(13)
    x = rng.normal(size=(120, 3))
    y = (x[:, 0] * x[:, 1] > 0).astype(int) if binary else x[:, 0] * x[:, 1]
    cls = CodAdaptClassifier if binary else CodAdaptRegressor
    model = cls(early_stopping=False, random_state=41).fit(x, y)
    assert hasattr(_training, "train_coded_memory")
    assert not hasattr(_training, "train")
    assert model.n_iter_ == len(model.levels_) <= 3
