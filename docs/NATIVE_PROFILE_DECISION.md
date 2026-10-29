# Explicit native execution and automatic dispatch

**The automatic guard is unchanged.** On the qualified Windows x64 / CPython
3.10.22 and 3.14.10 profiles, normal predictions still select Python. Explicit
native execution passes finite correctness and performance checks, but is not
the same as automatic selection or a stable public backend parameter.

| Exact profile | Installed native execution | Normal automatic selection |
|---|---|---|
| Windows x64, CPython 3.10.22; NumPy 1.26.4, pandas 2.2.3, SciPy 1.14.1, scikit-learn 1.6.1 | Core qualified; optional EBM remains blocked by OS policy | Python |
| Windows x64, CPython 3.14.10; NumPy 2.5.4, pandas 3.1.0, SciPy 1.18.1, scikit-learn 1.9.1 | Qualified in the declared finite scope | Python |
| Windows x64, CPython 3.12.10; NumPy 2.5.4, pandas 3.1.0, SciPy 1.18.1, scikit-learn 1.9.1 | Preserved G6-R1 evidence; fresh proposed 2.1.0 runtime still blocked at a prerequisite | Native eligible when the extension is present; this retained code guard is not a new 2.1.0 clean-runtime PASS |
| Other OS, architecture, Python patch or dependency versions | Requires its own execution evidence | Python |

A pure wheel has no native extension and uses Python. On an eligible profile,
expected absence of the exact extension falls back to Python; DLL, ABI, transitive
import and Windows App Control errors are not suppressed as successful native
execution. Explicit native requests fail visibly if unavailable.

## New finite performance evidence

No model was fitted again. Three previously saved engineering models (binary,
multiclass and regression) and fixed synthetic ndarray inputs were reused.
For each profile, nine fresh paired processes alternated Python/native order.
Each batch used 30 prediction calls after warmup (five at 65,536 rows), with one
numerical thread and no concurrent Codex build/test/benchmark. CPU affinity and
frequency were not pinned. The hardware inventory is the same previously
recorded Windows11 / AMD Ryzen7 255 machine; a fresh read-only CIM query was
unavailable and was not elevated or retried.

| Profile | MC batch 2,048 Python median | Explicit native median | Reduction | MC p95 Python / native | Median whole-process peak RSS ratio native/Python |
|---|---:|---:|---:|---:|---:|
| 3.10.22 | 1.8830 ms | 1.1001 ms | 41.58% | 1.97875 / 1.16626 ms | 0.99250 |
| 3.14.10 | 1.6308 ms | 0.9593 ms | 41.18% | 1.87756 / 1.03218 ms | 0.99546 |

All 12 measured task/batch cells per profile (1, 32, 2,048 and 65,536 rows)
passed the preregistered latency non-regression check. The original G3 target
of at least20% multiclass batch2,048 improvement and the1.05x small-batch/RSS
bounds were retained. Serialized state and model sizes were identical.
There were252 exact dtype/shape/output-byte comparisons per profile, including
labels, probabilities and decision scores where applicable. These are repeated
checks of three finite models, not252 independent datasets or a predictive study.

Peak working set is the entire worker process, including imports and resident
models/queries. It is not model-only RAM and does not establish a memory-saving
claim. Throughput in the detailed evidence means rows/second at the measured
single-request latency, not concurrent server throughput. No training speedup,
new accuracy improvement, multiclass algorithmic promotion or cross-platform
support follows from these inference measurements.

The complete samples, exact model hashes, package versions and per-cell results
are in [NATIVE_PROFILE_EVALUATION.json](../qualification/NATIVE_PROFILE_EVALUATION.json).
The [preregistered protocol](../benchmarks/NATIVE_PROFILE_PROTOCOL.md) and
[benchmark script](../benchmarks/native_profile_benchmark.py) are included.

## Why automatic selection is not expanded in this delivery

The dispatcher `codadapt/_inference.py` is covered by the producer-source contract.
Changing its automatic guard changes that fingerprint and the combined contract.
The current loader would then reject existing proposed2.1.0 serving images even
though the ordered floating-point calculation remains equivalent. Keeping the
old hash despite changed source, excluding the dispatcher from integrity checks,
or introducing an unchecked allowlist would weaken the persistence contract.

This delivery preserves the existing2.1.0 source contract exactly, as requested.
No verified and authorized serving migration exists for a changed guard, so
passing explicit-native performance is not used to introduce that incompatibility.
No new fallback or silent backend policy is added. ExistingG6-R1 source-bound
exports still require their preserved producing runtime; this delivery does not
alter that rule. See [PERSISTENCE.md](PERSISTENCE.md).

The private `codadapt._inference.inference_backend("native")` context is used by
qualification tools. It remains private rather than a promised public API. Normal
usage continues through `from codadapt import CodAdaptClassifier` with the automatic
selection stated in the table above.

## Reproduction in an already qualified matching environment

Use only trusted local model files. For the exact no-fit replay, supply the three
hashed engineering `.pickle` files from the retained evidence. A fresh finite
workload can instead be generated explicitly with the existing engineering probe;
that generates new engineering evidence and does not recreate historical hashes
by assertion.

```text
python tools/engineering_probe.py --output qualification_runs/native_reference --native required
python benchmarks/native_profile_benchmark.py run --python <absolute-path-to-matching-python> --models qualification_runs/native_reference --output qualification_runs/native_benchmark
```

Set `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1` and
`NUMEXPR_NUM_THREADS=1` before starting; use a new output directory. Keep model
and output paths local, avoid competing benchmark/build jobs, and retain failures.
The recorded production evidence used the bounded laboratory runner with a
300-second/1.5GiB owned-process-tree limit. The standalone benchmark is sequential
with a45-second timeout for each worker and does not itself enforce a total RSS
limit. Do not use it to bypass any OS policy.
