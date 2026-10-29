"""Private resource admission with an explicitly unqualified legacy fallback."""

import time

import numpy as np
import pandas as pd

from ._memory_policy import MIB, requirement
from ._resource_snapshot import observe
from ._visible_tier import decide as tier_decide
from ._visible_virtual import merge as merge_virtual
from ._visible_virtual import observe as observe_virtual


def payload(value):
    """Conservative trusted payload, or explicit opaque metadata rejection."""
    from ._trusted_payload import ensure_trusted

    ensure_trusted(value)
    if isinstance(value, pd.DataFrame):
        return int(value.memory_usage(index=True, deep=True).sum())
    if isinstance(value, pd.Series):
        return int(value.memory_usage(index=True, deep=True))
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            if value.ndim == 1:
                return int(pd.Series(value, copy=False).memory_usage(index=True, deep=True))
            if value.ndim == 2:
                return int(
                    pd.DataFrame(value, copy=False).memory_usage(index=True, deep=True).sum()
                )
            raise ValueError("AUTO cannot bound an object array with this dimensionality")
        return int(value.nbytes)
    from ._sequence_payload import sequence_payload

    return sequence_payload(value)


def summary(observation):
    if observation.get("status") != "OBSERVED_VISIBLE_LIMITS":
        raise ValueError(
            "AUTO resources are unknown or incomplete: "
            + "; ".join(observation.get("uncertainties", []))
        )
    a = observation.get("effective_available_bytes")
    c = observation.get("effective_capacity_bytes")
    rss = observation.get("process_RSS_bytes")
    if any(type(v) is not int or v < 0 for v in [a, c, rss]) or c == 0 or a > c:
        raise ValueError("AUTO resource observation is invalid")
    return a, c, rss


def _snapshot():
    try:
        return observe()
    except (OSError, TypeError, ValueError, OverflowError):
        return dict(status="UNOBSERVED", uncertainties=["Resource observation unavailable"])


def _tier(estimate, required, snapshots, complete, virtual):
    known = []
    rss_values = []
    for snapshot in snapshots:
        a = snapshot.get("effective_available_bytes")
        c = snapshot.get("effective_capacity_bytes")
        rss = snapshot.get("process_RSS_bytes")
        if (
            snapshot.get("status") == "OBSERVED_VISIBLE_LIMITS"
            and type(a) is int
            and type(c) is int
            and 0 <= a <= c
            and c > 0
        ):
            known.append((a, c))
            if type(rss) is int and rss >= 0:
                rss_values.append(rss)
    if known:
        capacity = min(c for _, c in known)
        available = min(capacity, *(a for a, _ in known))
        merged = dict(
            status="OBSERVED_VISIBLE_LIMITS",
            effective_available_bytes=available,
            effective_capacity_bytes=capacity,
        )
    else:
        available = capacity = None
        merged = dict(status="UNOBSERVED")
    if estimate > 512 * MIB and (len(known) != len(snapshots) or len(rss_values) != len(snapshots)):
        raise ValueError(
            "AUTO extension requires complete visible resource observations including RSS"
        )
    if estimate > 512 * MIB:
        if any(type(s.get("uncertainties")) is not list or s["uncertainties"] for s in snapshots):
            raise ValueError("Visible resource metadata unreliable;legacy512cap fallback")
        if virtual["status"] in ("OBSERVED_AVAILABLE", "OBSERVED_FINITE_REMAINING"):
            remaining = virtual.get("available_bytes")
            if type(remaining) is not int or remaining < 0:
                raise ValueError("Visible virtual headroom invalid;legacy512cap fallback")
            if available is not None:
                available = min(available, remaining)
                merged["effective_available_bytes"] = available
    outcome = tier_decide(estimate, required, merged, complete, virtual["status"])
    return outcome, available, capacity, max(rss_values) if rss_values else None


def _admitted(outcome):
    return (
        outcome["status"].startswith("LEGACY_COMPATIBILITY")
        or outcome["status"] == "VISIBLE_HEURISTIC_EXTENSION"
    )


