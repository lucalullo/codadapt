# Changelog

## Unreleased — current 0.2.0rc2 repository line

- Removed redundant gradient recomputation in the native SafeBlend Rational
  optimization path while preserving exact model outputs.
- Redesigned experimental `SafeBlendRegressor` as fully native Base + Rational
  diversity blending, with frozen alpha 0.30 and internal validation fallback.
- Removed the external LightGBM product dependency; no SafeBlend extra is needed.
- Ported the independently confirmed Round 78 recipe without changing scientific
  capacity, preprocessing, stopping or prediction semantics.
- Confirmed +2.061% median RMSE gain on 18 new regression datasets × five splits;
  improvement is not guaranteed on individual datasets or splits.
- Reduced fit/deployment cost relative to the superseded external-model design;
  the frozen native research panel still costs about 4.13× Base to fit.
- Added standalone persistence, native-independence tests and Python 3.10–3.14 CI.
- Native binary/regression defaults, EBM compiler and version 0.2.0rc2 remain unchanged.
- Added automatic fully native single-label multiclass classification to CodAdaptClassifier/CodAdapt.
- Shared OVR retains exact independent-native-OVR predictions with shared encoding, validation and compact artifact persistence; gains are panel-specific.
- This is local experimental API integration, not a new release or research round.

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
