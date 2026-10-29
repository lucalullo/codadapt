> Historical public documentation preserved from the 2.0.0 source line.
> Technical descriptions apply where unchanged; release and platform receipts
> below describe that historical source, not qualification of the present C++
> backend. Current scope: [compatibility](COMPATIBILITY.md), [API](API.md),
> [persistence](PERSISTENCE.md). This copy remains a development review candidate.
> In historical prose, "native" names CodAdapt's own algorithm; it does not
> imply that training runs in C++.

# CodAdapt coded-memory learning algorithm

This describes the explicit shared trainer in `_training.py`. Historical
coordinate-wise code-move experiments do not describe this public runtime.
The binary/regression learning arithmetic is unchanged by the release hardening.

## Train-only encoding

Positive-weight training rows determine quantiles, vocabularies and support. An
internal validation split, when requested, is made before encoding. The finest
numeric resolution is `max(2, min(16, n_bins))`, with three nested resolutions
`[max(2, finest//4), max(2, finest//2), finest]`. Codes are computed once and mapped
to coarser levels. Quantile sampling is limited by `quantile_sample_size`.

Numeric buckets use `searchsorted(cuts, value, side="right")`: equality goes right;
NaN has a separate bucket and infinities are rejected. Duplicate cuts and cuts at
the minimum are removed. Categorical buckets distinguish missing, rare observed,
unseen and frequent values. Supported categorical scalars include strings, booleans,
integers and finite reals; `"1"`, `1` and `True` are distinct, while `1` and `1.0`
represent the same numeric category. Vocabularies use observed training values,
not unused pandas categorical levels. Schema and support remain frozen at prediction.

## Compact residual memories

```text
F(x) = intercept + sum over accepted levels of:
       sum main_value[feature_bucket] + sum interaction_value[address]
address = sum(feature_code[feature_bucket]) mod table_size
```

`table_size` is a power of two. The regressor returns F; the binary classifier
returns a stable sigmoid and preserves class labels. Initial intercept is the
weighted target mean or weighted class log-odds. A missing/unseen bucket without
training support contributes zero. An interaction containing an unsupported bucket
contributes zero; empty memory cells are zero. Python's randomized `hash()` is not used.

Each level receives a share of the remaining `lookup_budget`. Cheap screening on at
most 512 training rows precedes full feature scoring. Main effects are selected by
residual gain, fitted sequentially and can be dropped at later levels when weak.
The bounded interaction proposal uses feature-gain-ranked pairs, train-only random
integer codes and collision-aware utility. It does not enumerate all pairs over the
entire dataset. Groups have two features, or one when p=1. Selected interaction
memories are then fitted sequentially to the current residual surrogate.

For cell address m, aggregate float64 statistics with `np.bincount`:

```text
A[m] = sum h_i; B[m] = sum h_i * residual_target_i
value[m] = B[m] / (A[m] + l2)
gain = 0.5 * sum B[m]^2 / (A[m] + l2)
regression: h = sample_weight; residual_target = y - current_prediction
binary: h = sample_weight / 4; residual_target = 4 * (y - sigmoid(current_score))
```

The binary update is a global-curvature quadratic surrogate, not the exact logistic
Hessian. L2 penalizes memory values, not the intercept. Losses are weighted sums;
rescaling all weights changes regularization strength. Zero-weight rows are removed
before discovery. Target or weight scales causing numerical overflow must be rescaled.

## Validation and stopping

Validation uses unweighted MSE or logloss. A candidate level is accepted when its
validation reduction exceeds `tol * max(1, abs(previous_validation_loss))`.
The first rejected level stops fitting and is discarded, preserving earlier levels.
There are at most three accepted levels. With `early_stopping=False`, explicit
validation loss is diagnostic only. There is no hidden final refit.

`n_iter_ == best_iteration_` is the accepted-level count. `accepted_moves_` is zero.
Inactive legacy controls were removed from the constructor in the pre-1.0 API
cleanup; see the migration section in [API.md](API.md). `features_per_table` remains
a resource-estimate control only. The learning updates, memory selection, stopping,
encoding and prediction arithmetic are unchanged by that cleanup.

Training rows, residuals, buckets, addresses and fit caches are discarded. The model
retains frozen encoding and compact tables. For each accepted level inference costs
roughly O(n*(selected main features + 2*interactions)), plus input validation/encoding.
Numerical encoding uses binary search over cuts; categorical mapping cost depends on
cardinality and values. Neither constant latency nor a hard RSS bound is promised.

The historical preflight fit estimate cap is 512 MiB; frozen C1 in 2.0.0
adds AUTO admission while preserving explicit integer caps (see [AUTO_MEMORY.md](AUTO_MEMORY.md)).
The separate bucket-matrix limit remains 512 MiB;
input arrays, the interpreter, vocabularies and other temporaries add RSS. Observed
categorical membership is limited to one million categories per feature. Oversized
workloads are rejected before primary allocations rather than routed to another model.

## Multiclass Shared OVR

For K classes, encoding, schema, resolution maps and validation rows are shared.
Each target `y == class` uses the same explicit native trainer with unchanged weights,
but its own residuals, selection and stopping. Fit-local caches reuse only X-dependent
addresses/counts/masses. No source text is reconstructed or executed.

Inference encodes once and evaluates K native heads. Sigmoid scores are normalized
across classes, not softmax; ties select the first label in `np.unique` order.
A compact artifact deduplicates shared metadata and preserves float64 coefficients.
Pickle/joblib restore sharing. No external teacher or private research module is
required. See [STABILITY.md](STABILITY.md) for persistence and concurrency limits.

## Current opt-in class balancing

The classifier adds class_weight="balanced" using effective positive TRAIN
mass, before OVR heads; class_weight=None and the regressor are unchanged.
See [API](API.md) for the exact weighting formula and validation isolation.
C++ accelerates ordered inference only; it does not change the learning rule.
