"""Opt-in native Base/Rational diversity blend with frozen validation fallback."""

from numbers import Integral

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import train_test_split
from sklearn.utils import check_random_state
from sklearn.utils.validation import check_is_fitted
from threadpoolctl import threadpool_limits

from ..preprocessing import BucketEncoder
from ..regressor import CodAdaptRegressor
from ._rational import Rational


class SafeBlendRegressor(RegressorMixin, BaseEstimator):
    """Experimental, fully native regression blend; never the CodAdapt default.

    A fixed 25% internal holdout selects Base or Base + 0.30*(Rational-Base).
    Both models use only the remaining training rows; neither is refitted after
    selection. Validation fallback reduces observed downside, but cannot
    guarantee improvement on unseen data. No external model is fitted or retained.

    Parameters
    ----------
    random_state : int, RandomState or None, default=None
        Controls the internal split and native Base. Integers give repeatable fits.
    verbosity : int, default=0
        Native Base logging level, between 0 and 2.
    n_jobs : int, default=1
        Positive numerical thread limit during fit. No process pool is created.
        Concurrent fits in separate threads should not share thread-pool limits.

    Notes
    -----
    Dense real numeric arrays and mixed pandas DataFrames are supported. Use
    pandas categorical/string/boolean columns to identify categories. This
    minimal interface does not expose categorical column indices, sample weights
    or an external eval_set. Targets must be one-dimensional, finite regression
    values; explicit class labels and conventional small integer class encodings
    are rejected. See docs/SAFE_BLEND_EXPERIMENTAL.md for the frozen contract.
    """

    def __init__(self, random_state=None, verbosity=0, n_jobs=1):
        self.random_state = random_state
        self.verbosity = verbosity
        self.n_jobs = n_jobs

    @staticmethod
    def _target(y, n):
        if isinstance(getattr(y, "dtype", None), pd.CategoricalDtype):
            raise ValueError(
                "SafeBlendRegressor supports regression, not categorical class labels."
            )
        target = np.asarray(y)
        if target.ndim != 1:
            raise ValueError(
                "SafeBlendRegressor supports one-dimensional single-target regression."
            )
        if len(target) != n:
            raise ValueError("X and y must contain the same number of samples.")
        if target.dtype.kind not in "iuf":
            raise ValueError("y must contain real numeric regression values, not class labels.")
        target = target.astype(np.float64)
        if not np.isfinite(target).all():
            raise ValueError(
                "y must contain finite regression values; missing/infinity are invalid."
            )
        labels = np.unique(target)
        if 2 <= len(labels) <= 20 and np.array_equal(labels, labels.astype(np.int64)):
            if len(labels) == 2 or np.array_equal(labels, np.arange(len(labels))):
                raise ValueError(
                    "Classification labels are unsupported; use CodAdaptClassifier. "
                    "SafeBlendRegressor expects regression targets."
                )
        return target

    def _validate_parameters(self):
        for name, low, high in (("verbosity", 0, 2), ("n_jobs", 1, None)):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
                raise ValueError(f"{name} must be an integer.")
            if value < low or (high is not None and value > high):
                raise ValueError(f"{name} is outside its supported range.")
        if isinstance(self.random_state, (bool, np.bool_)):
            raise ValueError("random_state must be an integer, RandomState or None.")
        if isinstance(self.random_state, Integral):
            seed = int(self.random_state)
            if not 0 <= seed <= 2**32 - 101:
                raise ValueError("random_state must be between 0 and 2**32 - 101.")
            return seed
        return int(check_random_state(self.random_state).randint(0, 2**32 - 100, dtype=np.int64))

    def _prepare(self, X):
        X = BucketEncoder._validate_input(X)
        if isinstance(X, pd.DataFrame) != self._fit_dataframe_:
            raise ValueError(
                "Input must use the same DataFrame/array representation as during fit."
            )
        if X.shape[1] != self.n_features_in_:
            raise ValueError(
                f"X must have {self.n_features_in_} features, matching the fitted schema."
            )
        if self._fit_dataframe_:
            order = X.columns.get_indexer(self._columns_)
            if (order < 0).any():
                raise ValueError("DataFrame columns must match the fitted schema.")
            if not X.columns.equals(self._columns_):
                X = X.iloc[:, order]
            X = X.copy()
        else:
            X = pd.DataFrame(X, columns=self._columns_)
        for j, vocabulary in self._vocab_.items():
            series = X.iloc[:, j]
            BucketEncoder._categorical_values(series, self._columns_[j])
            X[X.columns[j]] = series.map(vocabulary).astype(float)
        # Validate unsupported numeric dtypes/infinities before conversion. Base
        # performs its own numeric validation; no additional fitted encoder exists.
        for j in range(X.shape[1]):
            if j not in self._vocab_:
                series = X.iloc[:, j]
                BucketEncoder._numeric_values(series, self._columns_[j])
        return X.astype(np.float64)

    def fit(self, X, y):
        """Fit the frozen native recipe using training-only preprocessing and holdout."""
        # A failed/refallback fit cannot leave an old fitted branch accessible.
        for name in list(vars(self)):
            if name.endswith("_"):
                delattr(self, name)
        seed = self._validate_parameters()
        X = BucketEncoder._validate_input(X)
        target = self._target(y, len(X))
        if len(X) < 8:
            raise ValueError(
                "SafeBlendRegressor requires at least 8 samples for internal validation."
            )
        cats = sorted(BucketEncoder()._categorical_indices(X))
        train, validation = train_test_split(
            np.arange(len(X)), test_size=0.25, random_state=seed + 100
        )
        self.n_features_in_ = X.shape[1]
        self._fit_dataframe_ = isinstance(X, pd.DataFrame)
        self._columns_ = X.columns.copy() if self._fit_dataframe_ else pd.RangeIndex(X.shape[1])
        if self._fit_dataframe_ and all(isinstance(c, str) for c in X.columns):
            self.feature_names_in_ = X.columns.to_numpy(dtype=object, copy=True)
        self._vocab_ = {}
        for j in cats:
            series = BucketEncoder._column(X, j)
            BucketEncoder._categorical_values(series, self._columns_[j])
            values = sorted(series.iloc[train].dropna().unique(), key=str)
            self._vocab_[j] = {v: i for i, v in enumerate(values)}
        prepared = self._prepare(X)
        x_train, x_validation = prepared.iloc[train], prepared.iloc[validation]
        with threadpool_limits(limits=int(self.n_jobs)):
            base = CodAdaptRegressor(
                categorical_features=cats, random_state=seed, verbosity=self.verbosity
            ).fit(x_train, target[train], eval_set=(x_validation, target[validation]))
            rational = Rational(bins=16, ridge=0.001, seed=seed, maxiter=100, cats=cats).fit(
                x_train, target[train]
            )
            base_prediction = base.predict(x_validation)
            rational_prediction = rational.predict(x_validation)
        blended = base_prediction + 0.30 * (rational_prediction - base_prediction)
        if not np.isfinite(rational.theta).all() or not np.isfinite(blended).all():
            raise ValueError("Native Rational fitting produced nonfinite values; fit failed.")
        base_loss = np.mean((target[validation] - base_prediction) ** 2)
        blend_loss = np.mean((target[validation] - blended) ** 2)
        # Strict squared-loss comparison preserves the Round78 arithmetic exactly;
        # square root is monotone, so this is strict validation RMSE improvement.
        accepted = bool(blend_loss < base_loss)
        self.base_ = base
        self.rational_ = rational if accepted else None
        self.branch_ = "BLEND" if accepted else "BASE"
        self.alpha_ = 0.30 if accepted else 0.0
        self.validation_base_rmse_ = float(np.sqrt(base_loss))
        self.validation_blend_rmse_ = float(np.sqrt(blend_loss))
        self.fit_diagnostics_ = {
            "train_samples": len(train),
            "validation_samples": len(validation),
            "rational_converged": rational.converged,
            "rational_iterations": len(rational.trace),
            "refit": False,
        }
        self._is_fitted_ = True
        return self

    def predict(self, X):
        """Return predictions using only the retained native branch."""
        check_is_fitted(self, "_is_fitted_")
        prepared = self._prepare(X)
        prediction = self.base_.predict(prepared)
        if self.rational_ is None:
            return prediction
        return prediction + self.alpha_ * (self.rational_.predict(prepared) - prediction)
