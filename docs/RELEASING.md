# Preparing and releasing CodAdapt 1.1.0rc1

This is a manual handoff procedure. The local 1.1.0rc1 candidate is prepared from
frozen C1 with release-only version/documentation changes. Preparation never
modifies the GitHub clone or invokes GitHub, TestPyPI, PyPI, tags or workflows.
Local readiness does not authorize publication or stable 1.1 promotion.

## Local evidence

1. Freeze exact computational source, tests, API/default migration and claims.
2. Build wheel/sdist from a clean public-only snapshot; audit metadata, license,
   archive contents, private-file exclusion and high-confidence secret patterns.
3. Run Ruff, formatting, the installed-RC public suite, Twine, clean package
   installs, pip check and installed-artifact smokes. Preserve four known scope
   XFAIL and distinguish them from failures.
4. Qualify Python 3.10–3.14 wheel and primary Python 3.12 sdist. Record existing
   offline numerical stack reuse and actual interpreter/dependency versions.
5. Exercise binary/multiclass/regression, SafeBlend, AUTO/explicit budgets,
   failure atomicity, clone/Pipeline/CV, examples/notebook and fresh-process trusted
   pickle/joblib. Cross-version replay remains diagnostic, not guaranteed.
6. Bind real platform receipts to C1 through explicit source lineage. Do not
   relabel prior V8 or C1 hosts as new exact-RC host executions.
7. Record exact changed public paths, hashes, wheel/sdist and test receipts in
   RC1_RELEASE_MANIFEST.json and RC1_MANUAL_GITHUB_HANDOFF.md under the private
   local release-preparation folder. Research memory is tracked in the source
   repository but excluded from distributions; research_private is never copied.

## Maintainer-only actions, after separate approval

1. Manually copy only the handoff's public paths from the Desktop workspace to
   the real clone. Compare each SHA256 and review the exact diff; do not copy
   private evidence, caches, environments or build outputs into source control.
2. Manually commit/push and record the resulting commit. Obtain push CI PASS.
3. Manually run `Manual release qualification (no publishing)` on that exact
   commit, including the Windows/Linux/macOS and Python 3.10–3.14 matrix. This is
   an external manual gate, not a local failure when unexecuted.
4. After explicit authorization and trusted-publisher configuration, manually run
   the TestPyPI workflow for 1.1.0rc1. Inspect the exact artifacts/hashes. Never
   overwrite a published version, add source secrets or enable automatic publishing.
5. In a fresh external environment, preinstall declared dependencies from the
   trusted production index. Install the explicit TestPyPI candidate with
   `--no-deps --pre --index-url https://test.pypi.org/simple/ codadapt==1.1.0rc1`.
   Avoid mixed-index dependency resolution. Run pip check, import/version, binary,
   multiclass, regression, SafeBlend, AUTO large-N and persistence smokes.
6. Review uploaded README/metadata, failure behavior and observation feedback.
   TestPyPI success does not itself authorize production upload, a tag, GitHub
   Release or stable 1.1. A new decision is required for each publication step.

The future general prerelease install command is
`python -m pip install --pre codadapt==1.1.0rc1`, only after the intended index
contains the approved candidate. See the private RC1_TESTPYPI_PLAN.md for exact
manual smoke commands and the original real-data acceptance case.

## Claim lock and limitations

Resource-aware admission is eligible-domain admission, not guaranteed memory
safety. Explicit integers cap estimated E, not RSS. Qualified C1 matched fit ratio
is approximately 0.997x; ndarray inference approximately 0.808x; categorical pickle
approximately 0.748x. Each belongs to its own protocol. No universal speed, size,
RAM or predictive-quality advantage is claimed. Preserve mixed blind results and
compact-specialist SafeBlend positioning. Original real satisfaction-data full
fits are scoped platform evidence, not validation of every 700k-row dataset.

Retain all positive/negative receipts and known limitations. A CRITICAL/HIGH
runtime/product issue blocks readiness. See [migration](V1_0_1_TO_V1_1_0RC1_COMPATIBILITY.md),
[limitations](RC1_KNOWN_LIMITATIONS.md), [AUTO](AUTO_MEMORY.md) and
[Python compatibility](PYTHON_COMPATIBILITY.md).
