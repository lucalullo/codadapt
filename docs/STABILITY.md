# Stability and persistence contract

## Stable native API in 1.0.0

The stable surface is `codadapt.CodAdaptClassifier`, its exact alias
`codadapt.CodAdapt`, `codadapt.CodAdaptRegressor` and `codadapt.__version__`.
It includes documented constructor parameters/defaults, public methods, input and
output shapes, class ordering, documented exception categories and inspection
attributes in [API.md](API.md). Estimators follow scikit-learn constructor,
clone, parameter and Pipeline conventions. Stable 1.0.0 preserves qualified RC2
behavior; it introduces no new learner, probability mapping or experimental API.

`memory_budget_mb=512` remains a keyword-only positive integer in MiB. It controls
a deterministic admission heuristic, not total RSS, and includes external validation
rows. It does not increase model capacity or promise unlimited data size. See
[LARGE_DATASETS.md](LARGE_DATASETS.md). `features_per_table` remains functional
only in this memory estimate; native interaction groups are pairs, or a singleton
when only one feature exists. Numeric resolution remains capped at16 bins.

The pre-1.0 removal of seven inactive controls and keyword-only construction is
documented in the [migration guide](API.md). Those controls do not return in1.0.0.
Stable API does not mean predictive leadership, a final algorithm, complete sklearn
certification, arbitrary input support or universal hardware/memory guarantees.

## Experimental and private surfaces

`codadapt.experimental` exports `SafeBlendRegressor`, `compile_ebm`,
`CompilationError`, `CompiledEBMClassifier` and `CompiledEBMRegressor`. They remain
experimental, opt-in and outside stable API guarantees. SafeBlend is a compact
regression specialist, not the native default or a general accuracy leader.
Compiled classes are compiler outputs, not general trainable sklearn estimators.

Underscore modules and `codadapt.preprocessing`, including `BucketEncoder`, are
private implementation details. BucketEncoder is not exported at the root or
experimental namespace. Its internal import/trusted-pickle path is retained.
Do not mutate encoders, heads, histories or fitted arrays or depend on their layout.

## Semantic versioning and deprecation

Use major versions for intentional incompatible changes to the stable surface,
minor versions for backward-compatible capabilities and patch versions for fixes.
Deprecations emit `FutureWarning` at the public call site, document migration in
the API guide/changelog, and remain for at least two minor releases before removal
in a major release. Experimental/private surfaces are excluded. Prediction-changing
default changes require release notes and comparison with existing behavior.
Malformed inputs may be rejected more clearly by fixes.

## Persistence

Pickle/joblib round trips are supported for the same CodAdapt version in a matching
Python, dependency and platform environment. Record those versions, schema and
artifact SHA256. Only load trusted files: deserialization can execute arbitrary code.
Same version does not guarantee portability across different numerical environments.

Cross-CodAdapt-version, cross-Python-minor, cross-dependency and cross-platform
loading is **not guaranteed**. RC2-to1.0.0 replay is a qualified diagnostic,
WORKS_NOT_GUARANTEED, not a permanent migration contract. No stable interchange
format, automatic migration or long-term serialized-layout compatibility is promised.
Keep the original environment when archiving models.

## Fitting, reproducibility and concurrency

Fit returns self. Failed fit/refit leaves the estimator unfitted; complete a valid
new fit before predicting. Concurrent read-only predict/predict_proba has smoke
coverage. Concurrent fits, fit-with-predict and parameter/fitted-state mutation are
unsupported. SafeBlend fit thread-pool limits are process-wide.

Use an integer random_state and identical data/order/configuration/environment for
repeatability. Bitwise results across numerical versions or platforms are not
guaranteed. `None` is nondeterministic; prefer integers over shared RandomState objects.
