"""Shared estimator API and train-only preparation."""

import copy
import numbers
import warnings
from time import perf_counter

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.base import BaseEstimator
from sklearn.exceptions import DataConversionWarning
from sklearn.model_selection import train_test_split
from sklearn.utils.multiclass import type_of_target
from sklearn.utils.validation import check_is_fitted

from ._core import addresses
from ._inference import predict_coded_memory_buckets
from ._training import (
    train_coded_memory,
)
from .preprocessing import BucketEncoder, _pool_categorical_strings


def _rows(X, indices):
    return X.iloc[indices] if isinstance(X, pd.DataFrame) else X[indices]


def _target(y):
    if y is None:
        raise ValueError("This estimator requires y to be passed, but the target y is None.")
    result = np.asarray(y)
    if result.ndim == 2 and result.shape[1] == 1:
        warnings.warn(
            "A column-vector y was passed when a 1d array was expected.",
            DataConversionWarning,
            stacklevel=3,
        )
        result = result.ravel()
    if result.ndim != 1:
        raise ValueError("Only single-target, one-dimensional y is supported; no multioutput.")
    if len(result) == 0 or pd.isna(result).any():
        raise ValueError("Target y must be nonempty and contain no missing values (NaN or NA).")
    if result.dtype.kind == "c":
        raise ValueError("Complex data not supported in target y.")
    if result.dtype.kind in "fiu" and not np.isfinite(result).all():
        raise ValueError("Target y contains infinity or a value too large.")
    return result


_LEGACY_MEMORY_MIB = 2**20


def _legacy_diagnostics(estimate, shape):
    # This is the inherited budget domain, never a new memory safety bound.
    rows, features = shape if type(shape) is tuple and len(shape) == 2 else (None, None)
    return dict(
        required_bytes=None,
        effective_budget_bytes=512 * _LEGACY_MEMORY_MIB,
        available_bytes=None,
        capacity_bytes=None,
        process_RSS_bytes=None,
        rows=rows,
        features=features,
        dtype="UNPROFILED_LEGACY_INPUT",
        observed_class_count=None,
        class_count_bound_known=False,
        elapsed_s=None,
        policy="EXACT_LEGACY_512_ADMISSION_DOMAIN",
        model_changed=False,
        status="LEGACY_COMPATIBILITY_UNPROFILED_CONVERSION",
        tier_status="LEGACY_COMPATIBILITY_EXACT_STATIC_DOMAIN",
        virtual_domain="UNOBSERVED",
        virtual_observation=dict(status="UNOBSERVED", scope="Not queried inside legacy domain"),
        profile_complete=False,
        resource_qualified=False,
        required_bytes_is_lower_bound=True,
        unprofiled_external_inputs=["All roles deliberately unprofiled inside inherited domain"],
        conversion_peak_bound_known=False,
        safety_scope="Inherited512heuristic risk only;no input profile or resource certificate. Arbitrary custom conversion and hidden constraints remain unbounded.",
    )


def _record_legacy_diagnostics(model, diagnostics, pre_conversion=True):
    for attribute, key in [
        ("memory_admission_available_bytes_", "available_bytes"),
        ("memory_admission_process_RSS_bytes_", "process_RSS_bytes"),
        ("memory_admission_virtual_available_bytes_", "virtual_available_bytes"),
    ]:
        setattr(model, attribute, diagnostics.get(key))
    model.memory_admission_tier_ = diagnostics["tier_status"]
    model.memory_admission_virtual_domain_ = diagnostics["virtual_domain"]
    model.memory_admission_safety_certificate_ = False
    model.effective_memory_budget_mb_ = diagnostics["effective_budget_bytes"] / _LEGACY_MEMORY_MIB
    model.memory_admission_required_bytes_ = diagnostics["required_bytes"]
    model.memory_admission_profile_complete_ = diagnostics["profile_complete"]
    model.memory_admission_resource_qualified_ = diagnostics["resource_qualified"]
    model.memory_admission_required_is_lower_bound_ = diagnostics["required_bytes_is_lower_bound"]
    if pre_conversion:
        model.memory_validation_conversion_preflight_qualified_ = diagnostics["profile_complete"]
        model.memory_admission_preconversion_status_ = diagnostics["status"]
        model.memory_admission_status_ = diagnostics["status"]
        model.memory_admission_shape_ = (diagnostics["rows"], diagnostics["features"])
    else:
        model.memory_admission_status_ = (
            (
                "LEGACY_COMPATIBILITY_AFTER_ORIGINAL_NORMALIZATION_RECHECK"
                if diagnostics["tier_status"].startswith("LEGACY_COMPATIBILITY")
                else "AUTO_ADMIT_AFTER_ORIGINAL_NORMALIZATION_RECHECK"
            )
            if diagnostics["profile_complete"]
            else "LEGACY_COMPATIBILITY_UNPROFILED_REMAINDER"
        )


