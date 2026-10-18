# CodAdapt 1.1.0rc1 release notes

Local prerelease candidate; this preparation does not publish an artifact or run
remote workflows. The frozen C1 computational implementation is unchanged.

- **Resource-aware automatic admission:** native binary, Shared OVR multiclass
  and regression constructors default to `memory_budget_mb="auto"`. Eligible
  large inputs can fit without manually increasing a budget when visible
  resources provide conservative headroom. The original 699,635 x 21 satisfaction
  dataset has source-bound full-fit acceptance evidence, not merely a preflight.
- **Explicit control is preserved:** a positive integer in MiB is a hard cap on
  estimated working allocation E, not on total RSS. Pass `512` to retain historical
  admission. SafeBlend's internal Base remains explicitly 512 MiB.
- **Scoped systems value:** matched C1 fit ratio approximately 0.997x, ndarray
  inference latency 0.808x (19.2% lower), categorical pickle size 0.748x (25.2%
  smaller), each in its own qualified protocol. These are not one universal
  benchmark. Peak RSS was about 1.002x in the matched fit comparison; no general
  RAM saving is claimed. DataFrame inference may be unchanged; categorical
  compaction can increase loading time and small models can grow slightly.
- **Predictive behavior:** qualified exact comparisons preserve predictions and
  fitted numeric state. No accuracy improvement or competitive leadership is
  claimed; the published blind quality evidence remains mixed.
- **Compatibility:** exact RC installed-wheel checks cover Windows Python
  3.10–3.14, plus a Python 3.12 sdist install. Actual Windows, WSL, Kaggle, Docker,
  nested Linux and macOS receipts are bound through the frozen C1/V8 source
  lineage. They are not a fresh RC OS-by-minor matrix.

AUTO is a visible-resource heuristic, not an allocation reservation or anti-OOM
guarantee. Hidden limits, concurrent pressure and custom input conversions remain
limitations. Same-version matching-environment trusted persistence is supported;
cross-version replay is diagnostic, not guaranteed. Four known sklearn scope
XFAIL remain disclosed. SafeBlend and EBM compilation remain opt-in experimental.

See [migration](docs/V1_0_1_TO_V1_1_0RC1_COMPATIBILITY.md),
[AUTO details](docs/AUTO_MEMORY.md), [all six limitation rows](docs/RC1_KNOWN_LIMITATIONS.md),
[Python policy](docs/PYTHON_COMPATIBILITY.md) and [manual release steps](docs/RELEASING.md).

---

## Historical 1.0.1 notes

The following section preserves its preparation-time availability statements.

# CodAdapt 1.0.1 release notes

Patch release focused on exact training-speed optimization. CodAdapt1.0.1
substantially reduces native training time while preserving the exact learned
model and predictions. This source candidate is prepared locally; publication
and final remote release gates are maintainer actions.

The change replaces structured-row distinct counting in training metadata with
exact scalar counting for native one- and two-feature codes, including Shared
OVR's existing cache. API, defaults, addressing, learned numeric values,
probabilities and model-format semantics are unchanged. No new algorithm,
feature, parameter or dependency is introduced.

Controlled local qualification measured a Windows median fit ratio of about
0.24× and a WSL ratio of about0.19× versus unpatched1.0.0. Installed-wheel
qualification also showed strong speedup. These are measured workload results,
not a promise of the same speedup on every dataset or machine. No accuracy,
inference-speed or memory improvement is claimed.

Python3.10–3.14 and the stable1.0 native API remain supported. SafeBlend and the
optional additive EBM compiler remain experimental. Same-version trusted
pickle/joblib persistence requires matching environments; successful1.0.0
artifact replay does not establish general cross-version portability.

The four known sklearn scope XFAIL remain documented. Classification quality
is still mixed; benchmark and compact-specialist SafeBlend positioning are
unchanged. See [BENCHMARKS.md](BENCHMARKS.md), [STABILITY.md](docs/STABILITY.md)
and the [manual release procedure](docs/RELEASING.md).
