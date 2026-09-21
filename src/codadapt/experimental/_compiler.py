"""Exact additive EBM compilation, restricted to a verified optional dependency."""

import numbers

import numpy as np
import pandas as pd

from ._model import CompiledEBMClassifier, CompiledEBMRegressor, _frame, _Runtime


class CompilationError(ValueError):
    """REJECT: no compiled model is returned when the contract cannot be verified."""

    compiler_status_ = "REJECT"


def compile_ebm(teacher, *, X_verify, max_states=None):
    """Compile a fitted additive EBM with mandatory independent verification.

    Supports interpret-core 0.7.8, binary classification and scalar regression.
    X_verify must be a nonempty held-out DataFrame with teacher feature names.
    max_states limits exact lookup entries (including missing/unknown states).
    No approximation, fitting or teacher retention occurs. Raw output must be
    bitwise equal; probabilities must be within absolute tolerance 1e-15.
    """
    try:
        from importlib.metadata import version

        from interpret.glassbox import ExplainableBoostingClassifier, ExplainableBoostingRegressor
    except ImportError as exc:
        raise ImportError("Compilation requires the optional codadapt[ebm] dependency.") from exc
    if version("interpret-core") != "0.7.8":
        raise CompilationError("REJECT: only interpret-core 0.7.8 has been validated.")
    if type(teacher) not in (ExplainableBoostingClassifier, ExplainableBoostingRegressor):
        raise CompilationError("REJECT: expected a supported fitted additive EBM teacher.")
    try:
        return _compile(
            teacher, X_verify, max_states, type(teacher) is ExplainableBoostingClassifier
        )
    except CompilationError:
        raise
    except (ValueError, TypeError, AttributeError, IndexError, KeyError, OverflowError) as exc:
        raise CompilationError(
            f"REJECT: unsupported model/schema or verification failure: {exc}"
        ) from exc


def _compile(t, x, budget, classification):
    if not isinstance(x, pd.DataFrame) or len(x) == 0 or not x.columns.is_unique:
        raise CompilationError("REJECT: X_verify must be a nonempty unique-column DataFrame.")
    columns = list(t.feature_names_in_)
    p = len(columns)
    if (
        not p
        or len(set(columns)) != p
        or any(not isinstance(c, str) for c in columns)
        or list(x.columns) != columns
    ):
        raise CompilationError("REJECT: verification feature names/order must match the teacher.")
    if budget is not None and (
        isinstance(budget, bool) or not isinstance(budget, numbers.Integral) or budget < 0
    ):
        raise CompilationError("REJECT: max_states must be a nonnegative integer or None.")
    if (
        list(t.term_features_) != [(j,) for j in range(p)]
        or len(t.bins_) != p
        or len(t.term_scores_) != p
    ):
        raise CompilationError("REJECT: only ordered additive univariate terms are supported.")
    if len(t.feature_types_in_) != p or any(
        v not in ("continuous", "nominal", "ordinal") for v in t.feature_types_in_
    ):
        raise CompilationError("REJECT: unsupported feature type.")
    if getattr(t, "link_", None) != ("logit" if classification else "identity"):
        raise CompilationError("REJECT: unsupported output link.")
    intercept = np.asarray(t.intercept_, dtype=float)
    if intercept.size != 1 or not np.isfinite(intercept).all():
        raise CompilationError("REJECT: finite scalar intercept required; multiclass unsupported.")
    if classification and len(t.classes_) != 2:
        raise CompilationError("REJECT: binary classification only.")
    specs = []
    numeric_unknown = []
    capacity = payload = 0
    for j, levels in enumerate(t.bins_):
        bins = levels[0]
        v = np.asarray(t.term_scores_[j], dtype=float)
        if v.ndim != 1 or len(v) < 2 or not np.isfinite(v).all():
            raise CompilationError("REJECT: invalid or nonfinite cell values.")
        if isinstance(bins, dict):
            if any(not isinstance(k, str) for k in bins):
                raise CompilationError("REJECT: categorical bin labels must be strings.")
            if any(
                isinstance(i, bool)
                or not isinstance(i, numbers.Integral)
                or i < 1
                or i >= len(v) - 1
                for i in bins.values()
            ):
                raise CompilationError("REJECT: invalid category bin index.")
            keys = pd.Index(list(bins))
            values = np.array([v[i] for i in bins.values()] + [v[-1], v[0]])
            specs.append((False, keys, values))
            capacity += len(values)
            payload += values.nbytes + sum(len(k.encode("utf8")) + 8 for k in keys)
        else:
            cuts = np.asarray(bins, dtype=float)
            if (
                cuts.ndim != 1
                or len(v) != len(cuts) + 3
                or not np.isfinite(cuts).all()
                or np.any(np.diff(cuts) <= 0)
            ):
                raise CompilationError("REJECT: invalid numeric cuts/cells.")
            values = v[1:-1]
            keep = values[1:].view("u8") != values[:-1].view("u8")
            # Lossless equal-neighbor coalescing only, preserving cut semantics.
            edges = cuts[keep].copy()
            values = np.r_[values[np.r_[True, keep]], v[0]]
            specs.append((True, edges, values))
            numeric_unknown.append(v[-1])
            capacity += len(values) + 1  # Includes teacher numeric unknown-state audit slot.
            payload += edges.nbytes + values.nbytes + 8
    if budget is not None and capacity > budget:
        raise CompilationError(
            f"REJECT: exact export requires {capacity} states, budget is {budget}."
        )
    x = _frame(x, columns, specs)
    model = CompiledEBMClassifier() if classification else CompiledEBMRegressor()
    model._runtime_ = _Runtime(columns, float(intercept.ravel()[0]), specs, numeric_unknown)
    model.feature_names_in_ = np.asarray(columns, dtype=object)
    model.n_features_in_ = p
    if classification:
        model.classes_ = np.array(t.classes_, copy=True)
    raw = model._raw(x)
    expected = np.asarray(t.decision_function(x) if classification else t.predict(x), dtype=float)
    if (
        expected.shape != raw.shape
        or not np.isfinite(raw).all()
        or not np.array_equal(expected.view("u8"), raw.view("u8"))
    ):
        raise CompilationError("REJECT: raw-score verification failed (exact float64 required).")
    probability_error = None
    if classification:
        got = model.predict_proba(x)
        ref = np.asarray(t.predict_proba(x), dtype=float)
        if ref.shape != got.shape or not np.isfinite(ref).all():
            raise CompilationError("REJECT: invalid teacher probabilities.")
        probability_error = float(np.max(abs(got - ref)))
        if probability_error > 1e-15:
            raise CompilationError(
                "REJECT: probability verification exceeded absolute tolerance 1e-15."
            )
    model.compiler_status_ = "SAFE"
    model.required_capacity_ = capacity
    model.compiled_state_count_ = capacity
    model.estimated_memory_bytes_ = payload
    model.teacher_type_ = type(t).__name__
    model.task_ = "classification" if classification else "regression"
    model.verification_error_ = {
        "raw_max_absolute_error": 0.0,
        "raw_bit_mismatches": 0,
        "probability_max_absolute_error": probability_error,
        "probability_absolute_tolerance": 1e-15,
        "verification_rows": len(x),
    }
    return model
