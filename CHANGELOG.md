# Changelog

## 1.1.0rc1 — prepared locally, not published

- Change the native memory admission default from `512` to `"auto"`. Eligible
  larger inputs use conservative visible headroom; explicit positive integer
  budgets remain hard caps on the deterministic working-allocation estimate E.
  Neither mode guarantees RSS or prevents every OOM. No model downsizing,
  subsampling, precision or fitted-prediction change is introduced.
- Preserve frozen C1 lazy admission routing, scoped real platform acceptance
  and the existing experimental SafeBlend internal Base budget of 512 MiB.
- Qualify the exact RC wheel on Python 3.10–3.14 and its sdist on Python 3.12
  locally; distinguish source-bound platform receipts from a new remote matrix.
- Document the intentional default migration, six audited limitation rows and
  manual-only release gates. No parameters are deprecated or removed in this RC.

- Optimize numeric NumPy prediction input conversion and exact address
  arithmetic. Learned values and predictions are unchanged by these inference optimizations.
- Share immutable categorical strings within bounded native encoder metadata
  after fit and trusted pickle/joblib loading. This reduces duplication in
  qualifying categorical models; high-cardinality loading can take longer.
  Existing artifacts remain compatible.

## 1.0.1 — prepared locally, publication pending

- Optimize exact training metadata cardinality counts for native one- and
  two-feature codes, including Shared OVR's existing count cache. Predictions,
  fitted numeric state, API, defaults and model format are unchanged. This is
  an internal training-speed optimization; no accuracy, inference-speed or
  memory improvement is claimed. This patch preserves the learned model and
  predictions; local preparation does not publish 1.0.1.

## 1.0.0

- Finalize stable native CodAdapt/Classifier/Regressor API from qualified RC2;
  keyword-only construction, active defaults and predictive/resource semantics unchanged.
- Retain Shared OVR multiclass, clear failed-fit state and configurable native
  memory_budget_mb=512MiB with external-validation accounting.
- Keep SafeBlend and EBM compilation experimental; BucketEncoder stays private.
- Finalize version/installation/metadata/stability/persistence/release documentation.
  Same-version matching-environment persistence is supported; cross-version portability is not guaranteed.
- Preserve mixed blind competitiveness and compact-specialist SafeBlend evidence;
  no new algorithm, predictive promotion, runtime dependency or benchmark is introduced.
- Stable publication remains a separate maintainer-only action after qualification.

The following entries preserve earlier prerelease preparation history, including
their availability statements at that time; they do not describe current package-index availability.

## 1.0.0rc2 — prepared locally, not published

- Add native `memory_budget_mb=512` as a positive integer MiB admission budget.
  Preserve default budget, encoder, fitted values and training precision.
- Count external validation rows in preflight allocation estimates, before row
  copies and encoding. Explain the estimated/requested budget in resource errors.
- Load trusted RC1 native objects with the historical 512 MiB parameter default;
  tested loads do not promise general cross-version persistence.
- Document large-data scaling, dtype effects and SafeBlend's separate resource
  limitations. The guard is a heuristic, not an RSS cap or OOM guarantee.
- Published 1.0.0rc1 is unchanged. This RC2 payload requires fresh
  qualification/observation before stable release; do not republish it as RC1.

## 1.0.0rc1 candidate — prepared, not published

- Prepare the native `CodAdapt` / `CodAdaptClassifier` and `CodAdaptRegressor`
  API for a future stable 1.x contract. This is a prerelease candidate; no PyPI
  release, tag or stable compatibility guarantee is announced.
- Retain native binary classification, shared-encoding Shared OVR multiclass and
  single-target regression without changing their algorithms or active defaults.
- Keep fully native `SafeBlendRegressor` and the additive EBM compiler explicitly
  experimental and opt-in. SafeBlend is a compact regression specialist, not a
  general predictive-quality leader.
- Carry forward explicit classifier training without internal `exec`/source
  reconstruction, input validation and fitted-state/failed-refit hardening.
- Freeze keyword-only native constructors after removing seven inactive legacy
  controls; retain `features_per_table` solely as a resource-estimate control.
- Keep `BucketEncoder` private while preserving its internal import/pickle path.
- Retain Python 3.10–3.14 support and matching-environment trusted persistence.
  Qualify fresh RC1 wheel/sdist artifacts, installed APIs and package metadata;
  full remote platform qualification and index checks remain manual gates.
