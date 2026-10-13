# Python compatibility and release policy

Every CodAdapt release must pass `PYTHON_COMPATIBILITY_GATE` before publication.
Executed tests establish support; classifiers, resolver success or an available
wheel alone do not. Review the matrix every release, prioritize mainstream Python
and evaluate the newest stable CPython practical for dependencies. Keep older
minors when maintenance is reasonable. Beta/RC/dev interpreters are diagnostic
only. Optional extras may have narrower support without limiting the native core.

## Source policy and evidence boundaries

Metadata declares **>=3.10,<3.15**. The five minors are the qualification target;
an allowed dependency range is not a claim that every combination has been tested.
SciPy is a **direct runtime dependency**, used by native sparse-input checks and
SafeBlend numerical optimization; it is neither optional nor dev-only. threadpoolctl
is a direct lightweight runtime dependency, also required transitively by sklearn.
The optional EBM compiler alone uses `interpret-core==0.7.8`.

Prior local checks covered Windows 3.10.11, 3.11.9, 3.12.14, 3.13.16 and 3.14.8,
plus WSL 3.12.3 on the same physical host. They are historical receipts, not fresh
qualification of every later source edit. In the most recent exec-removal audit,
new Windows 3.13/3.14 environments encountered an OS application-control DLL block
while importing standalone SciPy, before CodAdapt. Functional checks using previously
qualified numerical dependency directories passed. **Those checks are not clean
dependency installs.** Do not disable OS security policy or infer a CodAdapt failure.

Fresh wheel/sdist installs, standalone numerical imports/Cholesky and installed-package
tests are release gates. Local environmental blocks remain ENVIRONMENT_LIMITATION
until equivalent clean CI succeeds. A previously user-confirmed remote CI PASS belongs
to its recorded public commit, not to newer local files.

Fast CI covers representative old/new Python and optional EBM. The manual
`release-qualification.yml` covers all five minors on Windows, Ubuntu and macOS,
with wheel/sdist installs and installed-wheel suites. These workflow definitions
are **prepared gates**, not evidence of execution. macOS and independent hardware
remain unqualified locally. No new remote run or hosted-image qualification is claimed.

Use maintained interpreter patches in deployment; available local interpreter patches
are test inputs, not security recommendations. Optional EBM may require newer NumPy
and sklearn than core-minimum versions. Native training and saved compiled inference
do not import interpret/LightGBM/XGBoost/CatBoost.

## Mandatory gate

Each release tests the oldest, middle, all supported mainstream and newest practical
stable minor; preferably include every supported minor in CI. Execute minimum and
modern numerical stacks. Verify native imports, NumPy/pandas, classifier/regressor,
categorical/missing inputs, clone, pipeline/CV and trusted pickle/joblib. Build
wheel/sdist, install outside the source tree into clean environments, check package
provenance and run the full public suite.

Test the optional EBM compiler separately for compilation, fidelity and teacher-free
reload. Native tests must also pass with interpret, LightGBM, XGBoost and CatBoost
physically absent. Print interpreter/dependency versions and thread pools. Distinguish
environmental DLL/backend failures from estimator failures.

Compiler dependency changes need separate fidelity validation. Preserve previous
release archives and scientific evidence; do not refit research panels for packaging.
Metadata/classifiers and docs must match executed evidence.

## Kaggle and persistence

The user reports Kaggle 3.13.15. Local 3.13.16 checks do not validate that exact patch
or image. Keep **KAGGLE_REMOTE_CONFIRMATION_PENDING** until the manual smoke runs
there. The historical tag and older wheels retain their `<3.13` restriction.
Use updated `main` after manual upload, or the rebuilt current local wheel. Do not
bypass `requires-python` or assume that an older artifact with the same name is updated.

Cross-Python pickle/joblib is diagnostic, not an official portability contract.
Prefer matching interpreter/dependency versions and load only trusted artifacts.
Teacher-free inference remains supported; cross-minor compatibility cannot be
inferred from one successful transfer.

Compatibility work does not alter native fitting, prediction semantics, compiler
cells or native validation protocols. SafeBlend is a separate fully native, opt-in
experimental regression estimator. The current candidate source version is
**1.0.0rc2**, not stable 1.0.0. Candidate preparation creates no tag, publication or
remote release. RC2 artifacts require fresh version/provenance/install checks on
each available minor; old commit CI does not qualify this new candidate. The full
remote release matrix, including macOS, remains a maintainer-only external gate.
