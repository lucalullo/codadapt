# Experimental SafeBlendRegressor

`SafeBlendRegressor` is an opt-in, single-target **regression-only** estimator in
`codadapt.experimental`. Native CodAdapt estimators and defaults are unchanged.
CodAdapt 0.2.0rc2 includes the validated engineering integration of this frozen recipe.
The integration itself is not a new predictive confirmation; the experimental recipe/API is frozen.

```python
from codadapt.experimental import SafeBlendRegressor

model = SafeBlendRegressor(random_state=42, verbosity=0, n_jobs=4)
model.fit(X_train, y_train)
prediction = model.predict(X_test)
```

## Fit-only optional dependency

Install the tagged GitHub release with the optional training extra:

```bash
python -m pip install "codadapt[safeblend] @ git+https://github.com/lucalullo/codadapt.git@v0.2.0rc2"
```

From a local checkout:

```bash
python -m pip install -e ".[safeblend]"
```

It pins **LightGBM 4.7.0**. LightGBM is not a mandatory core dependency. Importing
SafeBlend, reloading a fitted artifact and predicting do not import LightGBM.
Fit raises a clear installation error if the teacher is unavailable and rejects
another version to preserve the frozen recipe.

The teacher is a tree ensemble used offline. Deployment uses compact Base memory
plus flat binary functions and coefficients; the deployed artifact is neither a
tree nor a neural network. This is an approximate LightGBM compiler, distinct from
the additive EBM compiler. It does not preserve all teacher quality or claim exact
LightGBM predictions.

## Frozen fitting and branch contract

Pass only outer training data to `fit`; keep evaluation data separate. The method
uses a fixed internal split: **75% TRAIN / 25% branch validation**, with seed
`random_state + 100`. Base keeps its unchanged 15% internal validation. External
category vocabularies are discovered on TRAIN only; validation does not add labels.

The pipeline fits the frozen Base, fits the fixed LightGBM teacher, compiles it,
then evaluates Base and the blend on branch validation. The teacher uses 500
estimators, 31 leaves, learning rate 0.05, lambda 1 and one teacher thread. Compilation
uses UNIFORM SBD1024, 25,000 jitter queries and ridge 0.0001. The amplitude is fixed:

```text
alpha = 0.27388247139831357
blend = Base + alpha * (Compiled - Base)
if RMSE(blend) >= RMSE(Base): branch = BASE
else:                       branch = BLEND
```

Ties choose BASE. There is **no final refit** and no test-based choice. Models retain
the exact inner-training fit rather than fitting again on all input rows. Validation
fallback reduced observed downside; it cannot guarantee improvement on future data.
BASE artifacts contain only required Base state and compact diagnostics, with no
compiler or teacher. BLEND artifacts contain Base plus compiled state, with no
teacher, training/query arrays or optimizer.

## Parameters and diagnostics

Signature: `SafeBlendRegressor(*, random_state=0, verbosity=0, n_jobs=4)`.

- `random_state`: fixed integer seed for reproducibility.
- `verbosity`: 0 or 1.
- `n_jobs`: 1–4 fitting BLAS threads; teacher remains at one thread. Prediction uses
  the caller's BLAS settings; the frozen RC2 audit used four threads.

Alpha, safety threshold, validation fraction, compiler capacity, teacher tuning and
representation recipe are not configurable. There is no sample-weight, external
validation-set, classifier or partial-fit interface for this experimental estimator.

Fitted properties: `branch_`, `alpha_`, `validation_base_rmse_`,
`validation_blend_rmse_`, `base_`, `compiled_`, and compact `fit_diagnostics_`.
`compiled_` is None for BASE; no compiler object is retained. `compiler_` is an alias
of `compiled_`. Base/compiled diagnostics are internal deployment state, not
independent estimators or supported mutable tuning interfaces. `n_features_in_` and
string-column `feature_names_in_` are also available. Predict before fit raises
`NotFittedError`.

## Inputs and unsupported tasks

Supported inputs are dense numeric two-dimensional NumPy arrays or pandas DataFrames
with unique column names and the same columns/order at prediction. Mixed frames
support scalar categorical labels, boolean features, numeric NaN and missing category
values. Unseen categories map to missing according to the frozen train-only encoding.
Numeric array columns are numeric; there is no categorical-column parameter.
Do not change feature roles between fit and prediction.

Targets must be one-dimensional finite numeric regression values. Boolean/string
labels, explicitly categorical multiclass targets, two-valued numeric targets,
missing/infinite targets and multioutput targets are rejected. Sparse inputs,
complex/datetime training features, infinity, malformed shapes and incompatible
prediction schemas are unsupported. Fit requires at least eight rows.

