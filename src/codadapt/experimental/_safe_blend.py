"""Experimental regression estimator with the frozen safe-blend fitting recipe."""

import json
import numbers
import time
from importlib.resources import files

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import train_test_split
from sklearn.utils.validation import check_is_fitted
from threadpoolctl import threadpool_limits

from ._safe_blend_artifact import ALPHA, SafeBlendArtifact

RECIPE = json.loads(
    files("codadapt.experimental").joinpath("_safe_blend_recipe.json").read_text(encoding="utf-8")
)


def validate_training_input(x, y):
    if sparse.issparse(x):
        raise ValueError(
            "Sparse inputs are unsupported; provide a dense numeric array or DataFrame."
        )
    if isinstance(x, pd.DataFrame):
        frame = x
    else:
        array = np.asarray(x)
        if array.ndim != 2 or array.dtype.kind not in "fiu":
            raise ValueError(
                "X must be a 2D numeric array; use a DataFrame for mixed categorical data."
            )
        frame = pd.DataFrame(array)
    if frame.shape[0] < 8 or not 1 <= frame.shape[1] <= 65535:
        raise ValueError("X requires at least 8 rows and 1..65535 features.")
    if not frame.columns.is_unique:
        raise ValueError("X column names must be unique.")
    if isinstance(y, pd.Series) and isinstance(y.dtype, pd.CategoricalDtype):
        raise ValueError(
            "Categorical/classification/multiclass targets are unsupported; regression only."
        )
    target = np.asarray(y)
    if target.ndim != 1 or len(target) != len(frame):
        raise ValueError("y must be one-dimensional, single-target, and match the rows of X.")
    if target.dtype.kind not in "fiu":
        raise ValueError(
            "Boolean, string, categorical and classification targets are unsupported; numeric regression only."
        )
    target = target.astype(np.float64)
    if not np.isfinite(target).all():
        raise ValueError(
            "y must contain only finite numeric values; missing/infinite targets unsupported."
        )
    if len(np.unique(target)) == 2:
        raise ValueError("Binary/classification targets are unsupported; use CodAdaptClassifier.")
    cats = []
    for j, dtype in enumerate(frame.dtypes):
        if pd.api.types.is_complex_dtype(dtype) or pd.api.types.is_datetime64_any_dtype(dtype):
            raise ValueError("Complex/datetime features are unsupported.")
        if not pd.api.types.is_numeric_dtype(dtype) or pd.api.types.is_bool_dtype(dtype):
            values = frame.iloc[:, j].dropna()
            try:
                for value in values.unique():
                    hash(value)
            except (TypeError, ValueError) as error:
                raise ValueError("Categorical values must be scalar hashable labels.") from error
            cats.append(j)
        elif np.isinf(frame.iloc[:, j].to_numpy(dtype=float)).any():
            raise ValueError(
                "Numeric features contain infinity; NaN is supported, infinity is not."
            )
    return frame, target, cats


class TrainOnlyEncoding:
    """Same external vocabulary as Round76; discovered on TRAIN only."""

    def __init__(self, x, cats):
        self.columns = tuple(x.columns)
        self.cats = tuple(cats)
        self.vocab = {}
        for j in cats:
            values = sorted(x.iloc[:, j].dropna().unique(), key=str)
            self.vocab[j] = {v: float(i) for i, v in enumerate(values)}

    def transform(self, x):
        a = np.empty(x.shape, dtype=float)
        for j in range(x.shape[1]):
            values = x.iloc[:, j]
            if j in self.vocab:
                values = values.map(self.vocab[j])
            a[:, j] = values.to_numpy(dtype=float)
        return a


def choose_branch(y, base, compiled):
    blend = base + ALPHA * (compiled - base)
    if not all(np.isfinite(a).all() for a in [y, base, blend]):
        raise ValueError("Nonfinite validation predictions; fitted artifact not produced.")
    b = float(np.sqrt(np.mean((y - base) ** 2)))
    z = float(np.sqrt(np.mean((y - blend) ** 2)))
    return ("BASE" if z >= b else "BLEND"), b, z


def teacher_class():
    try:
        import lightgbm
    except (ImportError, OSError) as error:
        raise ImportError(
            "SafeBlendRegressor.fit requires optional lightgbm==4.7.0. Install codadapt[safeblend] to fit; deployment predict/reload does not require LightGBM."
        ) from error
    if lightgbm.__version__ != "4.7.0":
        raise RuntimeError(
            "Frozen SafeBlend training requires lightgbm==4.7.0; no teacher version drift accepted."
        )
    return lightgbm.LGBMRegressor


