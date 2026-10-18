"""Read-only virtual-domain observation; absence is never unlimited."""

import sys


def observe():
    if not sys.platform.startswith(("linux", "darwin")):
        return dict(
            status="UNKNOWN", scope="No qualified stdlib virtual-cap query on this platform"
        )
    try:
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        if soft == resource.RLIM_INFINITY:
            return dict(
                status="OBSERVED_UNLIMITED",
                soft_bytes=None,
                hard_raw=hard,
                scope="Own soft RLIMIT_AS only; physical/commit/hierarchy separate",
            )
        if type(soft) is int and soft >= 0:
            return dict(
                status="OBSERVED_FINITE",
                soft_bytes=soft,
                hard_raw=hard,
                scope="Finite own virtual cap; no physical-Q-as-virtual-bound",
            )
        return dict(status="UNKNOWN", scope="Invalid soft RLIMIT_AS observation")
    except (ImportError, AttributeError, OSError, ValueError):
        return dict(status="UNKNOWN", scope="Virtual-domain observation unavailable")