def _recheck_memory_after_conversion(model, estimate, X, y, weight, eval_set):
    if type(estimate) is int and 0 <= estimate <= 512 * _LEGACY_MEMORY_MIB:
        _record_legacy_diagnostics(
            model,
            _legacy_diagnostics(estimate, model.memory_admission_shape_),
            pre_conversion=False,
        )
    else:
        from ._memory_admission import recheck_after_conversion

        recheck_after_conversion(model, estimate, X, y, weight, eval_set)


class _BaseCodAdapt(BaseEstimator):
    """Common parameters; construction only stores the supplied values."""

    def __init__(
        self,
        *,
        n_bins=32,
        max_categories=128,
        quantile_sample_size=20000,
        n_tables=8,
        features_per_table=3,
        table_size=256,
        main_effects=True,
        l2=5.0,
        categorical_features=None,
        early_stopping=True,
        validation_fraction=0.15,
        tol=1e-5,
        random_state=None,
        verbosity=0,
        lookup_budget=24,
        memory_budget_mb="auto",
    ):
        self.n_bins = n_bins
        self.max_categories = max_categories
        self.quantile_sample_size = quantile_sample_size
        self.n_tables = n_tables
        self.features_per_table = features_per_table
        self.table_size = table_size
        self.main_effects = main_effects
        self.l2 = l2
        self.categorical_features = categorical_features
        self.early_stopping = early_stopping
        self.validation_fraction = validation_fraction
        self.tol = tol
        self.random_state = random_state
        self.verbosity = verbosity
        self.lookup_budget = lookup_budget
        self.memory_budget_mb = memory_budget_mb

    def _validate_parameters(self):
        automatic = isinstance(self.memory_budget_mb, str) and self.memory_budget_mb == "auto"
        if not automatic and (
            isinstance(self.memory_budget_mb, (bool, np.bool_))
            or not isinstance(self.memory_budget_mb, numbers.Integral)
            or self.memory_budget_mb < 1
        ):
            raise ValueError("memory_budget_mb must be a positive integer in MiB or 'auto'.")
        bounds = {
            "n_bins": (2, 4096),
            "max_categories": (1, 4096),
            "quantile_sample_size": (2, 1000000),
            "n_tables": (0, 128),
            "features_per_table": (1, 32),
            "table_size": (16, 4096),
            "verbosity": (0, 2),
            "lookup_budget": (1, 4096),
        }
        for name, (low, high) in bounds.items():
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral):
                raise ValueError(f"{name} must be an integer in [{low}, {high}].")
            if not low <= value <= high:
                raise ValueError(f"{name} must be in [{low}, {high}].")
        if self.table_size & (self.table_size - 1):
            raise ValueError("table_size must be a power of two from 16 through 4096.")
        for name in ("main_effects", "early_stopping"):
            if not isinstance(getattr(self, name), (bool, np.bool_)):
                raise ValueError(f"{name} must be boolean.")
        for name in ("l2", "tol", "validation_fraction"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
                raise ValueError(f"{name} must be a finite real number.")
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if self.l2 <= 0 or self.tol < 0:
            raise ValueError("l2 must be positive and tol nonnegative.")
        if not 0 < self.validation_fraction < 1:
            raise ValueError("validation_fraction must lie strictly between zero and one.")
        state = self.random_state
        if state is not None and not isinstance(state, (numbers.Integral, np.random.RandomState)):
            raise ValueError("random_state must be None, an integer, or a NumPy RandomState.")
        if isinstance(state, numbers.Integral) and not 0 <= state <= 2**32 - 1:
            raise ValueError("random_state integer must lie in [0, 2**32 - 1].")

    def _check_memory_budget(self, n, p, eval_set=None, *, X=None, y=None, sample_weight=None):
        """Apply the deterministic working-allocation heuristic, not an RSS cap."""
        validation_rows = 0
        if eval_set is not None:
            if not isinstance(eval_set, (tuple, list)) or len(eval_set) != 2:
                raise ValueError("eval_set must be the pair (X_valid, y_valid).")
            if sparse.issparse(eval_set[0]):
                raise TypeError(
                    "Sparse validation input is not supported; provide a dense numeric array."
                )
            # Read only the row count before copies/encoding; detailed validation
            # remains in preparation. External validation is live during fit too.
            try:
                validation_rows = len(eval_set[0])
            except TypeError as error:
                raise ValueError("Validation X must be a 2D array or DataFrame.") from error
        estimate = (int(n) + int(validation_rows)) * (40 * int(p) + 2 * self.n_tables + 80)
        estimate += (
            24
            * (p + self.n_tables * min(p, self.features_per_table))
            * max(self.n_bins + 1, self.max_categories + 3)
        )
        estimate += 32 * self.n_tables * self.table_size
        if isinstance(self.memory_budget_mb, str) and self.memory_budget_mb == "auto":
            if 0 <= int(estimate) <= 512 * _LEGACY_MEMORY_MIB:
                _record_legacy_diagnostics(
                    self, _legacy_diagnostics(int(estimate), (int(n), int(p)))
                )
            else:
                from ._memory_admission import check_auto, record_diagnostics

                diagnostics = check_auto(
                    self, int(estimate), X, y, sample_weight, eval_set, shape=(int(n), int(p))
                )
                record_diagnostics(self, diagnostics)
            return int(estimate)
        budget = int(self.memory_budget_mb) * 1024**2
        if estimate > budget:
            raise ValueError(
                f"Estimated working allocation {estimate / 1024**2:.2f} MiB exceeds "
                f"the {self.memory_budget_mb} MiB memory_budget_mb budget "
                f"({n} training rows, {validation_rows} external validation rows, "
                f"{p} features). Use fewer rows/features or explicitly raise "
                "memory_budget_mb only with sufficient RAM headroom. This heuristic "
                "is not a total process RSS limit or an out-of-memory guarantee."
            )
        return int(estimate)

    def __setstate__(self, state):
        # Trusted RC1 artifacts predate the explicit resource-only parameter.
        state = state.copy()
        state.setdefault("memory_budget_mb", 512)
        super().__setstate__(state)
        if hasattr(self, "shared_encoder_"):
            _pool_categorical_strings(self.shared_encoder_)

    def _encode_target(self, y, fitting=False):
        if self._task == "regression":
            try:
                values = np.asarray(y, dtype=np.float64)
            except (TypeError, ValueError) as error:
                raise ValueError("Regression requires a finite numeric target.") from error
            if not np.isfinite(values).all():
                raise ValueError("Regression target must be finite.")
            return values
        if fitting:
            try:
                target_type = type_of_target(y)
                classes = np.unique(y)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "Binary targets require comparable scalar class labels."
                ) from error
            if target_type == "continuous":
                raise ValueError(
                    "Unknown label type: continuous. Only binary classification is supported."
                )
            if target_type != "binary" or len(classes) != 2:
                raise ValueError(
                    "Only binary classification is supported: one class was found; "
                    "need two classes with positive weight."
                )
            self.classes_ = classes
        if not np.isin(y, self.classes_).all():
            raise ValueError(
                "Validation target contains classes absent from positive-weight training."
            )
        return (y == self.classes_[1]).astype(np.float64)

    def _prepare_training_weight(self, y, weight, *, encoded_classes=None):
        # Regression retains the original vector and arithmetic verbatim.
        return weight

    def fit(self, X, y, sample_weight=None, eval_set=None):
        """Fit only on positive-weight training rows, with optional external validation."""
        started = perf_counter()
        # A failed refit must not leave the former fitted model available for prediction.
        for name in list(vars(self)):
            if name.endswith("_"):
                delattr(self, name)
        self._validate_parameters()
        if sparse.issparse(X):
            raise TypeError("Sparse input is not supported; provide a dense numeric array.")
        if not isinstance(X, pd.DataFrame):
            try:
                X = np.asarray(X)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "X must be a DataFrame or dense numeric array-like input."
                ) from error
        if X.ndim != 2:
            raise ValueError("Expected 2D array. Reshape your data to (n_samples, n_features).")
        n, p = X.shape
        if not p:
            raise ValueError(
                f"Found array with 0 feature(s) (shape={X.shape}) while a minimum of 1 is required."
            )
        if not n:
            raise ValueError(
                f"Found array with 0 sample(s) (shape={X.shape}); a minimum of 1 is required."
            )
        y = _target(y)
        if len(y) != n:
            raise ValueError("X and y have inconsistent numbers of samples.")
        if sample_weight is None:
            weight = np.ones(n, dtype=np.float64)
        else:
            try:
                weight = np.asarray(sample_weight, dtype=np.float64)
            except (TypeError, ValueError) as error:
                raise ValueError("sample_weight must be a finite nonnegative 1D array.") from error
            if weight.ndim != 1 or len(weight) != n:
                raise ValueError("sample_weight must be a 1D array with one value per sample.")
            if not np.isfinite(weight).all() or (weight < 0).any():
                raise ValueError("sample_weight must be finite and nonnegative.")
        if not np.isfinite(weight.sum()) or weight.sum() <= 0:
            raise ValueError(
                "sample_weight must contain at least one non-zero value and have a finite positive sum."
            )
        self.estimated_memory_bytes_ = self._check_memory_budget(
            n, p, eval_set, X=X, y=y, sample_weight=weight
        )
        keep = np.flatnonzero(weight > 0)
        X_train, y_train, weight = _rows(X, keep), y[keep], weight[keep].copy()
        y_train = self._encode_target(y_train, fitting=True)
        rng = (
            copy.deepcopy(self.random_state)
            if isinstance(self.random_state, np.random.RandomState)
            else np.random.RandomState(self.random_state)
        )
        X_valid = y_valid = None
        if eval_set is not None:
            if not isinstance(eval_set, (tuple, list)) or len(eval_set) != 2:
                raise ValueError("eval_set must be the pair (X_valid, y_valid).")
            X_valid, y_valid = eval_set
            if sparse.issparse(X_valid):
                raise TypeError(
                    "Sparse validation input is not supported; provide a dense numeric array."
                )
            if not isinstance(X_valid, pd.DataFrame):
                try:
                    X_valid = np.asarray(X_valid)
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        "Validation X must be a 2D dense array or DataFrame."
                    ) from error
            if X_valid.ndim != 2:
                raise ValueError(
                    "Validation X must be a 2D array with shape (n_samples, n_features)."
                )
            y_valid = self._encode_target(_target(y_valid))
            if len(y_valid) != X_valid.shape[0]:
                raise ValueError("Validation X and y have inconsistent numbers of samples.")
        elif self.early_stopping:
            indices = np.arange(len(y_train))
            try:
                train_indices, valid_indices = train_test_split(
                    indices,
                    test_size=self.validation_fraction,
                    random_state=copy.deepcopy(rng),
                    stratify=y_train if self._task == "classification" else None,
                )
                if self._task == "classification" and len(np.unique(y_train[train_indices])) != 2:
                    raise ValueError("Training split does not retain both classes.")
            except ValueError as error:
                raise ValueError(
                    f"Insufficient data ({len(y_train)} sample(s)) for internal validation; "
                    "use early_stopping=False or a valid eval_set."
                ) from error
            X_valid, y_valid = _rows(X_train, valid_indices), y_train[valid_indices]
            X_train, y_train, weight = (
                _rows(X_train, train_indices),
                y_train[train_indices],
                weight[train_indices],
            )
        if getattr(self, "memory_validation_conversion_preflight_qualified_", True) is False:
            normalized_eval = (X_valid, y_valid) if X_valid is not None else None
            _recheck_memory_after_conversion(
                self, self.estimated_memory_bytes_, X_train, y_train, weight, normalized_eval
            )
        weight = self._prepare_training_weight(
            y_train, weight, encoded_classes=getattr(self, "classes_", None)
        )
        self.n_features_in_ = p
        self.timings_ = {}
        preprocessing_start = perf_counter()
        encoder_seed = int(rng.randint(2**31 - 1))
        finest = max(2, min(16, self.n_bins))
        self.resolution_bins_ = [max(2, finest // 4), max(2, finest // 2), finest]
        self.shared_encoder_ = BucketEncoder(
            n_bins=finest,
            max_categories=self.max_categories,
            quantile_sample_size=self.quantile_sample_size,
            categorical_features=self.categorical_features,
            random_state=encoder_seed,
        )
        Z_levels = self.shared_encoder_.fit_transform_levels(X_train, self.resolution_bins_)
        Z_valid_levels = (
            self.shared_encoder_.transform_levels(X_valid) if X_valid is not None else None
        )
        self.encoders_ = self.shared_encoder_.level_views_
        self.encoder_ = self.shared_encoder_
        if hasattr(self.encoder_, "feature_names_in_"):
            self.feature_names_in_ = self.encoder_.feature_names_in_.copy()
        self.timings_["preprocessing"] = perf_counter() - preprocessing_start
        train_coded_memory(
            self,
            Z_levels,
            y_train,
            weight,
            Z_valid_levels,
            y_valid,
            rng,
        )
        self.timings_["fit_total"] = perf_counter() - started
        if self.verbosity:
            print(
                f"CodAdapt fitted {self.n_iter_} iterations; restored={self.best_iteration_}; moves={self.accepted_moves_}; fit={self.timings_['fit_total']:.3f}s"
            )
        self._is_fitted_ = True
        return self

    def _raw_predict_buckets(self, Z):
        result = np.full(len(Z), self.intercept_, dtype=np.float64)
        for j, values in enumerate(self.main_tables_):
            result += values[Z[:, j]]
        for features, codes, values in zip(self.groups_, self.codes_, self.tables_):
            index = addresses(Z, features, codes, self.table_size)
            supported = np.ones(len(Z), dtype=bool)
            for j in features:
                supported &= self.encoder_.support_[j][Z[:, j]]
            result += np.where(supported, values[index], 0.0)
        return result

    def _decision(self, X):
        check_is_fitted(self)
        from ._batching import decision
        return decision(self.shared_encoder_, X, lambda z: predict_coded_memory_buckets(
            self.levels_, self.encoders_, z, self.intercept_, self.table_size
        ))

    def __sklearn_is_fitted__(self):
        return getattr(self, "_is_fitted_", False)

    def _more_tags(self):
        return {"allow_nan": True, "requires_y": True, "X_types": ["2darray", "categorical"]}

    def __sklearn_tags__(self):
        tags = super().__sklearn_tags__()
        tags.input_tags.allow_nan = True
        tags.input_tags.categorical = True
        tags.input_tags.string = True
        tags.input_tags.sparse = False
        tags.target_tags.required = True
        return tags
