# Release notes

## 1.0.0rc2 candidate — prepared locally, not published

The 1.0.0rc2 candidate adds native `memory_budget_mb=512` and accounts for external
validation rows before training allocations. This is a resource/API change that
requires **RC2 before stable 1.0**, with fresh platform qualification and public
observation. It does not change predictive training or internal precision. Published
RC1 remains unchanged; these additions are not available by installing RC1.

```python
from codadapt import CodAdaptClassifier

model = CodAdaptClassifier(memory_budget_mb=1024, random_state=42)
```

The parameter is a positive integer in MiB (2**20 bytes), with default 512.
Increasing it only raises the guard's admission budget: it does not reduce
memory usage or change learned predictions. Choose it with sufficient RAM
headroom for input, validation, other processes and the OS. This heuristic
is not a total RSS cap or a universal guarantee against OOM. SafeBlend does
not expose this parameter; see [the large-data guide](docs/LARGE_DATASETS.md).

No new algorithm, scientific recipe, precision change or predictive claim
is introduced. RC2 requires its own manual remote qualification and
observation before stable 1.0; preparation performs no publication.
See [LARGE_DATASETS.md](docs/LARGE_DATASETS.md) for configuration and limitations.

## 1.0.0rc1 candidate — not stable, not published by this preparation

CodAdapt is a compact native tabular model family with a scikit-learn-style API
and mixed predictive competitiveness. RC1 prepares product and API stability;
it does not claim benchmark supremacy or announce an index release.

### Native API and tasks

The intended native API is `CodAdaptClassifier`, its exact alias `CodAdapt`,
`CodAdaptRegressor` and `__version__`. Binary classification uses the native
coded-memory path. Single-label multiclass uses Shared OVR with shared encoding,
ordered original labels and normalized sigmoid probabilities, not softmax.
Regression supports a single target. No external learner is needed for native
fit, validation, prediction or reload. Active defaults and predictive algorithms
are unchanged from the qualified pre-RC payload.

Native constructors are keyword-only. Remove `max_iter`, `adapt_codes`,
`adapt_every`, `max_code_updates`, `n_candidates`, `min_code_count` and `patience`
from constructors, `set_params`, saved configuration and search grids; these
inactive controls are rejected explicitly. `features_per_table` remains a
resource-estimate control, not an interaction-order setting. `BucketEncoder` and
the preprocessing helper module remain private, with their internal import and
trusted-pickle path preserved. See [the API guide](docs/API.md).

### Experimental components and scientific positioning

`codadapt.experimental.SafeBlendRegressor` remains a fully native, opt-in Base +
Rational blend with frozen alpha 0.30 and internal validation fallback. Independent
qualification supports a **compact regression specialist**, not a general accuracy
leader: nine datasets / 45 splits gave +4.62% median RMSE versus the external
leader and 0.129× serialized size. A deep-RAM advantage was not demonstrated.
Binary/multiclass quality leadership is non-uniform; the frozen blind benchmark
supports mixed product positioning. Historical gains do not become new RC1 claims.
See [BENCHMARKS.md](BENCHMARKS.md) for panels, limitations and superseded evidence.

The optional EBM compiler remains experimental and limited to supported additive
binary/regression teachers from `interpret-core==0.7.8`. The teacher is required
only for compilation, not standalone compiled inference. No teacher, compiler
recipe, fidelity contract or runtime optimization changes in this candidate.

### Compatibility, hardening and known limitations

Python **3.10–3.14** is the declared qualification matrix. Core dependencies remain
NumPy, pandas, scikit-learn, SciPy and threadpoolctl. Explicit shared training has
no dynamic source execution. Input validation and successful/failed-fit lifecycle
hardening from the pre-RC payload are retained without scientific changes.

Dense numeric NumPy and mixed pandas inputs are supported; sparse data, mixed
NumPy object arrays, multioutput targets and multilabel classification are outside
the documented contract. Four known strict expected failures in the modern
sklearn checks reflect two scope limits for each native estimator: NumPy object
input and invariance to replacing sample weights with repeated rows. Quantiles
and support counts are unweighted; supported sample-weight behavior and exclusion
of zero-weight rows have separate passing contracts. These XFAIL are disclosed
scope limits, not newly hidden failures or full sklearn certification.

Pickle/joblib persistence is qualified in matching CodAdapt/Python/dependency
environments and fresh processes. Load only trusted artifacts. Cross-version,
cross-Python and cross-platform pickle portability is not guaranteed. Large/wide
workloads can be rejected by conservative memory guards; those guards are not a
hard process-RSS limit. Performance depends on workload and environment.

Native names, active meanings/defaults and documented methods/input/output
contracts are frozen as the candidate for future 1.x stability. Stable guarantees
take effect only with actual stable publication; SafeBlend, the compiler and
private helpers remain outside that stable surface. See [STABILITY.md](docs/STABILITY.md).

RC1 wheel/sdist builds, clean installs, API, persistence, examples/notebook and
local Python qualification are release gates. macOS and the full remote release
workflow remain **EXTERNAL_MANUAL_GATE**; no workflow run, upload, tag or release
is performed by local preparation. See [RELEASING.md](docs/RELEASING.md). Stable
1.0.0 requires RC feedback/index installs and its own final qualification.

