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
