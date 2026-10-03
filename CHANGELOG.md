# Changelog

## 0.2.0rc2 - Experimental release candidate

- Added opt-in `codadapt.experimental.SafeBlendRegressor` for single-target regression.
- Added the optional pinned `safeblend` LightGBM training dependency; saved models
  predict and reload without the teacher.
- Preserved the validated fixed blend amplitude, validation fallback, no-final-refit
  protocol and compact deployment runtime. Native estimators and defaults are unchanged.
- Included the previously validated small-batch and streaming runtime optimizations;
  this candidate makes no new predictive or runtime changes.
- Added public contract, persistence and packaging tests and deployment documentation.
- Removed non-executable private source-path metadata from the packaged recipe.

This is an experimental release candidate. Training remains expensive; the measured large-batch path is slower than Base. The native core and defaults remain unchanged.

## 0.2.0rc1 - Experimental release candidate

- Added opt-in `codadapt.experimental.compile_ebm` for supported additive binary and
  regression EBMs, with capacity/schema checks and mandatory fidelity verification.
- Added standalone compiled estimators with pickle/joblib persistence and no EBM
  dependency at inference. Compilation uses the optional pinned `ebm` extra.
- Kept the native v0.1.0 default, training algorithm and existing estimator API unchanged.
- Added compiler contract documentation, integration tests and optional-dependency CI.
- Excluded private research directories from source distributions.

This is an experimental release candidate. Probability fidelity is numerical; no universal large-batch performance or independent-hardware claim is made.

**Subsequent documentation clarification (post-R74, not a new release):** frozen
local Windows/WSL validation supports compact standalone export and the documented
teacher-fidelity contract. The historical single-row speed advantage did not replicate;
no general inference-speed advantage is established. Both environments used the same
physical host, so independent-hardware validation remains pending. See
[BENCHMARKS.md](BENCHMARKS.md#experimental-ebm-compiler--frozen-local-validation).
The compiler remains experimental, opt-in and non-default. This clarification does
not change the release chronology, implementation or version.

## 0.1.0 - Experimental public release

- Made adaptive coded memory with shared multi-resolution encoding the official CodAdapt default.
- Added `CodAdapt` / `CodAdaptClassifier` for binary classification and `CodAdaptRegressor` for single-target regression.
- Added native pandas handling for numeric, categorical, string, boolean, and missing values.
- Added shared coarse-to-fine encoding, adaptive levels, feature-level stopping, coded residual memory, and a lookup budget.
- Added sample weights, explicit validation sets, deterministic random states, persistence, and scikit-learn estimator APIs.
- Added examples, documentation, benchmark disclosure, automated tests, packaging checks, and GitHub Actions CI.

This is an experimental alpha release and makes no claim of general superiority over established boosted-tree libraries.