def _legacy_diagnostics(estimate, shape):
    # This is the inherited budget domain, never a new memory safety bound.
    rows, features = shape if type(shape) is tuple and len(shape) == 2 else (None, None)
    return dict(
        required_bytes=None,
        effective_budget_bytes=512 * MIB,
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


def check_auto(model, estimate, X, y, weight, eval_set, *, shape=None):
    """Separate inherited risk compatibility from strictly qualified extension."""
    if type(estimate) is int and 0 <= estimate <= 512 * MIB:
        return _legacy_diagnostics(estimate, shape)
    started = time.perf_counter()
    rows, features = (
        shape
        if shape is not None
        else (X.shape if type(X) in (np.ndarray, pd.DataFrame) else (None, None))
    )
    dtype = str(X.dtype) if type(X) is np.ndarray else type(X).__name__
    try:
        first = _snapshot()
        virtual = observe_virtual(first)
        floor = requirement(int(estimate), 0, 0, int(features))["required_bytes"]
        quick, available, capacity, rss = _tier(int(estimate), floor, [first], True, virtual)
        if not _admitted(quick):
            raise ValueError(
                "AUTO preliminary headroom/domain admission rejected: " + quick["status"]
            )
        copied = 0
        unknown = []
        roles = [("training_X", X), ("training_y", y), ("training_weight", weight)]
        if eval_set is not None:
            roles.extend(zip(["validation_X", "validation_y"], eval_set))
        for role, value in roles:
            try:
                copied += payload(value)
            except (TypeError, ValueError, OverflowError) as error:
                unknown.append(role + ": " + str(error))
        complete = not unknown
        if not complete and estimate > 512 * MIB:
            raise ValueError(
                "Cannot auto-raise the legacy 512MiB estimate cap for an unprofiled conversion"
            )
        class_count_known = not any(role.startswith("training_y:") for role in unknown)
        k = len(pd.unique(y)) if model._task == "classification" and class_count_known else 0
        if model._task == "classification" and not class_count_known:
            unknown.append(
                "class_count: UNKNOWN;retained-head requirement is a lower bound,not zero heads"
            )
        required = requirement(
            int(estimate),
            copied,
            int(k),
            int(features),
            int(model.n_tables),
            int(model.features_per_table),
            max(int(model.n_bins) + 1, int(model.max_categories) + 3),
            int(model.table_size),
        )
        second = _snapshot()
        virtual = merge_virtual([virtual, observe_virtual(second)])
        outcome, available, capacity, rss = _tier(
            int(estimate), required["required_bytes"], [first, second], complete, virtual
        )
        if not _admitted(outcome):
            raise ValueError(
                "AUTO qualified headroom/domain admission rejected: " + outcome["status"]
            )
        budget = outcome["effective_budget_bytes"]
        assert estimate <= budget
        if not complete:
            assert budget <= 512 * MIB
        return dict(
            **required,
            effective_budget_bytes=budget,
            available_bytes=available,
            capacity_bytes=capacity,
            process_RSS_bytes=rss,
            rows=rows,
            features=features,
            dtype=dtype,
            observed_class_count=k if class_count_known else None,
            class_count_bound_known=class_count_known,
            elapsed_s=time.perf_counter() - started,
            policy="LEGACY_TIER_OR_FROZEN_CONSERVATIVE",
            model_changed=False,
            status=outcome["status"] if complete else "LEGACY_COMPATIBILITY_UNPROFILED_CONVERSION",
            tier_status=outcome["status"],
            virtual_domain=virtual["status"],
            virtual_observation=virtual,
            profile_complete=complete,
            resource_qualified=False,
            required_bytes_is_lower_bound=not complete,
            visible_resource_snapshots=[first, second],
            virtual_available_bytes=virtual.get("available_bytes"),
            unprofiled_external_inputs=unknown,
            conversion_peak_bound_known=complete,
            safety_scope="Visible heuristic or inherited512risk only;not OOM guarantee. Training custom conversion already precedes admission;validation unknown conversion is not peak-bounded.",
        )
    except (OSError, TypeError, ValueError, OverflowError) as error:
        budget = locals().get(
            "budget",
            locals().get("outcome", locals().get("quick", {})).get("effective_budget_bytes"),
        )
        if budget is None:
            budget = 512 * MIB
        need = locals().get("required", {}).get("required_bytes")
        raise ValueError(
            "AUTO memory admission rejected: "
            + str(error)
            + f"; legacy estimate={estimate / MIB:.2f}MiB, required_bytes={need}, effective_budget_bytes={budget},"
            + f" available_bytes={locals().get('available')}, capacity_bytes={locals().get('capacity')}, rows={rows}, features={features}, dtype={dtype}."
            + " No rows,precision or model capacity were changed."
        ) from error


def record_diagnostics(model, diagnostics, pre_conversion=True):
    for attribute, key in [
        ("memory_admission_available_bytes_", "available_bytes"),
        ("memory_admission_process_RSS_bytes_", "process_RSS_bytes"),
        ("memory_admission_virtual_available_bytes_", "virtual_available_bytes"),
    ]:
        setattr(model, attribute, diagnostics.get(key))
    model.memory_admission_tier_ = diagnostics["tier_status"]
    model.memory_admission_virtual_domain_ = diagnostics["virtual_domain"]
    model.memory_admission_safety_certificate_ = False
    model.effective_memory_budget_mb_ = diagnostics["effective_budget_bytes"] / MIB
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


def recheck_after_conversion(model, estimate, X, y, weight, eval_set):
    """Check actual normalized payload before training, never redo conversion."""
    diagnostics = check_auto(
        model, estimate, X, y, weight, eval_set, shape=model.memory_admission_shape_
    )
    # Unknown remainder is never called fully qualified; unchanged legacy cap
    # and conservative known floor still apply. Never invoke a hook to size it.
    record_diagnostics(model, diagnostics, pre_conversion=False)
