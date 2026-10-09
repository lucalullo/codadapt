"""Exact native multiclass preparation and fit-local X-only reuse."""

import copy
import inspect
import warnings
from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.model_selection import train_test_split
from sklearn.utils.multiclass import type_of_target

from ._base import _rows, _target
from ._core import addresses, aggregate
from ._training import _surrogate, train_coded_memory
from .preprocessing import BucketEncoder


def validate_weights(weight, n):
    if weight is None:
        result = np.ones(n, dtype=np.float64)
    else:
        try:
            result = np.asarray(weight, dtype=np.float64)
        except (TypeError, ValueError) as error:
            raise ValueError("sample_weight must be a finite nonnegative 1D array.") from error
        if result.ndim != 1 or len(result) != n:
            raise ValueError("sample_weight must be a 1D array with one value per sample.")
        if not np.isfinite(result).all() or (result < 0).any():
            raise ValueError("sample_weight must be finite and nonnegative.")
    if not np.isfinite(result.sum()) or result.sum() <= 0:
        raise ValueError(
            "sample_weight must contain at least one non-zero value and have a finite positive sum."
        )
    return result


def is_multiclass(y, weight):
    """Binary/invalid cases still delegate to the original public fit verbatim."""
    try:
        a = np.asarray(y)
        if a.ndim == 2 and a.shape[1] == 1:
            a = a.ravel()
        if a.ndim != 1 or not len(a) or pd.isna(a).any():
            return False
        if weight is not None:
            w = np.asarray(weight, dtype=float)
            if w.ndim == 1 and len(w) == len(a) and np.isfinite(w).all() and (w >= 0).all():
                a = a[w > 0]
        return type_of_target(a) == "multiclass" and len(np.unique(a)) > 2
    except (TypeError, ValueError):
        return False


@dataclass
class Prepared:
    x: object
    y: np.ndarray
    weight: np.ndarray
    xv: object
    yv: object
    classes: np.ndarray
    rng: object
    train_ids: np.ndarray
    valid_ids: object
    estimated_bytes: int


def prepare(model, X, y, sample_weight, eval_set):
    model._validate_parameters()
    if sparse.issparse(X):
        raise TypeError("Sparse input is not supported; provide a dense numeric array.")
    if not isinstance(X, pd.DataFrame):
        X = np.asarray(X)
    if X.ndim != 2:
        raise ValueError("Expected 2D array. Reshape your data to (n_samples, n_features).")
    n, p = X.shape
    if not n or not p:
        raise ValueError(f"Found array with {n} sample(s) and {p} feature(s); minimum1 required.")
    y = _target(y)
    if len(y) != n:
        raise ValueError("X and y have inconsistent numbers of samples.")
    weight = validate_weights(sample_weight, n)
    estimate = n * (40 * p + 2 * model.n_tables + 80)
    estimate += (
        24
        * (p + model.n_tables * min(p, model.features_per_table))
        * max(model.n_bins + 1, model.max_categories + 3)
    )
    estimate += 32 * model.n_tables * model.table_size
    if estimate > 512 * 1024**2:
        raise ValueError(
            "Estimated working allocation exceeds the 512 MiB budget; reduce rows/features/model size."
        )
    keep = np.flatnonzero(weight > 0)
    x, y, w = _rows(X, keep), y[keep], weight[keep].copy()
    try:
        classes, counts = np.unique(y, return_counts=True)
        kind = type_of_target(y)
    except (TypeError, ValueError) as error:
        raise ValueError("Classification requires comparable scalar class labels.") from error
    if kind != "multiclass" or len(classes) < 3:
        raise ValueError("At least three positive-weight classes required for shared OVR.")
    rng = (
        copy.deepcopy(model.random_state)
        if isinstance(model.random_state, np.random.RandomState)
        else np.random.RandomState(model.random_state)
    )
    xv = yv = valid_ids = None
    train_ids = keep
    if eval_set is not None:
        if not isinstance(eval_set, (tuple, list)) or len(eval_set) != 2:
            raise ValueError("eval_set must be the pair (X_valid, y_valid).")
        xv, yv = eval_set
        if sparse.issparse(xv):
            raise TypeError(
                "Sparse validation input is not supported; provide a dense numeric array."
            )
        if not isinstance(xv, pd.DataFrame):
            xv = np.asarray(xv)
        yv = _target(yv)
        if xv.ndim != 2 or len(yv) != len(xv):
            raise ValueError("Validation X and y have inconsistent numbers of samples.")
        if not np.isin(yv, classes).all():
            raise ValueError(
                "Validation target contains classes absent from positive-weight training."
            )
    elif model.early_stopping:
        try:
            a, b = train_test_split(
                np.arange(len(y)),
                test_size=model.validation_fraction,
                random_state=copy.deepcopy(rng),
                stratify=y,
            )
            if len(np.unique(y[a])) != len(classes):
                raise ValueError("Training split does not retain all classes.")
        except ValueError as error:
            raise ValueError(
                f"Insufficient data ({len(y)} sample(s)) for common stratified internal validation; use early_stopping=False or a valid eval_set."
            ) from error
        xv, yv = _rows(x, b), y[b]
        x, y, w = _rows(x, a), y[a], w[a]
        train_ids, valid_ids = keep[a], keep[b]
    _, counts = np.unique(y, return_counts=True)
    if counts.min() < 5:
        warnings.warn(
            "Rare class (<5 positive-weight TRAIN examples): native OVR quality is not guaranteed.",
            UserWarning,
            stacklevel=2,
        )
    return Prepared(x, y, w, xv, yv, classes, rng, train_ids, valid_ids, int(estimate))


