"""Frozen AUTO metadata regressions; offline fixtures are not platform qualification."""

import numpy as np
import pytest

from codadapt import CodAdaptClassifier, CodAdaptRegressor
from codadapt import _memory_admission as guard
from codadapt import _memory_policy as policy
from codadapt import _visible_tier as tier
from codadapt import _visible_virtual as virtual

MIB = 2**20
GIB = 2**30


def snapshot(a=8 * GIB, c=16 * GIB, rss=128 * MIB):
    return dict(
        platform="Windows",
        status="OBSERVED_VISIBLE_LIMITS",
        effective_available_bytes=a,
        effective_capacity_bytes=c,
        process_RSS_bytes=rss,
        uncertainties=[],
        virtual_capacity_bytes=128 * 1024 * GIB,
        virtual_available_bytes=8 * GIB,
    )


def inputs():
    return np.arange(24, dtype=float).reshape(8, 3), np.array([0, 1] * 4), np.ones(8)


def check(estimate=513 * MIB, x=None, y=None):
    X, Y, W = inputs()
    return guard.check_auto(
        CodAdaptClassifier(),
        estimate,
        X if x is None else x,
        Y if y is None else y,
        W,
        None,
        shape=(8, 3),
    )


@pytest.fixture(autouse=True)
def visible(monkeypatch):
    monkeypatch.setattr(guard, "observe", snapshot)
    monkeypatch.setattr(guard, "observe_virtual", virtual.windows_virtual)


@pytest.mark.parametrize("available", [0, 1, 1024, 8 * GIB])
def test_windows_availability_is_never_unlimited_or_a_certificate(available):
    r = virtual.windows_virtual(dict(snapshot(), virtual_available_bytes=available))
    assert r["status"] == "OBSERVED_AVAILABLE" and r["available_bytes"] == available
    assert not r["safety_certificate"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("virtual_available_bytes", None),
        ("virtual_available_bytes", -1),
        ("virtual_available_bytes", True),
        ("virtual_available_bytes", 129 * 1024 * GIB),
        ("virtual_capacity_bytes", 0),
        ("virtual_capacity_bytes", "128"),
        ("platform", "Darwin"),
    ],
)
def test_windows_invalid_or_missing_metadata_unknown(field, value):
    r = virtual.windows_virtual(dict(snapshot(), **{field: value}))
    assert r["status"] == "UNKNOWN" and r["available_bytes"] is None


@pytest.mark.parametrize(
    "soft,vms,expected",
    [(0, 0, 0), (GIB, 256 * MIB, 768 * MIB), (GIB, 2 * GIB, 0), (4 * GIB, 3 * GIB, GIB)],
)
def test_posix_finite_own_limit_remains_finite_and_uses_vms(soft, vms, expected):
    r = virtual.posix_virtual(soft, -1, vms)
    assert r["status"] == "OBSERVED_FINITE_REMAINING" and r["available_bytes"] == expected
    assert r["process_VMS_bytes"] == vms and not r["safety_certificate"]


@pytest.mark.parametrize("soft,vms", [(None, None), (-1, 0), (GIB, None), (True, 0), (GIB, -1)])
def test_unobservable_finite_posix_including_macos_no_vms_is_unknown(soft, vms):
    assert virtual.posix_virtual(soft, -1, vms)["status"] == "UNKNOWN"


def test_only_explicit_authoritative_infinity_flag_produces_unlimited():
    r = virtual.posix_virtual(-1, -1, None, unlimited=True)
    assert r["status"] == "OBSERVED_UNLIMITED" and r["available_bytes"] is None
    assert virtual.posix_virtual(-1, -1, None)["status"] == "UNKNOWN"


