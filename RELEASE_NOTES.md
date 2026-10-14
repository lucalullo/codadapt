# CodAdapt1.0.0 release notes

## Stable native API, unchanged RC2 behavior

CodAdapt1.0.0 finalizes the native API qualified through RC1/RC2:
`CodAdaptClassifier`, its exact alias `CodAdapt`, `CodAdaptRegressor` and `__version__`.
Constructors remain keyword-only. Binary uses the native coded-memory path;
single-label multiclass uses Shared OVR, shared encoding, ordered original labels
and normalized sigmoid probabilities. Regression remains single-target.
No new algorithm, default, numerical precision, compiler behavior or dependency
is introduced. All non-version runtime files are identical to public RC2.

The seven inactive pre-1.0 controls remain removed. `features_per_table` remains
functional only in the memory estimate, not interaction order. BucketEncoder and
preprocessing internals remain private. See [API.md](docs/API.md) for migration.

## Large datasets and resource admission

Native `memory_budget_mb=512` remains a positive integer in MiB, supports clone/
get/set/persistence, and includes external validation rows. Raising it changes
admission only, not model capacity or fitting. It is a heuristic, not an RSS cap
or universal OOM guarantee. The documented699635×21 engineering case is
SUPPORTED_WITH_CONFIG at1024MiB using a shape-equivalent synthetic fixture;
the undisclosed original real dataset was not reproduced. Float32 can reduce
raw/copy memory while internal precision remains unchanged. SafeBlend has a
separate resource profile. See [LARGE_DATASETS.md](docs/LARGE_DATASETS.md).

## Experimental components

SafeBlendRegressor remains experimental and opt-in: a fully native compact
regression specialist, with unchanged Base+Rational recipe and internal fallback.
It is not promoted to stable core API. The optional additive EBM compiler remains
experimental, pinned to interpret-core0.7.8, with teacher-free compiled inference.
No new experimental API is added.

## Compatibility, persistence and limitations

Python3.10–3.14 is the support matrix. Core dependencies remain NumPy, pandas,
scikit-learn, SciPy and threadpoolctl. Native inputs are dense numeric NumPy or
mixed pandas; sparse/object NumPy, multilabel/multioutput, raw datetime/complex/
infinite features and online/GPU training remain outside scope.
Failed fit/refit invalidates the old fitted state. Concurrent read-only prediction
is smoke-tested; simultaneous fit/mutation is unsupported.

Same-version pickle/joblib is supported in a matching Python/dependency/platform
environment. Load only trusted files. Cross-version/Python/platform/dependency
portability is not guaranteed; RC2 replay success is WORKS_NOT_GUARANTEED, not
a permanent migration promise. Four known strict sklearn XFAIL remain disclosed:
object-array inputs and weighted-row-repetition equivalence, for each native estimator.
Quantiles/support are unweighted; zero-weight exclusion has separate passing contracts.

## Scientific integrity

The frozen blind benchmark remains PRODUCT_POSITION_MIXED. Binary and multiclass
are not uniform quality leaders. Independent SafeBlend qualification remains
COMPACT_REGRESSION_SPECIALIST_CONFIRMED: quality leadership did not replicate,
serialized compactness did. Its nine-source/45-split panel has+4.62% median RMSE
versus the external leader and0.129× serialized size; no deep-RAM advantage was
demonstrated. Preserve all denominators, source counts, downside and coverage
limitations in [BENCHMARKS.md](BENCHMARKS.md). Stable API is not a scientific promotion.

## Release qualification

Local version/artifact qualification is separate from publication. RC2 platform/
index successes are maintainer-reported context. Stable post-integration push CI,
manual full release matrix including macOS, TestPyPI/index smoke, v1.0.0 tag and
production publication remain maintainer-only gates. This preparation executes
no remote workflow, tag, release or upload. See [RELEASING.md](docs/RELEASING.md).
