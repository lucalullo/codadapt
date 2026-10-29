# Final technical revision: evidence and limits

The final source uses the exact prior 2.1.0 Python/C++ product and serving contract.
Changes repair qualification tooling and tests, clarify backend documentation and
finalize historical-path decisions. No training or prediction strategy changes.

Before assembly, affected receipt checks passed on Windows3.14 before normal
imports (26 tests), after actual imports generated package bytecode (17 tests),
and on Windows3.10 after actual imports (26 tests). These 69 executions are not
69 distinct tests or a new full-platform qualification. A shared identity helper
excludes only __pycache__ directories; unknown non-cache files, standalone.pyc,
source/native edits and qualification-input edits remain bound and rejected.

The previous full actual 2.1.0 native-consumer suite remains valid for unchanged
product code: Windows3.14,1012PASS/3SKIP/4historicalXFAIL. Windows3.10 had1002PASS,
1SKIP,4XFAIL and12 optional EBM DLL policy errors. Core checks passed separately;
the full optional3.10 profile remains HOLD. Pure consumers had47PASS/51expected
native-absence skips in the selected boundary/packaging suite, plus three-task
and persistence probes. These inherited runs are not labelled as newly executed.

The final archives are rebuilt after affected build inputs are frozen. Native
wheels are compiled from the actual sdists. New exact-wheel clean consumers run
affected tests, import/API/three-task examples, no-fit old-model replay and saved
2.1.0 serving images. Current counts, hashes and results are issued after execution
in [RAPPORTO_FINALE.md](../RAPPORTO_FINALE.md) and qualification/GATES.json. This
document does not assert a not-yet-run result. Post-build reports and manifests
are separate from the build snapshot to avoid a circular self-hash claim.

All 59 historical paths have individual decisions; 38 absent old paths require owner
approval, including4oldworkflows. No real repository was accessed or changed.
Source/wheel integrity proves consistency against a trusted manifest, not sender
authentication. Backup independence, untested platforms and policy-blocked
components remain open. [COMPATIBILITY.md](COMPATIBILITY.md) and
[NATIVE_PROFILE_DECISION.md](NATIVE_PROFILE_DECISION.md) distinguish explicit
native performance from unchanged automatic dispatch. RELEASE=HOLD.