- Update current-version documentation and notebook checks to `1.0.0rc1`, with
  Beta prerelease metadata. Historical versions and scientific evidence remain
  historical; the version bump makes no new performance claim.

The entries below record preparation of the historical 0.2.0rc2 line. Their
version statements describe that earlier work, not the current1.0.1 source.

## Historical 0.2.0rc2 preparation — pre-1.0 API cleanup

- **Breaking constructor cleanup:** remove the inactive `max_iter`, `adapt_codes`,
  `adapt_every`, `max_code_updates`, `n_candidates`, `min_code_count` and `patience`
  parameters from the native classifier/regressor. Remove these keys from saved
  configuration and parameter-search dictionaries; `set_params` now rejects them.
- Native estimator constructors are keyword-only, so old positional calls fail
  explicitly instead of silently shifting the meanings of remaining arguments.
  Retained parameter defaults, fitting and prediction arithmetic are unchanged.
- Keep `features_per_table` as a documented resource-estimate control; it does not
  change interaction order. No inactive control is reactivated.
- Define `codadapt.preprocessing.BucketEncoder` as a private implementation detail,
  keeping its physical import/pickle path for native model persistence. No standalone
  encoder API is stabilized or moved to the experimental namespace.
- Record the future 1.x semantic-version/deprecation policy and pre-1.0 migration.
  Source version remains 0.2.0rc2; no release is implied by this entry.


## Historical 0.2.0rc2 preparation — release engineering

- Preserve explicit shared classifier training without dynamic source execution.
- Give malformed validation arrays clear public errors and mark a fit successful
  only after final logging; interrupted logging cannot leave a valid fitted marker.
- Avoid an out-of-range integer cast in SafeBlend target validation.
- Add focused lifecycle/concurrency/memory/schema contracts and strengthen an OVR assertion.
- Declare the existing lightweight threadpoolctl runtime dependency explicitly.
- Correct legacy parameter/trainer documentation, add stability/persistence and
  manual release policies, runnable examples and installed-package OS qualification CI.
- Keep scientific recipes/defaults, persistence layout and version 0.2.0rc2 unchanged.

## 0.2.0rc2 — historical repository line

- Refactored classifier training to remove internal dynamic source execution while
  preserving binary and multiclass model outputs. Public API, defaults and
  persistence format are unchanged.
- Completed independent SafeBlend regression qualification: nine NEW_EXTERNAL
  datasets, 45 frozen group/time splits, zero tuning and 270/270 SUCCESS jobs.
- Refined SafeBlend positioning to an experimental compact regression specialist:
  serialized compactness independently replicated (0.129× the external leader),
  while predictive quality leadership was not confirmed (+4.62% median RMSE).
  The earlier five-dataset −0.67% quality advantage did not replicate; no deep-RAM
  advantage was demonstrated. Algorithm, API, defaults and version are unchanged.
- Completed the frozen blind external benchmark: 16 NEW_EXTERNAL primary datasets,
  72 conditions, zero tuning and 381 terminal jobs (380 SUCCESS, one memory-guard
  coverage/system rejection). Protocol and baselines were frozen before fitting.
- Updated product positioning using the earlier blind panel to mixed predictive
  competitiveness with consistently compact serialized models. SafeBlend passed
  that panel's separate regression size/quality gates; the later independent
  qualification above supersedes its predictive positioning.
- Refined Base regression, binary and multiclass quality caveats using the blind
  evidence; retained earlier external pilots and research panels as historical evidence.
- Documented the external leakage-audited product qualification: six datasets,
  eleven evaluation units, no tuning and mixed predictive results versus fixed HGB.
- Disclosed the known binary competitiveness limitation and multiclass variability
  across domains and metrics, separately from successful technical qualification.
- Clarified separate Base/SafeBlend regression results and the tested conservative
  safe-memory exclusion of Covtype-like workloads; no actual OOM was measured.
- Removed redundant gradient recomputation in the native SafeBlend Rational
  optimization path while preserving exact model outputs.
- Redesigned experimental `SafeBlendRegressor` as fully native Base + Rational
  diversity blending, with frozen alpha 0.30 and internal validation fallback.
- Removed the external LightGBM product dependency; no SafeBlend extra is needed.
- Ported the independently confirmed Round 78 recipe without changing scientific
  capacity, preprocessing, stopping or prediction semantics.
- Round 78 independent research confirmation found +2.061% median RMSE gain on 18 new regression datasets × five splits;
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
