"""Standalone ordered NumPy lookup runtime. No teacher imports or retained teacher."""

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.utils.validation import check_is_fitted


class _Runtime:
    def __init__(self, columns, intercept, specs, numeric_unknown):
        self.columns = tuple(columns)
        self.intercept = intercept
        self.cache = {}
        self.numeric_unknown = np.array(numeric_unknown, dtype=float)
        numeric = [(e, v) for num, e, v in specs if num]
        self.edge_buffer = np.concatenate([e for e, _ in numeric]) if numeric else np.empty(0)
        self.value_buffer = np.concatenate([v for _, v in numeric]) if numeric else np.empty(0)
        self.specs = []
        ec = vc = 0
        for num, edges, values in specs:
            if num:
                edges = self.edge_buffer[ec : ec + len(edges)]
                values = self.value_buffer[vc : vc + len(values)]
                ec += len(edges)
                vc += len(values)
            self.specs.append((num, edges, values))

    def __getstate__(self):
        state = self.__dict__.copy()
        state["cache"] = {}
        state["specs"] = [
            (True, len(e), len(v)) if num else (False, e, v) for num, e, v in self.specs
        ]
        return state

    def __setstate__(self, state):
        specs = state.pop("specs")
        self.__dict__.update(state)
        self.specs = []
        ec = vc = 0
        for num, edges, values in specs:
            if num:
                self.specs.append(
                    (True, self.edge_buffer[ec : ec + edges], self.value_buffer[vc : vc + values])
                )
                ec += edges
                vc += values
            else:
                self.specs.append((False, edges, values))

    def _categorical(self, j, col, keys, values):
        if isinstance(col.dtype, pd.CategoricalDtype):
            levels = col.cat.categories
            cached = self.cache.get(j)
            if cached is None or cached[0] is not levels:
                idx = keys.get_indexer(levels)
                idx[idx < 0] = len(keys)
                aligned = np.r_[values[idx], values[-1]]
                self.cache[j] = (levels, aligned)
            else:
                aligned = cached[1]
            return aligned[col.cat.codes.to_numpy()]
        codes, levels = pd.factorize(col, sort=False)
        idx = keys.get_indexer(levels)
        idx[idx < 0] = len(keys)
        return np.r_[values[idx], values[-1]][codes]

    def raw(self, x):
        # Fixed policy: small C-order blocks; otherwise ordered feature loop.
        n = len(x)
        out = np.full(n, self.intercept)
        numeric = x.to_numpy(copy=False) if all(s[0] for s in self.specs) else None
        mask = np.empty(n, bool)
        width = min(16, len(self.specs))
        buffer = np.empty((width + 1, n), order="C") if n <= 32 else None
        used = 0
        for j, (num, edges, values) in enumerate(self.specs):
            if num:
                a = (
                    np.asarray(numeric[:, j], float)
                    if numeric is not None
                    else x[self.columns[j]].to_numpy(dtype=float, na_value=np.nan)
                )
                a = np.ascontiguousarray(a)
                idx = np.searchsorted(edges, a, side="right")
                np.isnan(a, out=mask)
                np.copyto(idx, len(values) - 1, where=mask)
                v = values[idx]
            else:
                v = self._categorical(j, x[self.columns[j]], edges, values)
            if buffer is None:
                np.add(out, v, out=out)
            else:
                if used == 0:
                    buffer[0] = out
                used += 1
                buffer[used] = v
                if used == width or j == len(self.specs) - 1:
                    np.add.accumulate(buffer[: used + 1], axis=0, out=buffer[: used + 1])
                    out[:] = buffer[used]
                    used = 0
        return out


def _frame(x, columns, specs):
    if not isinstance(x, pd.DataFrame) or not x.columns.is_unique:
        raise ValueError("Expected a DataFrame with unique string feature names.")
    if len(x.columns) != len(columns) or set(x.columns) != set(columns):
        raise ValueError("Feature schema must exactly match the compiled model.")
    if tuple(x.columns) != tuple(columns):
        x = x.loc[:, list(columns)]
    converted = False
    for j, (num, _, _) in enumerate(specs):
        col = x.iloc[:, j]
        if num:
            if (
                not pd.api.types.is_numeric_dtype(col.dtype)
                or pd.api.types.is_complex_dtype(col.dtype)
                or pd.api.types.is_bool_dtype(col.dtype)
            ):
                raise ValueError(f"Numeric feature {columns[j]!r} needs real numeric dtype.")
            if isinstance(col.dtype, pd.api.extensions.ExtensionDtype):
                if not converted:
                    x = x.copy()
                    converted = True
                x[columns[j]] = col.to_numpy(dtype=float, na_value=np.nan)
        else:
            levels = (
                col.cat.categories
                if isinstance(col.dtype, pd.CategoricalDtype)
                else pd.unique(col.dropna())
            )
            if any(not isinstance(v, str) for v in levels):
                raise ValueError(f"Categorical feature {columns[j]!r} supports string labels only.")
    return x


class _CompiledBase(BaseEstimator):
    def fit(self, X, y=None):
        """Compiled estimators cannot be trained; use compile_ebm with a fitted teacher."""
        raise TypeError(
            "Compiled estimators are not trainable; use compile_ebm(teacher, X_verify=...)."
        )

    def _raw(self, x):
        check_is_fitted(self, "_runtime_")
        return self._runtime_.raw(_frame(x, self.feature_names_in_, self._runtime_.specs))


class CompiledEBMClassifier(ClassifierMixin, _CompiledBase):
    """Experimental compiler-produced binary classifier; not a trainable learner."""

    def decision_function(self, X):
        """Return verified exact raw logits in the teacher's class order."""
        return self._raw(X)

    def predict_proba(self, X):
        """Return numerically equivalent probabilities, not bitwise teacher probabilities."""
        p = expit(self.decision_function(X))
        return np.column_stack((1 - p, p))

    def predict(self, X):
        """Return original labels by probability argmax; ties select classes_[0]."""
        probabilities = self.predict_proba(X)
        return self.classes_[np.argmax(probabilities, axis=1)]


class CompiledEBMRegressor(RegressorMixin, _CompiledBase):
    """Experimental compiler-produced single-target regressor; not trainable."""

    def predict(self, X):
        """Return verified exact regression predictions."""
        return self._raw(X)
