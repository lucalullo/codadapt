"""Frozen native Rational16 kernel; internal implementation, not a public estimator."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class Codes:
    def __init__(self, bins=16, cats=()):
        self.bins = bins
        self.cats = tuple(cats)

    def fit(self, x):
        a = np.asarray(x)
        self.spec = []
        self.sizes = []
        for j in range(a.shape[1]):
            v = a[:, j]
            if j in self.cats:
                counts = pd.Series(v).dropna().value_counts()
                values = counts.index[: self.bins].tolist()
                spec = {v: i + 2 for i, v in enumerate(values)}
                size = len(values) + 2
            else:
                v = np.asarray(v, dtype=float)
                finite = v[np.isfinite(v)]
                spec = (
                    np.unique(np.quantile(finite, np.linspace(0, 1, self.bins + 1)[1:-1]))
                    if len(finite)
                    else np.array([])
                )
                size = len(spec) + 2
            self.spec.append(spec)
            self.sizes.append(size)
        return self

    def transform(self, x):
        a = np.asarray(x)
        z = np.zeros(a.shape, dtype=np.int32)
        for j, spec in enumerate(self.spec):
            if isinstance(spec, dict):
                s = pd.Series(a[:, j])
                z[:, j] = s.map(spec).fillna(1).astype(np.int32)
                z[s.isna().to_numpy(), j] = 0
            else:
                v = np.asarray(a[:, j], dtype=float)
                z[:, j] = np.searchsorted(spec, v, side="right") + 1
                z[~np.isfinite(v), j] = 0
        return z


class Rational:
    def __init__(self, bins=16, ridge=0.001, seed=0, maxiter=100, cats=()):
        self.bins, self.ridge, self.seed = bins, ridge, seed
        self.maxiter, self.cats = maxiter, cats

    @staticmethod
    def objective(theta, z, offsets, target, ridge):
        m = int(offsets[-1])
        num = np.full(len(z), theta[0])
        den = np.ones(len(z))
        for j in range(z.shape[1]):
            idx = offsets[j] + z[:, j]
            num += theta[1 + idx]
            den += theta[1 + m + idx]
        pred = num / den
        res = pred - target
        g = np.zeros_like(theta)
        dn = res / den / len(z)
        dd = -dn * pred
        g[0] = dn.sum()
        for j in range(z.shape[1]):
            lo, hi = offsets[j : j + 2]
            g[1 + lo : 1 + hi] = np.bincount(z[:, j], weights=dn, minlength=hi - lo)
            g[1 + m + lo : 1 + m + hi] = np.bincount(z[:, j], weights=dd, minlength=hi - lo)
        g[1:] += ridge * theta[1:]
        return 0.5 * np.mean(res**2) + 0.5 * ridge * (theta[1:] @ theta[1:]), g

    def fit(self, x, y):
        self.encoder = Codes(self.bins, self.cats).fit(x)
        z = self.encoder.transform(x)
        self.offsets = np.r_[0, np.cumsum(self.encoder.sizes)]
        m = self.offsets[-1]
        self.mean, self.scale = float(np.mean(y)), max(float(np.std(y)), 1e-12)
        target = (np.asarray(y) - self.mean) / self.scale
        theta = np.zeros(1 + 2 * m)
        # Nonzero training-only numerator initializes denominator derivatives.
        for j in range(z.shape[1]):
            lo, hi = self.offsets[j : j + 2]
            sums = np.bincount(z[:, j], weights=target, minlength=hi - lo)
            counts = np.bincount(z[:, j], minlength=hi - lo)
            theta[1 + lo : 1 + hi] = sums / (counts + 5) / z.shape[1]
        self.trace = []

        def callback(v):
            self.trace.append(float(self.objective(v, z, self.offsets, target, self.ridge)[0]))

        result = minimize(
            self.objective,
            theta,
            args=(z, self.offsets, target, self.ridge),
            jac=True,
            method="L-BFGS-B",
            bounds=[(None, None)] * (m + 1) + [(0, 8)] * m,
            options={"maxiter": self.maxiter, "ftol": 1e-9},
            callback=callback,
        )
        self.theta = result.x
        self.converged = bool(result.success)
        self.solver_message = str(result.message)
        return self

    def predict(self, x):
        z = self.encoder.transform(x)
        m = self.offsets[-1]
        num = np.full(len(z), self.theta[0])
        den = np.ones(len(z))
        for j in range(z.shape[1]):
            idx = self.offsets[j] + z[:, j]
            num += self.theta[1 + idx]
            den += self.theta[1 + m + idx]
        return self.mean + self.scale * num / den
