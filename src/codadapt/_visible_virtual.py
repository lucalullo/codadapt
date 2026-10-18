"""Visible own-process address-space metadata, never an OOM certificate."""

import sys


def unknown(reason):
    return dict(
        status="UNKNOWN",
        available_bytes=None,
        capacity_bytes=None,
        source_kind="UNOBSERVED",
        scope=reason,
        safety_certificate=False,
    )


def windows_virtual(snapshot):
    capacity = snapshot.get("virtual_capacity_bytes")
    available = snapshot.get("virtual_available_bytes")
    if (
        snapshot.get("platform") != "Windows"
        or type(capacity) is not int
        or type(available) is not int
    ):
        return unknown("Windows current-process virtual metadata missing")
    if capacity <= 0 or not 0 <= available <= capacity:
        return unknown("Windows current-process virtual metadata invalid")
    return dict(
        status="OBSERVED_AVAILABLE",
        available_bytes=available,
        capacity_bytes=capacity,
        source_kind="WINDOWS_CURRENT_PROCESS_VIRTUAL_AVAILABLE",
        safety_certificate=False,
        scope="Available unreserved/uncommitted address space only;not contiguous workspace,commit/RSS quota or nested ancestor certificate",
    )


def posix_virtual(soft, hard, vms, *, unlimited=False):
    if unlimited is True:
        return dict(
            status="OBSERVED_UNLIMITED",
            available_bytes=None,
            capacity_bytes=None,
            soft_bytes=None,
            hard_raw=hard,
            process_VMS_bytes=vms,
            source_kind="POSIX_OWN_RLIMIT_AS",
            safety_certificate=False,
            scope="Own soft RLIMIT_AS reports infinity;physical/commit/cgroup/hidden constraints remain separate",
        )
    if type(soft) is not int or soft < 0 or type(vms) is not int or vms < 0:
        return unknown("Finite own RLIMIT_AS remaining address space cannot be observed reliably")
    return dict(
        status="OBSERVED_FINITE_REMAINING",
        available_bytes=max(0, soft - vms),
        capacity_bytes=soft,
        soft_bytes=soft,
        hard_raw=hard,
        process_VMS_bytes=vms,
        source_kind="POSIX_OWN_RLIMIT_AS",
        safety_certificate=False,
        scope="Own soft AS limit minus current VMS;visible heuristic quantity,not physical RSS or proven future allocation envelope",
    )


def linux_vms(text):
    if len(text) > 1024**2:
        raise ValueError("Process status metadata exceeds bounded read")
    matches = [line.split() for line in text.splitlines() if line.startswith("VmSize:")]
    if len(matches) != 1 or len(matches[0]) != 3 or matches[0][2] != "kB":
        raise ValueError("Own VmSize metadata missing or malformed")
    token = matches[0][1]
    if not token.isascii() or not token.isdecimal() or len(token) > 20:
        raise ValueError("Own VmSize amount invalid")
    return int(token) * 1024


def observe(snapshot):
    if sys.platform == "win32":
        return windows_virtual(snapshot)
    if not sys.platform.startswith(("linux", "darwin")):
        return unknown("Unsupported platform")
    try:
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        if soft == resource.RLIM_INFINITY:
            return posix_virtual(soft, hard, None, unlimited=True)
        if sys.platform.startswith("linux"):
            with open("/proc/self/status", encoding="ascii") as stream:
                vms = linux_vms(stream.read(1024**2 + 1))
        else:
            # Do not silently replace VMS by ru_maxrss on a finite macOS limit.
            vms = None
        return posix_virtual(soft, hard, vms)
    except (ImportError, AttributeError, OSError, ValueError, OverflowError):
        return unknown("Own virtual metadata unavailable;legacy cap fallback required")


def merge(observations):
    if not observations:
        return unknown("No virtual observations")
    supported = {"OBSERVED_AVAILABLE", "OBSERVED_FINITE_REMAINING", "OBSERVED_UNLIMITED"}
    if any(type(o) is not dict or o.get("status") not in supported for o in observations):
        return unknown("At least one virtual observation unknown")
    sources = {o.get("source_kind") for o in observations}
    if len(sources) != 1 or None in sources:
        return unknown("Inconsistent virtual observation source")
    limited = [o for o in observations if o["status"] != "OBSERVED_UNLIMITED"]
    if not limited:
        result = dict(observations[-1])
    else:
        if any(
            type(o.get("available_bytes")) is not int
            or type(o.get("capacity_bytes")) is not int
            or not 0 <= o["available_bytes"] <= o["capacity_bytes"]
            for o in limited
        ):
            return unknown("Invalid virtual headroom observation")
        statuses = {o["status"] for o in limited}
        if len(statuses) != 1:
            return unknown("Inconsistent bounded virtual domains")
        result = dict(
            limited[-1],
            available_bytes=min(o["available_bytes"] for o in limited),
            capacity_bytes=min(o["capacity_bytes"] for o in limited),
        )
        result["available_bytes"] = min(result["available_bytes"], result["capacity_bytes"])
    result["observations"] = observations
    result["safety_certificate"] = False
    return result