@pytest.mark.parametrize(
    "text,expected", [("VmSize: 1024 kB\n", MIB), ("Name: python\nVmSize:\t2097152 kB\n", 2 * GIB)]
)
def test_linux_vms_parser_units(text, expected):
    assert virtual.linux_vms(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "VmRSS: 128 kB\n",
        "VmSize: -1 kB\n",
        "VmSize: 128 bytes\n",
        "VmSize: 128 kB\nVmSize: 129 kB\n",
        "VmSize: " + "1" * 21 + " kB\n",
        "x" * (1024**2 + 1),
    ],
    ids=[
        "empty",
        "wrong_field",
        "negative",
        "wrong_units",
        "duplicate",
        "oversized_integer",
        "oversized_text",
    ],
)
def test_linux_vms_bad_or_unbounded_metadata_rejected(text):
    with pytest.raises(ValueError):
        virtual.linux_vms(text)


def test_merge_uses_minimum_available_and_keeps_original_observations():
    first = virtual.windows_virtual(snapshot())
    second = virtual.windows_virtual(dict(snapshot(), virtual_available_bytes=4 * GIB))
    r = virtual.merge([first, second])
    assert r["status"] == "OBSERVED_AVAILABLE" and r["available_bytes"] == 4 * GIB
    assert r["observations"] == [first, second] and not r["safety_certificate"]
    assert "observations" not in first and "observations" not in second


def test_newly_observed_finite_posix_limit_wins_over_unlimited():
    r = virtual.merge(
        [
            virtual.posix_virtual(-1, -1, None, unlimited=True),
            virtual.posix_virtual(4 * GIB, -1, 3 * GIB),
        ]
    )
    assert r["status"] == "OBSERVED_FINITE_REMAINING" and r["available_bytes"] == GIB


@pytest.mark.parametrize("which", [0, 1])
def test_any_unknown_virtual_observation_blocks_extension(monkeypatch, which):
    seq = [virtual.windows_virtual(snapshot()), virtual.unknown("controlled metadata absence")]
    if which == 0:
        seq.reverse()
    it = iter(seq)
    monkeypatch.setattr(guard, "observe_virtual", lambda s: next(it))
    with pytest.raises(ValueError, match="VIRTUAL_METADATA"):
        check()


def test_different_virtual_sources_cannot_be_combined():
    r = virtual.merge(
        [virtual.windows_virtual(snapshot()), virtual.posix_virtual(-1, -1, None, unlimited=True)]
    )
    assert r["status"] == "UNKNOWN"


@pytest.mark.parametrize(
    "domain", ["OBSERVED_AVAILABLE", "OBSERVED_FINITE_REMAINING", "OBSERVED_UNLIMITED"]
)
def test_fixed_conservative_policy_exact_boundary_for_visible_domains(domain):
    obs = snapshot(4 * GIB, 8 * GIB)
    budget = policy.budget("CONSERVATIVE", 4 * GIB, 8 * GIB)
    assert budget == GIB
    good = tier.decide(513 * MIB, budget, obs, True, domain)
    bad = tier.decide(513 * MIB, budget + 1, obs, True, domain)
    assert good["status"] == "VISIBLE_HEURISTIC_EXTENSION" and not good["resource_qualified"]
    assert (
        bad["status"] == "REJECT_INSUFFICIENT_HEADROOM" and bad["effective_budget_bytes"] == budget
    )


@pytest.mark.parametrize("estimate", [512 * MIB + 1, 513 * MIB])
def test_real_extension_sentinel_uses_complete_visible_snapshot_and_q(estimate):
    r = check(estimate)
    assert (
        r["tier_status"] == "VISIBLE_HEURISTIC_EXTENSION"
        and r["virtual_domain"] == "OBSERVED_AVAILABLE"
    )
    assert r["required_bytes"] == estimate + 256 * MIB and r["effective_budget_bytes"] == 2 * GIB
    assert r["profile_complete"] and not r["resource_qualified"]
    assert (
        len(r["visible_resource_snapshots"]) == len(r["virtual_observation"]["observations"]) == 2
    )