class SafeBlendRegressor(RegressorMixin, BaseEstimator):
    """Experimental opt-in regression estimator with a fit-only LightGBM teacher.

    Parameters control reproducibility/logging/fit resource usage only. Alpha, safety,
    validation25%, teacher, compiler and capacity are fixed. Inference uses caller BLAS
    thread settings; scientific bitwise and latency audits use4threads.
    """

    def __init__(self, *, random_state=0, verbosity=0, n_jobs=4):
        self.random_state = random_state
        self.verbosity = verbosity
        self.n_jobs = n_jobs

    def __sklearn_is_fitted__(self):
        return hasattr(self, "_artifact")

    def fit(self, X, y):
        if (
            not isinstance(self.random_state, numbers.Integral)
            or isinstance(self.random_state, bool)
            or not 0 <= self.random_state <= 2**32 - 101
        ):
            raise ValueError("random_state must be an integer in0..2**32-101.")
        if (
            not isinstance(self.n_jobs, numbers.Integral)
            or isinstance(self.n_jobs, bool)
            or not 1 <= self.n_jobs <= 4
        ):
            raise ValueError("n_jobs must be1..4; teacher remains frozen at1thread.")
        if self.verbosity not in (0, 1):
            raise ValueError("verbosity must be0 or1.")
        x, target, cats = validate_training_input(X, y)
        teacher_type = teacher_class()
        # No training-only module is imported by reload/predict.
        from codadapt import CodAdaptRegressor

        from ._safe_blend_queries import make_queries
        from ._safe_blend_training import Compiled, Dictionary, pooled_boundaries

        seed = int(self.random_state)
        train, validation = train_test_split(
            np.arange(len(target)), test_size=0.25, random_state=seed + 100
        )
        started = time.perf_counter()
        durations = []
        with threadpool_limits(limits=int(self.n_jobs)):
            t = time.perf_counter()
            encoding = TrainOnlyEncoding(x.iloc[train], cats)
            xt = encoding.transform(x.iloc[train])
            durations.append(time.perf_counter() - t)
            t = time.perf_counter()
            config = dict(RECIPE["base_config"])
            config.update(random_state=seed, categorical_features=list(cats))
            base = CodAdaptRegressor(**config).fit(xt, target[train])
            durations.append(time.perf_counter() - t)
            t = time.perf_counter()
            teacher = teacher_type(**RECIPE["teacher_config"], random_state=seed)
            teacher.fit(xt, target[train], categorical_feature=list(cats))
            durations.append(time.perf_counter() - t)
            t = time.perf_counter()
            boundaries = pooled_boundaries(teacher, xt, cats)
            dictionary = Dictionary("SBD", 1024, xt, cats, boundaries, seed)
            q, qy, metadata = make_queries(
                "jitter", 25000, xt, cats, boundaries, seed, teacher.predict, dictionary
            )
            compiler = Compiled(dictionary).fit(q, qy)
            durations.append(time.perf_counter() - t)
            t = time.perf_counter()
            xv = encoding.transform(x.iloc[validation])
            branch, vb, vz = choose_branch(
                target[validation], base.predict(xv), compiler.predict(xv)
            )
            durations.append(time.perf_counter() - t)
            artifact = SafeBlendArtifact(base, compiler, encoding, branch)
        # No refit, no teacher, training/query data or optimizer retained. Attach atomically.
        self._artifact = artifact
        self._validation = (vb, vz)
        self._fit_record = (
            len(train),
            len(validation),
            tuple(durations),
            metadata["teacher_query_s"],
            time.perf_counter() - started,
        )
        if self.verbosity:
            print(f"SafeBlendRegressor: frozen {branch} branch; no refit; teacher discarded.")
        return self

    def predict(self, X):
        check_is_fitted(self)
        if sparse.issparse(X):
            raise ValueError("Sparse inputs unsupported.")
        if isinstance(X, pd.DataFrame):
            if tuple(X.columns) != self._artifact.shared_preprocessing.columns:
                raise ValueError("Prediction columns/order differ from the fitted schema.")
            if any(pd.api.types.is_complex_dtype(dtype) for dtype in X.dtypes):
                raise ValueError("Complex features unsupported.")
        else:
            X = np.asarray(X)
            if X.ndim != 2 or X.dtype.kind not in "fiu":
                raise ValueError(
                    "Prediction X must be a2D numeric array or a named mixed DataFrame."
                )
        if X.shape[0] == 0 or X.shape[1] != self.n_features_in_:
            raise ValueError("Prediction X has no rows or incorrect feature count.")
        return self._artifact.predict(X)

    @property
    def branch_(self):
        check_is_fitted(self)
        return self._artifact.branch

    @property
    def alpha_(self):
        check_is_fitted(self)
        return ALPHA

    @property
    def validation_base_rmse_(self):
        check_is_fitted(self)
        return self._validation[0]

    @property
    def validation_blend_rmse_(self):
        check_is_fitted(self)
        return self._validation[1]

    @property
    def compiled_(self):
        """Compiled deployment state, or None for a BASE-only artifact."""
        check_is_fitted(self)
        return getattr(self._artifact, "compiled", None)

    @property
    def compiler_(self):
        check_is_fitted(self)
        return getattr(self._artifact, "compiled", None)

    @property
    def base_(self):
        check_is_fitted(self)
        return self._artifact.base

    @property
    def n_features_in_(self):
        check_is_fitted(self)
        return len(self._artifact.shared_preprocessing.columns)

    @property
    def feature_names_in_(self):
        check_is_fitted(self)
        if not all(isinstance(c, str) for c in self._artifact.shared_preprocessing.columns):
            raise AttributeError("feature_names_in_ only defined for string column names.")
        return np.asarray(self._artifact.shared_preprocessing.columns, dtype=object)

    @property
    def fit_diagnostics_(self):
        check_is_fitted(self)
        result = dict(
            recipe="ROUND76_FROZEN_SAFE_BLEND",
            teacher="LightGBM4.7.0,fit-only",
            compiler="UNIFORM_SBD1024",
            validation_fraction=0.25,
            refit=False,
            teacher_retained=False,
            branch=self.branch_,
            alpha=ALPHA,
            validation_base_rmse=self.validation_base_rmse_,
            validation_blend_rmse=self.validation_blend_rmse_,
            resource_control="n_jobs fit-only; predict caller BLAS",
            capacity=1024,
        )
        if self._fit_record is not None:
            train, validation, durations, teacher_query, total = self._fit_record
            result.update(
                train_rows=train,
                validation_rows=validation,
                encoding_s=durations[0],
                base_s=durations[1],
                teacher_s=durations[2],
                compilation_s=durations[3],
                selection_s=durations[4],
                teacher_query_s=teacher_query,
                total_fit_s=total,
            )
        else:
            result["source"] = "MIGRATED_FROZEN_CHECKPOINT;not_a_new_fit"
        return result
