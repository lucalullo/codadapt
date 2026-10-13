# Stability and persistence contract

## Current prerelease

The source version remains **0.2.0rc2**, an experimental prerelease. No 1.0 release
or compatibility promise is created by this document. Published historical RC2
artifacts and rebuilt local RC2 artifacts must be distinguished by SHA256.

The intentional native API is `codadapt.CodAdaptClassifier`, its exact alias
`codadapt.CodAdapt`, `codadapt.CodAdaptRegressor`, and `codadapt.__version__`.
The estimators follow scikit-learn constructor/clone/parameter/Pipeline conventions.
Supported methods and fitted inspection attributes are described in [API.md](API.md).
Fitted numeric arrays, encoders, histories, heads and caches are implementation
details; do not mutate them or rely on their storage layout.

`codadapt.experimental` intentionally exports `SafeBlendRegressor`, `compile_ebm`,
`CompilationError`, `CompiledEBMClassifier` and `CompiledEBMRegressor`. Compiled
classes are outputs of the compiler, not general trainable sklearn estimators.
The experimental namespace can change independently and is never the native default.
Underscore-prefixed modules and the entire `codadapt.preprocessing` helper module
are private implementation details. `BucketEncoder` is not a supported standalone
transformer and is not exported from the root or experimental namespace. Its
historical module/class path stays importable for internal use and trusted model
persistence; no physical rename or serialized-layout change accompanies this decision.

## 1.x policy — effective when a stable release is published

Stabilize the root estimator names, constructor defaults/active parameter meanings,
method signatures, target/prediction shapes, class ordering, supported input contract
and documented exception categories. Fixes may reject malformed inputs more clearly.
New opt-in estimators can be added without replacing existing defaults. Any deliberate
prediction-changing default requires release notes and comparison with existing behavior.

Use semantic versioning: major for intentional incompatible stable API changes,
minor for backward-compatible capabilities, patch for fixes. Deprecations should
emit `FutureWarning` at the public call site, document a migration in the API guide
and changelog, and remain for at least two minor releases before removal in a major
release. Experimental/private surfaces are excluded from this stable contract.
This policy is not a retroactive compatibility guarantee for RC artifacts.
The pre-1.0 cleanup removes seven inactive constructor controls and makes native
estimator construction keyword-only; see [API.md](API.md) for migration. All
remaining defaults and active parameter meanings are unchanged. In particular,
`features_per_table` is explicitly a memory-estimate control, not interaction order.

## Persistence

Pickle/joblib round trips are tested within a matching CodAdapt/Python/numerical
environment. Save package and dependency versions, feature schema and artifact SHA256.
Only load trusted artifacts: deserialization can execute arbitrary code.
Cross-CodAdapt, cross-Python, cross-dependency and cross-platform loading are **not
guaranteed**. Historical prerelease load success is diagnostic, not a support policy.
No stable interchange format, automatic artifact migration or long-term binary
compatibility is promised. Preserve the original environment when archiving models.

## Fitting, reproducibility and concurrency

Fit returns self. Failed refit invalidates the former fit; complete a valid new fit
before predicting. `check_is_fitted` and prediction reject failed/unfinished fits.
Use an integer random_state for repeatability with identical inputs/order/environment.
Numerical results across dependency versions or platforms are not guaranteed bitwise.
`None` is nondeterministic. RandomState consumption differs by estimator; prefer integers.

Concurrent read-only prediction has smoke coverage. Concurrent fit, fit with predict,
parameter mutation, or manual mutation of fitted arrays is unsupported. SafeBlend's
fit thread-pool limits are process-wide; avoid simultaneous fits in Python threads.
