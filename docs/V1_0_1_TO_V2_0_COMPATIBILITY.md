# Migrating to CodAdapt 2.0.0

**CodAdapt 2.0.0 — Official Stable Release.**
Prepared and fully qualified for official release.
The native algorithm, learned values and public methods retain the qualified RC1
implementation. No Next-Gen private component is integrated.

The intentional change relative to1.0.1 is the native admission default:
`memory_budget_mb="auto"`. No constructor configuration is normally required;
eligible larger inputs use conservative visible resources. To retain historical
admission use `memory_budget_mb=512`. Explicit integer MiB budgets remain hard
limits on estimated working allocation, not total process RSS. AUTO never silently
changes capacity, precision, rows or fitted predictions; unknown limits fall back
conservatively. It cannot reserve memory or guarantee no OOM under hidden limits,
custom conversions or concurrent pressure. See [AUTO_MEMORY.md](AUTO_MEMORY.md).

Supported Python remains3.10–3.14. Classifier/Regressor names, alias, input contract,
Shared OVR, sklearn methods and experimental SafeBlend/EBM APIs are unchanged.
SafeBlend's internal Base remains explicitly512MiB. No parameter is removed here.

Only trusted same-version artifacts in matching environments are supported for
pickle/joblib. A successful RC1 replay in qualification is diagnostic evidence,
not a general cross-version guarantee. Preserve exact artifacts and dependencies.
Four known sklearn XFAIL and the six RC1 limitation rows remain applicable.
Quality remains domain-dependent; no new accuracy or universal systems claim.

The2.0 version finalization followed a real-Mac PASS on the frozen public basis
and local metadata/build/install/contract qualification. Publishing to PyPI or
creating a GitHub Release remains a separate maintainer action.
