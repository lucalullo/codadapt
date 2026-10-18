# Large datasets and memory admission

## Native 1.1.0rc1 resource contract

The local RC defaults to `memory_budget_mb="auto"` for native estimators.
Version 1.0.1 used 512 MiB; an explicit integer retains that contract. See
[AUTO_MEMORY.md](AUTO_MEMORY.md) for the two paths, exact reserve policy,
array-like limitations, diagnostics and migration. No release is authorized.

## Historical 1.0.x resource contract

CodAdapt 1.0.0 preserves the `memory_budget_mb=512` parameter introduced in RC2
for the native classifier and regressor. The scientific recipe, arithmetic and
admission semantics are unchanged. Historical RC1 lacked this configurable parameter.

```python
from codadapt import CodAdaptClassifier

# Native 1.0.0; reserve RAM for the process and caller data.
model = CodAdaptClassifier(memory_budget_mb=1024, random_state=42)
model.fit(X_train, y_train)
```

`memory_budget_mb` is a positive integer measured in **MiB (2**20 bytes)**, despite
the conventional `_mb` suffix. In published 1.0.x the default is 512 and there is no automatic RAM
detection, unlimited mode, or retry. The 1.1.0rc1 AUTO default adds conservative
resource observation; explicit integers retain this contract. The
parameter controls admission only: increasing it does not increase model capacity,
change the encoder, change arithmetic precision, or alter the training recipe.
It works with `get_params`, `set_params`, clone, Pipeline and pickle/joblib.

## What the guard estimates

The deterministic working-allocation heuristic is

```text
E = (N + V) * (40*P + 2*T + 80)
    + 24 * (P + T*min(P,F)) * max(B+1,C+3)
    + 32*T*S
```

Here N is input training rows before zero-weight filtering, P is feature count,
T=`n_tables`, F=`features_per_table`, B=`n_bins`, C=`max_categories`, and
S=`table_size`. V is external `eval_set` rows, or zero with internal validation.
Internal validation is already part of N. External validation accounting is a
RC2 safety change retained in 1.0.0; RC1 omitted V. A fit is admitted when E is at most the
configured budget. Rejection occurs before row copies and encoding, after basic
input/target/weight validation. Converting an array-like input itself can allocate
memory before this check; prefer an existing ndarray or DataFrame.

This is an engineering heuristic, **not a bound on total process RSS**. It neither
reserves RAM nor guarantees that a fit cannot run out of memory. Imports, caller
data, categorical/string payloads, retained class heads, allocator caches, native
workspace and concurrent processes contribute separately. Historical measurements
show both overestimation and underestimation of incremental fit allocations. There
is no universal row limit, and a rejected shape is not proof that the machine lacks
RAM. Do not infer a safe budget from installed RAM alone.

At defaults, 699,635 rows and 21 features require **624.72 MiB** by this formula,
so the historical 512 MiB default rejects them even with float32 input. A
1,024 MiB explicit budget admits that estimate. The real satisfaction CSV has
subsequently passed scoped private AUTO full-fit gates on multiple platforms,
including real Kaggle and macOS. This does not qualify arbitrary categories or
every workload of the same shape.

## Scaling and practical use

Dense input bytes alone are N*P*4 for float32 and N*P*8 for float64. Native fitting
also keeps raw row selections, multiple uint16 code levels and full-length float64
working vectors. Float32 reduces raw input/copy storage, but does not halve total
RSS; numeric conversions and learned values still use float64. Casting arbitrary
float64 data to float32 can change cut assignments and predictions. The stable finalization
does not change internal precision. The guard intentionally remains dtype-neutral.

Shared OVR fits K heads sequentially with one shared encoder and a bounded X-only
cache. Time generally grows with K; retained predictive state grows with K too.
The heuristic has no explicit K term and is not a certificate for high-K workloads.
Use smaller representative fits and measure the complete process on your hardware.
Large strings/high-cardinality categories can cost more than numeric fixtures.

On machines with 16, 32 or 64 GB RAM, choose a budget only after accounting for
caller input, imports, data preparation, validation, other programs and ample OS
headroom. More physical RAM alone does not justify a specific budget. Keep one
large fit at a time; concurrent cross-validation multiplies working memory. Use
sequential CV and a small number of numerical threads when memory is constrained.
Prediction can be called on successive row batches without changing the fitted
model; there is no online/partial-fit training interface.

## Rejection and failure handling

The error reports estimated MiB, configured MiB, training/validation row counts
and feature count. Reduce rows/features, or explicitly increase the budget after
measuring available headroom. Reducing `n_tables` or `table_size` affects secondary
terms and often cannot rescue a shape dominated by 40*N*P. Do not use unused
columns, zero weights or smaller float dtype as a way to bypass admission.

A failed fit/refit invalidates the estimator for prediction. Catch the exception,
correct the input or resource configuration and perform a complete new fit.
`check_is_fitted` must reject unfinished fits. OS-level termination is outside
Python exception handling; preserve data/checkpoints outside the process.

## SafeBlend is a separate resource profile

Experimental `SafeBlendRegressor` retains its frozen API and recipe. It does not
expose `memory_budget_mb`; its internal Base is explicitly pinned to 512 MiB and the
internal Base accounts for its external validation rows. SafeBlend also prepares
a numeric DataFrame and fits its Rational component, which has separate temporary
allocations. A successful Base fit is not a SafeBlend memory guarantee. No universal
large-N SafeBlend guarantee or unlimited-memory mode is supported.

Persistence policy remains [STABILITY.md](STABILITY.md). Trusted RC1 native objects
loaded by 1.0.0 receive the historical 512 MiB parameter default. Tested
loads do not create a general cross-version compatibility promise.
