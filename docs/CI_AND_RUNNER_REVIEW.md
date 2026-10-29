# Qualification runner and manual CI

This workflow is manual and executes one selected OS/Python/backend job. It has
read-only repository permission, no publishing step, an explicit job deadline,
and a concurrency key that does not interrupt another qualification. Workflow
declaration and dependency resolution are not platform qualification.

Run the Python tool only in an authorized development interpreter with
`psutil==7.2.2` installed. The manual CI bootstraps this dependency from official
PyPI; local offline users can install the same wheel from their authorized
wheelhouse. No administrator privilege, account or security change is needed.

The runner limits each stage to 300 seconds, the complete run to 1800 seconds,
and sampled aggregate RSS of its recorded owned subprocess tree to 1.5GiB.
It records PID birth identities, sampled peak RSS, timeout/limit reasons and
cleanup of recorded descendants. Sampling is not a proof that every instantaneous
peak or a deliberately detached process is observable. Normal build/test child
processes remain owned; unrelated processes are never scanned or stopped.

Python3.11 cannot use the former NumPy2.5.4/SciPy1.18.1 profile: both official
wheel METADATA require Python>=3.12. It now uses the older explicit pinned stack
as an untested dependency candidate. All targets resolve actual binary wheels
with pip dry-run and preserve the report before build/install. Unsupported or
unavailable versions fail with evidence; they are not converted into skips or
support claims. Newer minors/OS still require real execution.

Schema2 receipts bind product source plus tools, tests, build configuration and
requirement file hashes. The checker accepts older schema1 consistent receipts,
requires the additional identities and preflight stage for schema2, and rejects
duplicate stages. A functional PASS is reported separately from the finite
performance guard. A timing failure is HOLD, never an automatic native/platform
promotion. Every platform requires review of all tests, skips and metrics.

The command uses the default pytest selection, which must include native,
legacy and tools in the candidate pyproject. The documented legacy packaging
path-injection exclusion must remain explicit in pytest addopts. Its replacement
is the clean consumer install/probe, not a relabelled historical PASS.
