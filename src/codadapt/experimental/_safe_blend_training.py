"""Four finite non-tree function dictionaries; inference requires NumPy only.

No teacher topology, path, leaf, node ID or prediction object is retained.
"""

import numpy as np


def as_array(x):
    return np.asarray(x, dtype=np.float64)


def pooled_boundaries(teacher, x, cats):
    """Offline extraction: retain feature/threshold frequency, discard topology."""
    pools = [{} for _ in range(x.shape[1])]
    stack = [t["tree_structure"] for t in teacher.booster_.dump_model()["tree_info"]]
    while stack:
        node = stack.pop()
        if "split_feature" not in node:
            continue
        j = node["split_feature"]
        if j not in cats and node["decision_type"] == "<=":
            cut = float(node["threshold"])
            pools[j][cut] = pools[j].get(cut, 0) + 1
        stack.extend([node["left_child"], node["right_child"]])
    return [np.array(sorted(pool), dtype=float) for pool in pools]


class Scale:
    def __init__(self, x, cats):
        a = as_array(x)
        self.spec = []
        for j in range(a.shape[1]):
            v = a[:, j]
            good = v[np.isfinite(v)]
            if j in cats:
                vals, counts = np.unique(good, return_counts=True)
                vals = vals[np.argsort(-counts, kind="stable")[:32]]
                self.spec.append(("cat", vals))
            else:
                center = float(np.median(good)) if good.size else 0.0
                spread = float(np.subtract(*np.quantile(good, [0.75, 0.25]))) if good.size else 1.0
                self.spec.append(("num", center, max(spread, 1e-8)))

    def transform(self, x):
        a = as_array(x)
        columns = []
        for j, spec in enumerate(self.spec):
            v = a[:, j]
            good = np.isfinite(v)
            if spec[0] == "cat":
                columns.extend((v == value).astype(float) for value in spec[1])
                columns.append((good & ~np.isin(v, spec[1])).astype(float))
            else:
                columns.append(np.where(good, np.clip((v - spec[1]) / spec[2], -4, 4), 0.0))
            columns.append((~good).astype(float))
        return np.column_stack(columns)


