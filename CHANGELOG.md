# Changelog

## 0.1.0 - Experimental public release

- Made adaptive coded memory with shared multi-resolution encoding the official CodAdapt default.
- Added `CodAdapt` / `CodAdaptClassifier` for binary classification and `CodAdaptRegressor` for single-target regression.
- Added native pandas handling for numeric, categorical, string, boolean, and missing values.
- Added shared coarse-to-fine encoding, adaptive levels, feature-level stopping, coded residual memory, and a lookup budget.
- Added sample weights, explicit validation sets, deterministic random states, persistence, and scikit-learn estimator APIs.
- Added examples, documentation, benchmark disclosure, automated tests, packaging checks, and GitHub Actions CI.

This is an experimental alpha release and makes no claim of general superiority over established boosted-tree libraries.
