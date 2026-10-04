# Python compatibility and release policy

Every CodAdapt release must pass `PYTHON_COMPATIBILITY_GATE` before publication.
Executed tests establish support; classifiers, resolver success or an available
wheel alone do not. Review the matrix every release, prioritize mainstream Python
and evaluate the newest stable CPython practical for dependencies. Keep older
minors when maintenance is reasonable. Beta/RC/dev interpreters are diagnostic
only. Optional extras may have narrower support without limiting the native core.

## Current 0.2.0rc2 compatibility matrix

The current repository declares `>=3.10,<3.15`. Compatibility work is incorporated
into the existing version line; no new release is created. The older published
`v0.2.0rc2` tag retains its original metadata and does not contain this update.

| Python | Core | EBM |
| --- | --- | --- |
| 3.10 | PASS | PASS |
| 3.11 | PASS | PASS |
| 3.12 | PASS | PASS |
| 3.13 | PASS | PASS |
| 3.14 | PASS | PASS |

These are **direct local validation** results. Tested Windows interpreters were
3.10.11, 3.11.9, 3.12.14, 3.13.16 and 3.14.8; WSL 3.12.3 was also tested. Valid 3.12
receipts were reused. Both new minors passed installed-wheel full suites, including
the then-current core, EBM and packaging. These are historical compatibility receipts; native SafeBlend has a separate integration validation. The 3.13 audit recovered only one environmental
packaging failure by shortening its Windows temporary path. Each final suite had
404 passed, two conditional skips and four existing XFAIL, with no unresolved failure.
The rebuilt current-version wheel also passed a fresh full run on each new minor:
404 passed, two conditional skips and four existing XFAIL on both 3.13 and 3.14.
New package environments reused the validated numerical dependency paths; they
installed CodAdapt locally with their own package provenance and metadata checked.

All five minors are configured in separate core, EBM compiler and native SafeBlend CI jobs. Native SafeBlend is additionally checked locally on 3.12–3.14 with installed wheels and no external ML packages.
**GitHub CI confirmation is pending:** preparing the workflow and running local
tests does not establish an actual remote CI pass. Kaggle confirmation is separate.

The official inventory lists **3.14.8 as the newest stable** and 3.15 as prerelease
([Python.org](https://www.python.org/downloads/)). The old 3.10/3.11 patches are the
available official Windows binaries used for isolated checks; they are not a
recommendation to deploy obsolete security patches. Prefer current maintained
releases. Local Windows/WSL tests share one physical host.

| Stack | NumPy | SciPy | pandas | scikit-learn |
| --- | --- | --- | --- |
| Core minimum, 3.10 | 1.24.0 | 1.8.0 | 2.0.0 | 1.4.0 |
| Optional extras, 3.10 | 2.2.6 | 1.15.3 | 2.3.3 | 1.7.2 |
| Recent, 3.11 and reused 3.12 | 2.3.5 | 1.16.2 | 2.2.3 | 1.8.0 |
| Modern, 3.13/3.14 and reused WSL 3.12 | 2.5.3 | 1.18.1 | 2.3.3 | 1.9.0 |

The optional compiler/import tool keeps **interpret-core 0.7.8**; no external model is required by native training. Validation uses
joblib 1.6.0, pytest 9.1.1 and threadpoolctl 3.7.0. These are tested stacks, not a claim
that each is the latest release. EBM requires newer NumPy/sklearn than the core
floor; install its extra rather than forcing core-minimum constraints on it.
The core neither imports nor needs a teacher for fit, validation, prediction or persistence.

The sklearn minimum is now **1.4**. Under 1.3.0, two official pickle checks attempted
NaN insertion into integer input before estimator fit. Direct pickle/joblib tests
passed, but the full minimum gate failed. No model change or new XFAIL was added;
the replacement minimum passed. The original failure is retained in the audit.

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
cells or native validation protocols. SafeBlend is a separate fully native, opt-in experimental regression estimator. The public version
remains 0.2.0rc2; this update creates no tag, publication or remote release.
