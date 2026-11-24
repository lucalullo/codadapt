# CodAdapt 2.1.0 history

This summarizes the public 2.1.0 feature baseline. The complete historical source
and original notices remain attributable to that release; this summary does not
reclassify its experimental or platform qualification.

## Public API

- `CodAdaptClassifier`, `CodAdaptRegressor`, and the `CodAdapt` classifier alias.
- Dense numeric arrays and supported mixed-type DataFrames, training-only
  preprocessing, optional weights, and scikit-learn estimator integration.
- Binary and multiclass classification, single-target regression and native
  pickle/joblib persistence of trusted models.
- Optional C++ inference in separately qualified 2.1.0 artifacts. Those binaries
  are not bundled by the 2.2.0 pure-Python backend.
- Opt-in experimental EBM compilation and SafeBlend APIs, which remain
  experimental in 2.2.0.

See the [2.2.0 changelog](../CHANGELOG.md), [compatibility](COMPATIBILITY.md)
and the [historical benchmark panel](../benchmarks/HISTORICAL_210.md).
