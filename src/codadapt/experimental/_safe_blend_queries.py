"""Queries depend on training rows and teacher feedback only, never heldout X."""

import time

import numpy as np

from ._safe_blend_training import Compiled


def perturb(anchors, train, cats, boundaries, rng, boundary):
    out = np.asarray(anchors, dtype=float).copy()
    a = np.asarray(train, dtype=float)
    numeric = [j for j in range(a.shape[1]) if j not in cats and np.isfinite(a[:, j]).any()]
    if not numeric:
        return out
    feature = rng.choice(numeric, size=len(out))
    for j in numeric:
        selected = np.flatnonzero((feature == j) & np.isfinite(out[:, j]))
        if not len(selected):
            continue
        finite = a[np.isfinite(a[:, j]), j]
        low, high = np.min(finite), np.max(finite)
        width = float(np.subtract(*np.quantile(finite, [0.75, 0.25])))
        v = out[selected, j]
        changed = np.clip(v + rng.uniform(-0.1, 0.1, len(v)) * width, low, high)
        cuts = boundaries[j]
        cuts = cuts[(cuts >= low) & (cuts <= high)]
        if boundary and len(cuts):
            ix = np.searchsorted(cuts, v)
            left = cuts[np.clip(ix - 1, 0, len(cuts) - 1)]
            right = cuts[np.clip(ix, 0, len(cuts) - 1)]
            nearest = np.where(np.abs(left - v) < np.abs(right - v), left, right)
            admissible = np.abs(nearest - v) <= 0.1 * (high - low)
            side = np.where(rng.integers(2, size=len(v)), np.inf, -np.inf)
            changed = np.where(admissible, np.clip(np.nextafter(nearest, side), low, high), changed)
        out[selected, j] = changed
    return out


def make_queries(strategy, budget, x, cats, boundaries, seed, teacher_predict, dictionary):
    rng = np.random.default_rng(seed + 740811)
    a = np.asarray(x, dtype=float)
    observed_ids = np.resize(rng.permutation(len(a)), budget)
    observed = a[observed_ids]
    query_s = 0.0

    def query(z):
        nonlocal query_s
        start = time.perf_counter()
        values = teacher_predict(z)
        query_s += time.perf_counter() - start
        return values

    pilot_s = 0.0
    if strategy == "observed":
        q = observed
        y = query(q)
    elif strategy == "bootstrap":
        q = a[rng.integers(len(a), size=budget)]
        y = query(q)
    elif strategy == "jitter":
        half = budget // 2
        q = np.concatenate(
            [observed[:half], perturb(observed[half:], a, cats, boundaries, rng, False)]
        )
        y = query(q)
    elif strategy == "active":
        half, quarter = budget // 2, budget // 4
        first = observed[:half]
        y1 = query(first)
        start = time.perf_counter()
        pilot = Compiled(dictionary).fit(first, y1)
        pilot_s = time.perf_counter() - start
        second = perturb(observed[half : half + quarter], a, cats, boundaries, rng, True)
        y2 = query(second)
        residual = np.abs(y2 - pilot.predict(second))
        hard = np.argsort(residual, kind="stable")[-max(1, len(second) // 4) :]
        anchors = second[rng.choice(hard, size=budget - half - quarter, replace=True)]
        third = perturb(anchors, a, cats, boundaries, rng, True)
        y3 = query(third)
        q = np.concatenate([first, second, third])
        y = np.concatenate([y1, y2, y3])
    else:
        raise ValueError(strategy)
    assert len(q) == budget and np.isfinite(y).all()
    return (
        q,
        y,
        dict(
            teacher_query_s=query_s,
            pilot_fit_s=pilot_s,
            nominal_teacher_queries=budget,
            unique_query_rows=len(np.unique(q, axis=0)),
            query_strategy=strategy,
        ),
    )