@dataclass
class NativeHead:
    intercept: float
    levels: list
    table_size: int


class XCache:
    def __init__(self, weight, budget=32 * 2**20):
        self.weight, self.budget, self.bytes = weight, budget, 0
        self.addresses, self.masses, self.combinations = {}, {}, {}

    def address(self, z, features, codes, size):
        key = (id(z), tuple(features), size, tuple(c.tobytes() for c in codes))
        if key not in self.addresses:
            value = addresses(z, features, codes, size)
            if self.bytes + value.nbytes <= self.budget:
                self.addresses[key] = value
                self.bytes += value.nbytes
            return value
        return self.addresses[key]

    def surrogate(self, y, score, old, weight, binary):
        assert binary and weight is self.weight
        return _surrogate(y, score, old, weight, binary)

    def aggregate(self, index, h, r, size):
        # native h=weight/4 for EVERY class in this fit; weight is identity bound.
        key = (index.__array_interface__["data"][0], index.shape, index.strides, size)
        if key in self.masses:
            return self.masses[key][1], np.bincount(index, weights=h * r, minlength=size)
        a, b = aggregate(index, h, r, size)
        required = a.nbytes + (0 if index.base is not None else index.nbytes)
        if self.bytes + required <= self.budget:
            self.masses[key] = (index, a)
            self.bytes += required
        return a, b

    def combination_count(self, z, features):
        key = (id(z), tuple(features))
        if key not in self.combinations:
            self.combinations[key] = int(np.unique(z[:, features], axis=0).shape[0])
        return self.combinations[key]


def fitter(cache):
    text = inspect.getsource(train_coded_memory)
    old = "int(np.unique(z[:, features], axis=0).shape[0])"
    assert text.count(old) == 1
    namespace = dict(train_coded_memory.__globals__)
    namespace.update(
        addresses=cache.address,
        aggregate=cache.aggregate,
        _surrogate=cache.surrogate,
        shared_combination_count=cache.combination_count,
    )
    exec(
        compile(
            text.replace(old, "shared_combination_count(z, features)"),
            "<private exact native OVR reuse>",
            "exec",
        ),
        namespace,
    )
    return namespace["train_coded_memory"]


def fit_heads(model, d):
    tick = perf_counter()
    rng = copy.deepcopy(d.rng)
    encoder_seed = int(rng.randint(2**31 - 1))
    finest = max(2, min(16, model.n_bins))
    resolutions = [max(2, finest // 4), max(2, finest // 2), finest]
    encoder = BucketEncoder(
        n_bins=finest,
        max_categories=model.max_categories,
        quantile_sample_size=model.quantile_sample_size,
        categorical_features=model.categorical_features,
        random_state=encoder_seed,
    )
    z = encoder.fit_transform_levels(d.x, resolutions)
    zv = encoder.transform_levels(d.xv) if d.xv is not None else None
    preprocessing_s = perf_counter() - tick
    cache = XCache(d.weight)
    fit = fitter(cache)
    heads = []
    # Local native head models are discarded; only predictive state survives.
    from codadapt import CodAdaptClassifier

    for label in d.classes:
        head = CodAdaptClassifier(**model.get_params(deep=False))
        head.classes_ = np.array([0, 1])
        head.shared_encoder_ = head.encoder_ = encoder
        head.encoders_, head.resolution_bins_ = encoder.level_views_, resolutions
        head.n_features_in_, head.timings_ = d.x.shape[1], {"preprocessing": 0.0}
        fit(
            head,
            z,
            (d.y == label).astype(float),
            d.weight,
            zv,
            (d.yv == label).astype(float) if d.yv is not None else None,
            copy.deepcopy(rng),
        )
        heads.append(NativeHead(head.intercept_, head.levels_, head.table_size))
    return encoder, heads, preprocessing_s
