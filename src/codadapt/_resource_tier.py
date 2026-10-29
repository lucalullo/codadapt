"""Private copied pure contract; no dependency on research code."""

from . import _memory_policy as old

LEGACY = 512 * old.MIB


def decide(estimate, required, observation, complete, virtual_domain, explicit=None):
    old.nonnegative(estimate, required)
    if explicit is not None:
        return old.decide("CONSERVATIVE", estimate, required, observation, explicit_MiB=explicit)
    a, c = (
        observation.get("effective_available_bytes"),
        observation.get("effective_capacity_bytes"),
    )
    observed = (
        observation.get("status") == "OBSERVED_VISIBLE_LIMITS"
        and type(a) is int
        and (type(c) is int)
        and (0 <= a <= c)
        and (c > 0)
    )
    if estimate <= LEGACY:
        if observed and required > a:
            return dict(
                status="REJECT_KNOWN_PRESSURE",
                effective_budget_bytes=min(LEGACY, a),
                resource_qualified=False,
            )
        return dict(
            status="LEGACY_COMPATIBILITY_VISIBLE_HEADROOM"
            if observed
            else "LEGACY_COMPATIBILITY_RESOURCE_UNKNOWN",
            effective_budget_bytes=min(LEGACY, a) if observed else LEGACY,
            resource_qualified=False,
        )
    if not complete:
        return dict(
            status="REJECT_UNPROFILED_EXTENSION",
            effective_budget_bytes=None,
            resource_qualified=False,
        )
    if not observed:
        return dict(
            status="REJECT_UNKNOWN_RESOURCE_EXTENSION",
            effective_budget_bytes=None,
            resource_qualified=False,
        )
    if virtual_domain != "OBSERVED_UNLIMITED":
        return dict(
            status="REJECT_UNQUALIFIED_VIRTUAL_DOMAIN_EXTENSION",
            effective_budget_bytes=None,
            resource_qualified=False,
        )
    result = old.decide("CONSERVATIVE", estimate, required, observation)
    return dict(
        status="VISIBLE_HEURISTIC_EXTENSION"
        if result["status"] == "AUTO_ADMIT"
        else result["status"],
        effective_budget_bytes=result["effective_budget_bytes"],
        resource_qualified=False,
        visible_resource_heuristic_only=result["resource_qualified"],
    )