@pytest.mark.parametrize("a", [0, 1024, 256 * MIB, GIB, 2 * GIB])
def test_low_visible_headroom_rejects_without_changing_model(monkeypatch, a):
    monkeypatch.setattr(guard, "observe", lambda: snapshot(a))
    with pytest.raises(ValueError, match="INSUFFICIENT_HEADROOM"):
        check()


@pytest.mark.parametrize("uncertainty", [None, "unknown", ["missing cgroup usage"]])
def test_unreliable_resource_metadata_falls_back_to_legacy_cap(monkeypatch, uncertainty):
    monkeypatch.setattr(guard, "observe", lambda: dict(snapshot(), uncertainties=uncertainty))
    with pytest.raises(ValueError, match="legacy512cap fallback") as e:
        check()
    assert "effective_budget_bytes=536870912" in str(e.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "UNOBSERVED"),
        ("process_RSS_bytes", None),
        ("effective_available_bytes", True),
        ("effective_available_bytes", 17 * GIB),
        ("effective_capacity_bytes", 0),
    ],
)
def test_incomplete_or_invalid_visible_observation_cannot_expand(monkeypatch, field, value):
    monkeypatch.setattr(guard, "observe", lambda: dict(snapshot(), **{field: value}))
    with pytest.raises(ValueError):
        check()


def test_snapshot_minimum_and_no_second_rss_subtraction(monkeypatch):
    seq = iter([snapshot(8 * GIB, 16 * GIB, 128 * MIB), snapshot(6 * GIB, 12 * GIB, 3 * GIB)])
    monkeypatch.setattr(guard, "observe", lambda: next(seq))
    r = check()
    assert r["available_bytes"] == 6 * GIB and r["capacity_bytes"] == 12 * GIB
    assert r["process_RSS_bytes"] == 3 * GIB and r["effective_budget_bytes"] == 6 * GIB // 4


def test_minimum_virtual_availability_also_restricts_the_final_snapshot(monkeypatch):
    seq = iter([snapshot(), dict(snapshot(), virtual_available_bytes=4 * GIB)])
    monkeypatch.setattr(guard, "observe", lambda: next(seq))
    r = check()
    assert r["available_bytes"] == 4 * GIB and r["virtual_available_bytes"] == 4 * GIB
    assert r["effective_budget_bytes"] == GIB


class Opaque:
    def fail(self, *a, **k):
        pytest.fail("New opaque callback forbidden")

    __array__ = __len__ = __bool__ = __hash__ = __sizeof__ = fail
    shape = property(fail)
    dtype = property(fail)


def test_legacy_integration_still_skips_all_input_and_resource_queries(monkeypatch):
    def fail(*a, **k):
        pytest.fail("Legacy queried new metadata")

    monkeypatch.setattr(guard, "observe", fail)
    monkeypatch.setattr(guard, "observe_virtual", fail)
    monkeypatch.setattr(guard, "payload", fail)
    x = Opaque()
    m = CodAdaptClassifier()
    r = guard.check_auto(m, 512 * MIB, x, x, x, x, shape=(8, 3))
    guard.record_diagnostics(m, r)
    assert m.effective_memory_budget_mb_ == 512 and m.memory_admission_available_bytes_ is None
    assert not m.memory_admission_safety_certificate_ and r["required_bytes"] is None


def test_untrusted_payload_cannot_expand_legacy_cap():
    with pytest.raises(ValueError, match="Cannot auto-raise"):
        check(x=Opaque())


@pytest.mark.parametrize("estimator", [CodAdaptClassifier, CodAdaptRegressor])
@pytest.mark.parametrize("budget", [512, 1024])
def test_explicit_hard_estimate_cap_never_overridden_or_queries_auto(
    monkeypatch, estimator, budget
):
    monkeypatch.setattr(
        guard, "check_auto", lambda *a, **k: pytest.fail("Explicit budget queried AUTO")
    )
    m = estimator(memory_budget_mb=budget)
    if budget == 512:
        with pytest.raises(ValueError, match="exceeds"):
            m._check_memory_budget(699635, 21)
    else:
        assert m._check_memory_budget(699635, 21) == 655065376
