"""Private pure counterfactual policy; no allocation, model fit or public API."""

MIB = 2**20
GIB = 2**30
POLICIES = {
    "CONSERVATIVE": (1, 4, 1, 4, 1024 * MIB),
    "BALANCED": (1, 3, 1, 4, 1024 * MIB),
    "RESPONSIVE": (1, 2, 1, 3, 2048 * MIB),
}


def nonnegative(*values):
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("Policy amounts must be nonnegative Python integers")


def requirement(estimate, copy_payload, k, p, tables=8, features=3, bins=131, size=256):
    nonnegative(estimate, copy_payload, k, p, tables, features, bins, size)
    head = 8 * p * bins + tables * (8 * size + features * (2 * bins + 8))
    head += 2048 * (p + tables * (features + 2))
    retained = 8 * k * 3 * head if k > 2 else 0
    return dict(
        legacy_estimate=estimate,
        copy_payload=copy_payload,
        packing_retained_allowance=retained,
        fixed_uncertainty_allowance=256 * MIB,
        required_bytes=max(estimate, 2 * copy_payload) + 256 * MIB + retained,
        safety_certificate=False,
    )


def budget(policy, available, capacity):
    nonnegative(available, capacity)
    if available > capacity or capacity == 0:
        raise ValueError("Invalid effective headroom/capacity pair")
    an, ad, cn, cd, reserve = POLICIES[policy]
    return max(0, min(available * an // ad, capacity * cn // cd, available - reserve))


def decide(policy, estimate, required, observation, profile_complete=True, explicit_MiB=None):
    nonnegative(estimate, required)
    if explicit_MiB is not None:
        nonnegative(explicit_MiB)
        if explicit_MiB < 1:
            raise ValueError("Explicit budget must be positive")
        limit = explicit_MiB * MIB
        return dict(
            status="EXPLICIT_ADMIT" if estimate <= limit else "EXPLICIT_REJECT",
            effective_budget_bytes=limit,
            resource_qualified=False,
        )
    if not profile_complete:
        return dict(
            status="REJECT_UNQUALIFIED_PROFILE",
            effective_budget_bytes=None,
            resource_qualified=False,
        )
    if observation.get("status") != "OBSERVED_VISIBLE_LIMITS":
        return dict(
            status="LEGACY_FALLBACK_ADMIT" if estimate <= 512 * MIB else "REJECT_RESOURCE_UNKNOWN",
            effective_budget_bytes=512 * MIB,
            resource_qualified=False,
        )
    a, c = observation.get("effective_available_bytes"), observation.get("effective_capacity_bytes")
    limit = budget(policy, a, c)
    return dict(
        status="AUTO_ADMIT" if required <= limit else "REJECT_INSUFFICIENT_HEADROOM",
        effective_budget_bytes=limit,
        resource_qualified=True,
    )
