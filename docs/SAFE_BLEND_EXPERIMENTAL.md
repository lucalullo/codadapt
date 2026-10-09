# Experimental native SafeBlend regression

`codadapt.experimental.SafeBlendRegressor` is an opt-in, fully native regression
estimator in the current **0.2.0rc2** repository. Standard CodAdapt installation
is sufficient. It fits no external teacher and retains no external model.
`CodAdaptRegressor` remains the default. The optional `codadapt[ebm]` compiler is
a separate tool and is not used by SafeBlend.

```python
from codadapt.experimental import SafeBlendRegressor

model = SafeBlendRegressor(random_state=42, verbosity=0, n_jobs=4)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
print(model.branch_, model.alpha_)
```

## Frozen training and prediction contract

The supplied data is split into 75% effective training and 25% internal validation.
For an integer seed, the split uses `random_state + 100`; Base uses `random_state`.
Numerical values are unscaled. Categories use a sorted, training-only vocabulary;
missing and unseen categories map to missing before the native bucket encoders.
No validation or test target enters preprocessing or either model's fit.

Base is the unchanged default `CodAdaptRegressor`, with this explicit validation
set and the detected categorical indices. The complementary native Rational
estimator uses 16 quantile bins, ridge 0.001 and at most 100 L-BFGS-B iterations.
It predicts a learned sum of numerator effects divided by one plus nonnegative
denominator effects, rescaled by the training target mean and standard deviation.
The solver's finite final iterate is retained even if its convergence flag is false,
matching the validated recipe. Nonfinite fitting results fail explicitly.

The fixed candidate prediction is:

```text
Base + 0.30 * (Rational - Base)
```

Strict improvement of validation RMSE selects `BLEND`; ties and worse validation
results select `BASE`. Squared losses are compared before taking the square root,
preserving the frozen comparison arithmetic. There is **no final refit** on the
validation rows. Alpha, capacity, regularization, stopping and selection rule are
internal constants, not public hyperparameters.

The fitted model exposes `branch_`, `alpha_`, `validation_base_rmse_`,
`validation_blend_rmse_`, `base_`, `rational_`, `n_features_in_` and compact
`fit_diagnostics_`. `rational_` is `None` on `BASE`, and its fitted state is discarded.
`alpha_` is 0 on `BASE` and 0.30 on `BLEND`. Training and validation rows are not
retained. `feature_names_in_` is provided for DataFrames with string column names.

## Inputs and estimator API

Supported inputs are dense real numeric NumPy arrays and pandas DataFrames with
numeric, string/object, categorical, boolean and missing values. Use categorical
or string pandas columns for integer-coded categories: this minimal API has no
`categorical_features` parameter. Raw datetime, complex values, infinities, sparse
input and mixed NumPy object arrays are unsupported. Missing numerical values
are supported. Unseen categories follow the frozen missing-category mapping.

Prediction must use the same DataFrame/array representation and the same number
of features. DataFrame columns must be unique and match the fitted schema;
reordering is allowed. At least eight fitting rows are required.

Targets must be finite, one-dimensional, single-target regression values. Boolean,
string and pandas categorical class labels, multioutput targets and conventional
small integer classification encodings are rejected. Specifically, two distinct
integer labels or consecutive labels `0..K-1` for `2 <= K <= 20` are treated as
classification. Numeric regression and classification targets are intrinsically
ambiguous; this guard is not a semantic classification detector. Other integer
regression outcomes remain supported. Use `CodAdaptClassifier` for classification.

The constructor has only `random_state=None`, `verbosity=0` and `n_jobs=1`.
`n_jobs` must be positive; it limits numerical threads during fit without creating
process workers. `verbosity` is 0, 1 or 2. Integer seeds from 0 through
`2**32 - 101` are supported. Integer seeds give repeatable fits with matching
dependencies. `get_params`, `set_params`, `clone`, regression scoring and ordinary
sklearn pipelines/CV follow the estimator protocol. `sample_weight`, `eval_set`
and incremental training are not part of this experimental interface.

Trusted pickle/joblib loading and prediction require only CodAdapt and its normal
numerical dependencies. Prefer matching dependency versions for persistence.
Cross-version bitwise fitting equivalence is not guaranteed.

## Confirmed evidence and limits

Round 78 froze the recipe before evaluating **18 new real regression datasets ×
5 splits**. The median dataset RMSE gain versus Base was **+2.061%**, with a
dataset-bootstrap 95% CI of **[+0.403%, +4.695%]** and dataset wins/ties/losses
**17/1/0** under the preregistered tie tolerance. The worst individual split
was **−6.157%**. Validation fallback reduces observed downside but **does not
guarantee improvement** on new data.

The inherited IID row protocol and recoverable historical novelty audit limit
these claims; temporal/grouped extrapolation and independent hardware remain
unvalidated. These are panel-specific results, not universal performance bounds.

Round 78 local medians versus Base were approximately **4.13× fit time**,
**1.09× serialized size**, **1.08× deep retained memory** and **1.19–1.23× warm
raw-input inference latency** for batches 1, 32, 1k and 100k. Those fit timings
predate the later exact callback optimization. The current implementation reuses
the already evaluated objective value for diagnostic tracing instead of recomputing
the full gradient. Qualification preserved coefficients, trace, iterations, branch
decisions and predictions bitwise-identically across the sealed replay. On a paired
six-case engineering panel, Rational fit time fell by **43.55%** and total SafeBlend
fit time by **27.27%**; serialized/deep memory and inference were effectively
unchanged. These measurements are panel-specific, not API latency guarantees.

The public port is checked against all 90 sealed cases for branch, Base, Rational,
blend and final predictions and RMSE. Local qualification passed Python 3.10–3.14;
actual remote CI remains a separate execution environment. SafeBlend remains
experimental, opt-in and regression-only.
