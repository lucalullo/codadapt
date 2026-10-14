# Python compatibility and release policy

CodAdapt1.0.0 declares **Python>=3.10,<3.15** and qualifies minors3.10–3.14.
Metadata/resolver success alone does not prove execution. Each release requires
installed-artifact numerical imports/Cholesky, pip check, native binary/multiclass/
regression, categorical/missing inputs, clone/Pipeline/CV, memory admission and
trusted persistence checks. Test minimum and modern numerical stacks; no claim
that every allowed dependency combination has been executed.

## Dependency scope

NumPy, pandas, scikit-learn, SciPy and threadpoolctl are direct runtime dependencies.
SciPy is required for native sparse-input checks and SafeBlend numerics. The optional
EBM compiler pins interpret-core==0.7.8; the teacher is needed only during compilation.
Native fit and compiled inference require no interpret/LightGBM/XGBoost/CatBoost model.
Optional extras may have narrower practical compatibility than the native core.

## Evidence and platform boundaries

RC2 Windows/Linux/macOS, Python3.10–3.14 and full remote release qualification PASS
were reported by the maintainer. They are RC2 context, not remotely queried evidence
or execution of stable1.0.0 workflows. Local stable qualification records exact
artifact hashes/interpreters/dependency versions separately. Available local Windows
minors and WSL installed-wheel checks are exercised; WSL is the same hardware.
Stable macOS and the post-integration remote matrix remain **EXTERNAL_MANUAL_GATE**.
No local macOS or independent-hardware execution is simulated.

Historical Windows DLL/application-control failures occurred in standalone SciPy
before CodAdapt. Preserve their receipts as numerical-environment limitations; do
not disable OS security controls or label them algorithm failures. A source workaround
that reuses old numerical directories is not a fresh dependency installation.
Stable qualification distinguishes those cases explicitly if they recur.

## Release gate

Fast tests.yml covers representative old/new Python and optional EBM. The manual
release-qualification.yml covers all five minors on Windows, Ubuntu and macOS,
wheel/sdist installs and installed-wheel suites. Optional compiler gates are separate.
Workflow definitions are prepared gates until the maintainer executes them against
the integrated stable commit. Previous-commit CI does not qualify new artifacts.

Use maintained interpreter patches in deployment; local patches are test inputs,
not security recommendations. Hosted Kaggle/Colab images need their own installed-
package smoke; local tests do not qualify those images. Cross-Python pickle/joblib
loading remains diagnostic, not guaranteed. Prefer matching environments.

No scientific recipe, numerical precision, compiler cells or native validation
protocol changes accompany stable version finalization. Release uploads, tags and
workflow execution are maintainer-only actions; preparation performs none of them.