**Numeric multiclass IDs cannot be distinguished automatically from legitimate count
regression.** More than two numeric target values are treated as regression; callers
must not use this estimator for classification. The conservative binary check also
excludes binary-valued numeric regression. Full sklearn `check_estimator` compliance
is not claimed; clone/get_params/set_params and the documented fitted contract are tested.

## Persistence and standalone deployment

Use trusted pickle/joblib with compatible package and dependency versions:

```python
import joblib

joblib.dump(model, "safe_blend.joblib")
restored = joblib.load("safe_blend.joblib")
prediction = restored.predict(X_test)
```

Public artifacts use `codadapt.experimental` module paths and retain no LightGBM
objects. Fresh-process reload/prediction is tested with teacher and fit-helper imports
blocked. Deployment still needs core CodAdapt, NumPy, pandas, scikit-learn and SciPy.
Pickle/joblib is not a stable cross-version interchange schema; use matching versions
and only trusted artifacts. Private research pickles are not supported public inputs:
the engineering replay explicitly converts known checkpoints in its private harness.
No automatic public migration from private names is provided.

## Quality evidence and limits

A frozen independent confirmation evaluated the candidate on **18 real regression dataset
sources × 5 splits** not used earlier in the recorded research. The median of dataset
mean RMSE gains was **+5.20% versus CodAdapt Base**, with dataset-bootstrap 95% interval
approximately **+2.87% to +15.37%** and **17 wins / 1 tie / 0 losses** at ±0.1% gain.
Safety selected BASE12/90 and BLEND78/90. Some selected blend test splits still lost;
the worst remaining split degradation was about6.10%.

These are convenience-panel, random-row IID results, not a universal guarantee or
future-time/new-subject/site validation. Five overlapping splits are not90independent
replications. Missing early archives limit absolute historical novelty proof. Public
integration replays the same frozen evidence; it is not new quality confirmation.

## Measured deployment and offline costs

The frozen productization panel used 18 first-seed workloads for paired warm latency,
90 artifacts for size, batches1/32/1k/100k, warmup1 and repeats9/9/7/3, alternating
model order. Preprocessing/Base/correction are included; batch materialization is not.
The environment was the development machine (AMD Ryzen 7 255, about 32 GB RAM), Windows 11,
Python 3.12.14, NumPy 2.3.5, LightGBM 4.7.0 and four BLAS threads/one teacher thread.
No independent hardware claim is made.

| Batch | Productization latency / Base | Productization latency / LightGBM |
| --- | --- | --- |
| 1 | 0.528× | 0.634× |
| 32 | 0.682× | 0.433× |
| 1k | 1.927× | 0.173× |
| 100k | 5.383× | 0.105× |

Median serialized/deep retained size was **1.434× / 0.819× Base**. The frozen systems audit measured serialized
size versus its teacher at about 0.045×; deep Python graph accounting does not fully
capture native LightGBM memory. Serialized size and retained graphs are not peak RSS.
The streaming task's four representative workloads had about55.83MiB median traced
whole-deployment temporary peak; this is not total isolated process RAM.

Small-batch interactive deployment is the stronger measured niche; large batches
remain much slower than Base. Dispatch is automatic: the audited small path through
32 rows and 2048-row streaming chunks above that. Cuts, cells, coefficients and
float64 arithmetic order are unchanged; no optimization or capacity change is included.

Offline training remains expensive: the archived full pipeline was **75.71× Base**,
including teacher fit; compilation given an already fitted teacher was **64.44× Base**.
These are source-balanced medians with full-pipeline Base denominators, not universal
costs. Small API fit smoke tests do not replace real-panel training-cost evidence.
Different hardware, libraries, data, feature counts and batch sizes can change costs.

The RC2 integration audit separately checked public/private bitwise predictions,
serialization, representative paired API costs, public tests and built packages.
The experimental namespace may change; validate quality and deployment cost on the intended workload.

## RC2 integration measurements

The RC2 public integration audit measured serialized/deep size **1.433× / 0.819× Base**
and latency **0.477× / 0.621× / 1.546× / 4.692× Base** at batches 1 / 32 / 1k / 100k.
These are source-balanced local medians, not performance promises. Hardware/protocol: development machine (AMD Ryzen 7 255, about 32 GB RAM), Windows 11,
Python 3.12.14, NumPy 2.3.5, four BLAS threads; 18 first-seed workloads, 90 size
artifacts, warmup 1, repeats 9/9/7/3 and paired alternating Base/private/public order. Predictions include
preprocessing; input batch materialization is excluded equally. No material public
wrapper regression was detected. This RC changes version/docs/non-executable provenance
only; it does not optimize or change the measured model. Large batches remain slower
than Base, offline fitting remains expensive, and independent-hardware validation is pending.
