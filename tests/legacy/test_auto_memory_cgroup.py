"""Offline cgroup parser/policy regressions, not real container evidence."""

import numpy as np
import pytest

from codadapt import CodAdaptClassifier
from codadapt import _memory_admission as guard
from codadapt import _resource_snapshot as resource
from codadapt import _visible_virtual as virtual

GIB = 2**30
MIB = 2**20


def files(version="v2", limit=8 * GIB, usage=GIB, parent_limit=None):
    membership = "0::/tenant/worker" if version == "v2" else "7:memory:/tenant/worker"
    kind = "cgroup2" if version == "v2" else "cgroup"
    flags = "rw" if version == "v2" else "rw,memory"
    raw = {
        "/proc/meminfo": f"MemTotal: {16 * GIB // 1024} kB\nMemAvailable: {12 * GIB // 1024} kB\n",
        "/proc/self/status": f"VmRSS: {128 * MIB // 1024} kB\n",
        "/proc/self/cgroup": membership + "\n",
        "/proc/self/mountinfo": f"36 25 0:32 / /sys/fs/cgroup rw - {kind} cgroup {flags}\n",
    }
    prefix = "memory.max" if version == "v2" else "memory.limit_in_bytes"
    used = "memory.current" if version == "v2" else "memory.usage_in_bytes"
    unlimited = "max" if version == "v2" else str(2**63 - 4096)
    for folder, c, u in [
        ("tenant/worker", limit, usage),
        ("tenant", parent_limit, GIB),
        ("", None, 0),
    ]:
        root = "/sys/fs/cgroup" + ("/" + folder if folder else "")
        raw[root + "/" + prefix] = str(c) if c is not None else unlimited
        raw[root + "/" + used] = str(u)
    return raw


def snapshot(raw):
    def read(path):
        if path not in raw:
            raise FileNotFoundError(path)
        value = raw[path]
        if isinstance(value, Exception):
            raise value
        return value

    return resource.linux(read)


def integrate(monkeypatch, observations):
    stream = iter(observations)
    monkeypatch.setattr(guard, "observe", lambda: next(stream))
    monkeypatch.setattr(
        guard, "observe_virtual", lambda s: virtual.posix_virtual(-1, -1, None, unlimited=True)
    )
    return guard.check_auto(
        CodAdaptClassifier(),
        513 * MIB,
        np.ones((8, 3)),
        np.array([0, 1] * 4),
        np.ones(8),
        None,
        shape=(8, 3),
    )


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_visible_container_capacity_admits_without_double_rss_subtraction(monkeypatch, version):
    observed = snapshot(files(version))
    result = integrate(monkeypatch, [observed, observed])
    assert (
        observed["effective_capacity_bytes"] == 8 * GIB
        and observed["effective_available_bytes"] == 7 * GIB
    )
    assert result["available_bytes"] == 7 * GIB and result["effective_budget_bytes"] == 7 * GIB // 4
    assert result["process_RSS_bytes"] == 128 * MIB and not result["resource_qualified"]


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize(
    "limit,usage,parent", [(4 * GIB, GIB, None), (8 * GIB, GIB, 3 * GIB), (8 * GIB, 7 * GIB, None)]
)
def test_actual_parsed_visible_limits_restrict_v8_not_host_only_budget(
    monkeypatch, version, limit, usage, parent
):
    observed = snapshot(files(version, limit, usage, parent))
    assert observed["effective_capacity_bytes"] <= 8 * GIB
    with pytest.raises(ValueError, match="INSUFFICIENT_HEADROOM"):
        integrate(monkeypatch, [observed, observed])


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize(
    "bad", [None, PermissionError("controlled"), "-1", "bad", "18446744073709551616"]
)
def test_unreliable_cgroup_usage_never_expands_legacy_cap(monkeypatch, version, bad):
    raw = files(version)
    key = "/sys/fs/cgroup/tenant/worker/" + (
        "memory.current" if version == "v2" else "memory.usage_in_bytes"
    )
    if bad is None:
        del raw[key]
    else:
        raw[key] = bad
    observed = snapshot(raw)
    assert observed["status"] == "INCOMPLETE" and observed["uncertainties"]
    with pytest.raises(ValueError, match="effective_budget_bytes=536870912"):
        integrate(monkeypatch, [observed, observed])


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_pressure_in_second_cgroup_snapshot_blocks_extension(monkeypatch, version):
    first = snapshot(files(version))
    second = snapshot(files(version, usage=7 * GIB))
    with pytest.raises(ValueError, match="INSUFFICIENT_HEADROOM"):
        integrate(monkeypatch, [first, second])


def test_visible_namespace_boundary_retains_hidden_ancestor_limitation():
    raw = files()
    raw["/proc/self/mountinfo"] = "36 25 0:32 /tenant /sys/fs/cgroup rw - cgroup2 cgroup rw\n"
    raw["/sys/fs/cgroup/worker/memory.max"] = str(8 * GIB)
    raw["/sys/fs/cgroup/worker/memory.current"] = str(GIB)
    observed = snapshot(raw)
    assert observed["status"] == "OBSERVED_VISIBLE_LIMITS"
    assert any("hidden" in note for note in observed["scope_notes"])
    assert not observed["policy_qualified"]
