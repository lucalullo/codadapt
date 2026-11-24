# Compatibility

## Package and locally verified profiles

CodAdapt 2.2.0 builds a **pure-Python wheel** and declares Python **>=3.12**.
The declaration is an installation constraint, not proof that every later
Python or dependency combination works.

| Profile | Evidence from this revision |
|---|---|
| Windows 11 x64, CPython 3.12.10, NumPy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0, SciPy 1.17.0 | All 143 supplied tests pass. Restored regression suite: 861 pass, four original strict expected failures. Optional EBM integration uses interpret-core 0.7.8. |
| Windows 11 x64, CPython 3.12.10, NumPy 2.5.4, pandas 3.1.0, scikit-learn 1.9.1, SciPy 1.18.1 | Supplied suite: 141 pass; two tests specific to pandas 2.2.3 are skipped by their existing version condition. |
| GitHub-hosted Ubuntu 24.04 and Windows, CPython 3.12/3.13 | Workflows prepared and locally linted; hosted execution still required. |
| GitHub-hosted macOS, CPython 3.13 | Manual compatibility workflow prepared; no local macOS qualification. |

The uploaded source's earlier review reports 143 passes on Linux CPython 3.13.5.
That historical report is not a fresh hosted-runner result. The precise CI core
versions are in [ci.txt](../requirements/ci.txt), packaging tools in
[packaging.txt](../requirements/packaging.txt), and optional test integration in
[test-optional.txt](../requirements/test-optional.txt). The earlier Windows
[reference lock](../requirements/verified.lock) is not a portable resolver lock.

## Migration from 2.1.0

The public estimator names, default learning algorithm, class order, supported
input schema, weights and native prediction rules are preserved. Python
3.10/3.11, accepted by older releases, are outside the new package's declared
range. Retain 2.1.0 or migrate to an admitted Python environment.

On pandas 2.2.3, the restricted snapshot reader recognizes specific legacy
constructors and can migrate nonmissing Python string indexes without changing
their labels or order. Unsupported missing-value semantics and unlisted
constructors remain errors. This is not universal cross-version persistence.
Serving images bind a producer/source contract and require their original
producer or re-export from a compatible native snapshot. Keep the original
model, digest and environment for rollback.

## Native and experimental functionality

The historical optional C++ source is retained under [native](../native/README.md)
but is not built into this wheel. Old native-wheel qualification does not apply
to a new binary. A compiler is unnecessary for this pure-Python package.
`auto` uses the admitted Python path when no native extension is installed;
requesting an unavailable native extension is an error, not a speedup.

`codadapt.experimental` retains `compile_ebm`, `CompilationError`,
`CompiledEBMClassifier`, `CompiledEBMRegressor` and `SafeBlendRegressor`. These
remain opt-in experimental interfaces. Software integration tests do not turn
them into newly qualified predictive components or scientific innovations.

The package includes its producer-bound `codadapt.serving` API. The separately
measured standalone lightweight serving/trace companion is **not included** in
the wheel or sdist. No dependency-free serving or trace command is advertised
as a bundled feature.

Build the distributions before distribution-bound tests, install the wheel,
then run `python -m pytest -q tests`. See [qualification](../qualification/README.md),
[installation](INSTALLATION.md) and [persistence](PERSISTENCE.md).
