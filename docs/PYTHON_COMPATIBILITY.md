# Python compatibility and release policy

The local CodAdapt **1.1.0rc1** candidate declares **Python >=3.10,<3.15**.
Exact installed-wheel qualification covers Python 3.10–3.14 locally on Windows;
exact sdist installation is checked on Python 3.12. Numerical imports/Cholesky,
metadata, pip check, native contracts, trusted persistence and sklearn behavior
are checked against the installed artifact. Existing matching-minor numerical
stacks are reused offline in new isolated candidate environments; this is not a
fresh network resolution of every dependency or every allowed combination.

## Dependency scope

NumPy, pandas, scikit-learn, SciPy and threadpoolctl remain direct runtime
dependencies, with unchanged declared ranges. SciPy supplies native sparse-input
checks and experimental SafeBlend numerics. The optional EBM compiler pins
interpret-core==0.7.8; its teacher is required only during compilation.
Native fit and compiled inference need no external tree learner or teacher.
Optional extras may have narrower practical compatibility than the native core.

## Actual platform evidence and source binding

Frozen AUTO has scoped full-fit receipts for the original 699,635 x 21
satisfaction dataset on Windows, WSL and a real Kaggle VM, real finite-container
Docker evidence, a real nested Linux VM gate and native macOS Intel/Python 3.12.
Earlier V8 hosts qualify the unchanged extension; C1's lazy routing is bound by
source comparison and qualified contracts. The macOS C1 gate is an actual Apple
host, not simulation. RC computational sources equal the integrated C1 sources;
only the package version literal changes in this release preparation.

These receipts are not relabeled as fresh 1.1.0rc1 executions on every host or
as a full OS-by-minor matrix. WSL shares the Windows machine's hardware. Historic
maintainer-confirmed CI is separate from locally inspected machine receipts.
Future exact-RC remote release qualification is **MANUAL_GITHUB_ACTION_REQUIRED**;
no GitHub operation is performed by local preparation.

Historical Windows DLL/application-control failures occurred in standalone SciPy
before CodAdapt. They remain numerical-environment evidence, not algorithm
failures. Do not disable security controls or describe reuse of existing numerical
libraries as a fresh dependency installation. Use maintained interpreter patches;
local patch versions are qualification inputs, not security recommendations.

## Manual release gate

Local workflow definitions include representative push tests and the manual
release-qualification workflow for Windows, Linux and macOS/Python 3.10–3.14.
Definitions are prepared gates until a maintainer executes them on the exact
integrated commit. Previous-commit CI does not qualify new artifacts. Optional
compiler checks remain separate. No workflow is dispatched by local preparation.

Trusted pickle/joblib persistence is supported only within matching environments;
cross-version or cross-Python replay is diagnostic, not a permanent guarantee.
Keep exact package artifacts, hashes and dependency versions. See
[stability](STABILITY.md), [limitations](RC1_KNOWN_LIMITATIONS.md) and
[manual release instructions](RELEASING.md).
