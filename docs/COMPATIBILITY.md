# Actual compatibility and backend selection

CodAdapt 2.1.0 metadata permits CPython 3.10–3.15. This is an installation
constraint, not a promise that every OS, patch and dependency set is qualified.

| Windows x64 exact profile | Actual 2.1.0 execution | Explicit C++ | Normal automatic selection |
|---|---|---|---|
| CPython 3.14.10, requirements/windows314.txt | Clean native and pure consumers; inherited full native suite 1012 PASS, 3 SKIP, 4 historical XFAIL; final affected checks separately recorded | Finite correctness and performance PASS | Python |
| CPython 3.10.22, requirements/windows310.txt | Core native and pure PASS; full suite 1002 PASS, 1 SKIP, 4 XFAIL, 12 optional EBM DLL policy errors | Core finite correctness/performance PASS; full optional profile HOLD | Python |
| CPython 3.12.10, requirements/windows312.txt | Native/pure builds; fresh runtime HOLD at blocked pandas prerequisite | Historical preserved G6-R1 evidence only | Existing guard allows native if extension/pins match; not a fresh 2.1.0 runtime PASS |
| Other available Windows patches 3.11.18, 3.12.16, 3.13.18, 3.15.2 | Existing runtime/dependency policy blockers; no changed conditions for another denied load | Not newly qualified | Python |
| Linux or macOS, x64/ARM64 | NOT TESTED: no authorized operational real environment available | Not qualified | Python; this does not establish whole-package support |

The full native suite is not a claim that the pure wheel ran every legacy test.
Its selected fallback/boundary/packaging checks and three-task/persistence probes
are separately recorded. The final targeted regressions on newly rebuilt exact
artifacts are in [the final report](../RAPPORTO_FINALE.md). The original full-suite
receipts remain historical evidence for unchanged product code, not a rerun.

An installed native wheel, an explicitly tested C++ path and an automatically
selected C++ path are different facts. The private test selector is not a stable
public estimator parameter. On 3.10/3.14 the default remains Python despite
measured explicit-native gains. [NATIVE_PROFILE_DECISION.md](NATIVE_PROFILE_DECISION.md)
contains exact pins, timings and the persistence reason for preserving the guard.
Missing-extension fallback is expected; DLL/ABI/App Control errors are not
silently relabelled as successful native execution.

## Historical and external boundaries

The preserved Windows 3.12.10 G6-R1 runtime has its own qualified automatic native
behavior. The R2 fresh consumer failed a pandas DLL import; its old full suite
used an already authorized G6-R1 runtime. Neither result qualifies a fresh final
2.1.0/3.12 runtime. Actual 2.1.0/3.14 and core 3.10 installs were executed later.
The optional 3.10 EBM error is preserved; no skip, alias or policy bypass fixes it.

The 3.11 runner selects older compatible dependency candidates because the newer
NumPy/SciPy pins require Python 3.12. Selection and build metadata are not runtime
qualification. Linux/macOS require real authorized executions. No cross-build,
CI configuration or predecessor-platform result replaces them. Retain exact
producing environments for models; [PERSISTENCE.md](PERSISTENCE.md) states limits.