class Dictionary:
    def __init__(self, kind, capacity, x, cats, boundaries, seed):
        self.kind = kind
        self.capacity = capacity
        self.cats = tuple(cats)
        rng = np.random.default_rng(seed + 740810)
        a = as_array(x)
        self.features = a.shape[1]
        if kind in ("RBF", "RFF"):
            self.scale = Scale(x, cats)
            ix = rng.choice(len(a), min(2048, len(a)), replace=False)
            u = self.scale.transform(a[ix])
            dif = u[rng.integers(len(u), size=256)] - u[rng.integers(len(u), size=256)]
            self.distance_scale = max(float(np.median(np.sum(dif * dif, axis=1))), 1e-8)
            if kind == "RBF":
                self.centers = self.scale.transform(
                    a[rng.choice(len(a), min(capacity, len(a)), replace=False)]
                )
            else:
                self.omega = rng.normal(size=(u.shape[1], capacity)) / np.sqrt(self.distance_scale)
                self.phase = rng.uniform(0, 2 * np.pi, size=capacity)
            return
        per_feature = []
        for j in range(a.shape[1]):
            v = a[:, j]
            good = v[np.isfinite(v)]
            atoms = [("missing", j, 0.0, 0.0, 0.0)]
            if j in cats:
                vals, counts = np.unique(good, return_counts=True)
                atoms += [
                    ("eq", j, float(v), 0.0, 0.0)
                    for v in vals[np.argsort(-counts, kind="stable")[:32]]
                ]
            else:
                cuts = boundaries[j]
                if len(cuts) > 32:
                    cuts = cuts[np.unique(np.linspace(0, len(cuts) - 1, 32).astype(int))]
                if not len(cuts) and len(good):
                    cuts = np.unique(np.quantile(good, [0.25, 0.5, 0.75]))
                if kind == "HAT" and len(good):
                    center = float(np.median(good))
                    scale = max(float(np.subtract(*np.quantile(good, [0.75, 0.25]))), 1e-8)
                    atoms.append(("linear", j, center, scale, 0.0))
                for i, cut in enumerate(cuts):
                    if kind == "SBD":
                        atoms.append(("le", j, float(cut), 0.0, 0.0))
                    else:
                        low = cuts[i - 1] if i else (np.min(good) if len(good) else cut - 1)
                        high = (
                            cuts[i + 1]
                            if i + 1 < len(cuts)
                            else (np.max(good) if len(good) else cut + 1)
                        )
                        atoms.append(
                            (
                                "hat",
                                j,
                                float(cut),
                                max(float(cut - low), 1e-8),
                                max(float(high - cut), 1e-8),
                            )
                        )
            per_feature.append(atoms)
        primitives = []
        for depth in range(max(map(len, per_feature))):
            for atoms in per_feature:
                if depth < len(atoms) and len(primitives) < capacity // 2:
                    primitives.append(atoms[depth])
        self.primitives = primitives
        self.terms = []
        by_feature = {
            j: [i for i, s in enumerate(primitives) if s[1] == j and s[0] != "missing"]
            for j in range(a.shape[1])
        }
        available = [j for j, ids in by_feature.items() if ids]
        if len(available) >= 2:
            seen = set()
            for _ in range(capacity * 20):
                degree = min(int(rng.integers(2, 5)), len(available))
                js = rng.choice(available, degree, replace=False)
                ids = sorted(int(rng.choice(by_feature[j])) for j in js)
                signs = tuple(bool(rng.integers(2)) if kind == "SBD" else False for _ in ids)
                signature = (tuple(ids), signs)
                if signature not in seen:
                    seen.add(signature)
                    self.terms.append(signature)
                if len(self.terms) >= capacity - len(primitives):
                    break

    def transform(self, x):
        a = as_array(x)
        if self.kind in ("RBF", "RFF"):
            u = self.scale.transform(a)
            if self.kind == "RFF":
                return np.cos(u @ self.omega + self.phase)
            squared = (
                np.sum(u * u, axis=1)[:, None]
                + np.sum(self.centers * self.centers, axis=1)[None, :]
                - 2 * (u @ self.centers.T)
            )
            return np.exp(-np.maximum(squared, 0) / self.distance_scale)
        primitive = np.empty((len(a), len(self.primitives)))
        for i, (kind, j, c, left_width, right_width) in enumerate(self.primitives):
            v = a[:, j]
            good = np.isfinite(v)
            if kind == "missing":
                z = ~good
            elif kind == "eq":
                z = v == c
            elif kind == "le":
                z = good & (v <= c)
            elif kind == "linear":
                z = np.where(good, np.clip((v - c) / left_width, -4, 4), 0.0)
            else:
                z = np.where(
                    good,
                    np.maximum(
                        0.0, 1 - np.where(v < c, (c - v) / left_width, (v - c) / right_width)
                    ),
                    0.0,
                )
            primitive[:, i] = z
        result = np.empty((len(a), len(self.primitives) + len(self.terms)))
        result[:, : len(self.primitives)] = primitive
        for k, (ids, signs) in enumerate(self.terms, start=len(self.primitives)):
            value = np.ones(len(a))
            for i, negative in zip(ids, signs):
                value *= 1 - primitive[:, i] if negative else primitive[:, i]
            result[:, k] = value
        return result


class Compiled:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def fit(self, x, y):
        from scipy.linalg import cho_factor, cho_solve

        n = len(y)
        gram = total = rhs = None
        mean_y = float(np.mean(y))
        for lo in range(0, n, 2048):
            a = self.dictionary.transform(np.asarray(x)[lo : lo + 2048])
            if gram is None:
                gram = np.zeros((a.shape[1], a.shape[1]))
                total = np.zeros(a.shape[1])
                rhs = np.zeros(a.shape[1])
            gram += a.T @ a
            total += a.sum(axis=0)
            rhs += a.T @ (y[lo : lo + 2048] - mean_y)
        mean = total / n
        gram /= n
        gram -= np.outer(mean, mean)
        sd = np.sqrt(np.maximum(np.diag(gram), 0.0001))
        gram /= np.outer(sd, sd)
        gram.flat[:: len(gram) + 1] += 0.0001
        rhs /= n * sd
        self.coef = (
            cho_solve(cho_factor(gram, lower=True, check_finite=False), rhs, check_finite=False)
            / sd
        )
        self.intercept = mean_y - float(mean @ self.coef)
        return self

    def predict(self, x):
        a = as_array(x)
        prediction = np.empty(len(a))
        for lo in range(0, len(a), 2048):
            prediction[lo : lo + 2048] = (
                self.intercept + self.dictionary.transform(a[lo : lo + 2048]) @ self.coef
            )
        return prediction