## Historical 0.2.0rc2 preparation — pre-1.0 API cleanup

Native classifier/regressor construction is keyword-only and no longer accepts
the seven inactive controls listed in the [API migration guide](docs/API.md).
Remove those keys from application/search configurations. Existing root imports,
alias identity, retained defaults and prediction behavior are unchanged.
`features_per_table` remains an explicit resource-estimate control.
`BucketEncoder` is a private helper with its import/pickle path retained; it is
not a supported standalone public transformer. Source version stays 0.2.0rc2.

## 0.2.0rc2 — historical repository line

The current working tree adds native multiclass Shared OVR to CodAdaptClassifier
and its CodAdapt alias. Binary/regression defaults and algorithms are unchanged.
Shared encoding and compact artifacts preserve exact independent-OVR predictions;
probabilities normalize native sigmoids, not softmax. No external learner is required.
Python 3.10–3.14 is supported; core dependencies are NumPy, pandas, scikit-learn and
SciPy and threadpoolctl. No external ML model is required for native fit, validation, prediction or reload.

The experimental `SafeBlendRegressor` is fully native: unchanged Base plus a
complementary Rational estimator, frozen weight 0.30 and internal validation fallback.
It uses the normal core install with no external model dependency. Historical Round 78 independent
confirmation found +2.061% median RMSE gain, CI [+0.403%, +4.695%], on 18 new datasets
× five splits; the worst split lost 6.157%. This is panel-specific evidence, not a
no-harm guarantee. Fit remains about 4.13× Base in the frozen research panel.
The later independent external qualification did not replicate quality leadership:
nine datasets/45 splits gave +4.62% median RMSE versus the fixed external leader,
but serialized compactness replicated at 0.129×. Current positioning is **compact
regression specialist**, not a general quality leader. See [BENCHMARKS.md](BENCHMARKS.md)
and [the native SafeBlend contract](docs/SAFE_BLEND_EXPERIMENTAL.md).

Local release hardening preserves the explicit shared trainer and successful-fit
arithmetic, clarifies malformed validation errors and incomplete-fit state, and
removes inactive legacy controls in the subsequent pre-1.0 API cleanup. No version
bump or stable release is implied.
See [STABILITY.md](docs/STABILITY.md) and [RELEASING.md](docs/RELEASING.md).

The optional `ebm` extra remains solely an explicit experimental compiler/import tool
for already fitted additive interpret-core 0.7.8 models. It is not a native trainer,
is never invoked by native estimators and is unnecessary for compiled-model inference.
Its fidelity and runtime contract remain unchanged. See [the compiler documentation](docs/EBM_COMPILER.md).

Local package validation is recorded separately from remote CI and independent-hardware
validation. No release, tag, publication or version increment is created by this cleanup.
The historical published tag is unchanged; current files and rebuilt local distributions
must be distinguished from older artifacts bearing the same version.

## 0.2.0rc1 — Experimental release candidate

This candidate adds the optional experimental additive EBM compiler documented in
[EBM_COMPILER.md](docs/EBM_COMPILER.md). The native default remains the v0.1.0 core.
Compilation requires the optional EBM extra; inference from a saved compiled model
does not. Exact raw-score verification and numerical probability tolerance are mandatory.

Subsequent frozen local validation covered 12 datasets × 3 splits (36 cases per
environment), using one thread on native Windows and WSL/Linux on the same physical
host. Supported teacher-to-compiled fidelity passed 36/36 cases in each environment;
standalone inference without interpret passed 36/36 in Windows. Median compiled/EBM
memory ratios were 0.195x deep retained memory and 0.236x serialized size.

These results support compact standalone export, not a general inference accelerator.
The historical single-row speed advantage did not replicate; runtime depends on
workload and environment. Cross-OS raw scores and classes were bitwise identical,
while probability differences reached 2.22e-16, within the frozen 1e-15 absolute
tolerance (relative tolerance zero). Strict cross-OS probability-bitwise checks did
not all pass. See [the full benchmark disclosure](BENCHMARKS.md#experimental-ebm-compiler--frozen-local-validation).

This local validation does not establish remote CI or independent-hardware performance.
The compiler remains opt-in, experimental and non-default; the native core is unchanged.

## 0.1.0 — Historical release notes

CodAdapt 0.1.0 is the first experimental public release.

The default `CodAdapt` and `CodAdaptRegressor` estimators now use adaptive coded memory with a shared
multi-resolution encoder. No strategy flag is required or exposed. The promoted default is
prediction-equivalent to the previously validated candidate on the core-promotion benchmark.

The release supports dense NumPy and mixed pandas input, missing and unseen values, binary
classification, regression, sample weights, validation stopping, persistence, deterministic random
states, and scikit-learn `get_params`/`set_params` behavior.

This remains alpha software. The frozen comparison found useful inference and retained-memory
characteristics but no general predictive-quality advantage over budget-matched LightGBM. Validate
quality, latency, memory, and error handling on the intended workload.
