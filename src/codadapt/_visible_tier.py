"""Explicitly noncertified visible-resource extension,with inherited fallback."""

from . import _memory_policy as old

LEGACY = 512 * old.MIB


def decide(estimate, required, observation, complete, virtual_domain, explicit=None):
    old.nonnegative(estimate, required)
    if explicit is not None:
        return old.decide("CONSERVATIVE", estimate, required, observation, explicit_MiB=explicit)
    if estimate <= LEGACY:
        return dict(
            status="LEGACY_COMPATIBILITY_EXACT_STATIC_DOMAIN",
            effective_budget_bytes=LEGACY,
            resource_qualified=False,
            visible_metadata_complete=False,
        )
    fallback = dict(
        effective_budget_bytes=LEGACY, resource_qualified=False, visible_metadata_complete=False
    )
    if not complete:
        return dict(status="REJECT_UNPROFILED_EXTENSION_LEGACY_CAP", **fallback)
    a, c = observation.get("effective_available_bytes"), observation.get("effective_capacity_bytes")
    if (
        observation.get("status") != "OBSERVED_VISIBLE_LIMITS"
        or type(a) is not int
        or type(c) is not int
        or not 0 <= a <= c
        or c <= 0
    ):
        return dict(status="REJECT_UNRELIABLE_VISIBLE_METADATA_LEGACY_CAP", **fallback)
    if virtual_domain not in {
        "OBSERVED_AVAILABLE",
        "OBSERVED_FINITE_REMAINING",
        "OBSERVED_UNLIMITED",
    }:
        return dict(status="REJECT_UNRELIABLE_VIRTUAL_METADATA_LEGACY_CAP", **fallback)
    result = old.decide("CONSERVATIVE", estimate, required, observation)
    return dict(
        status="VISIBLE_HEURISTIC_EXTENSION"
        if result["status"] == "AUTO_ADMIT"
        else result["status"],
        effective_budget_bytes=result["effective_budget_bytes"],
        resource_qualified=False,
        visible_metadata_complete=True,
        safety_certificate=False,
        scope="Conservative visible-resource heuristic only;hidden ancestor/pressure/converter/allocation-envelope risks remain",
    )
