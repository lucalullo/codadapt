# Benchmark Disclosure

CodAdapt 0.1.0 is experimental software. Its release comparison is intended to describe observed
trade-offs, not to claim general superiority over established tabular models.

The frozen release candidate was compared with HistGradientBoosting and budget-matched LightGBM on
12 datasets and five shared splits per dataset (240 valid runs). Nine datasets were synthetic and
three were scikit-learn real datasets. Raw-input preprocessing was included in the latency protocol.

Ratios below are `LightGBM / CodAdapt`; values above one favor CodAdapt for speed or compactness.

| Result | Value |
| --- | ---: |
| Predictive-quality mean wins | 0 / 12 |
| End-to-end training-time median wins | 5 / 12 |
| Raw-input inference-latency median wins | 10 / 12 |
| Retained model-memory wins | 12 / 12 |
| Median fit-speed ratio | 0.887x |
| Median inference-speed ratio | 1.258x |
| Median retained-memory ratio | 8.830x |
| Stable predictive wins | none |
| Four-dimensional Pareto dominance | none |

The measured candidate therefore showed a useful low-memory / low-latency profile, but no general
predictive-quality advantage over budget-matched LightGBM. The median fit ratio also favored
LightGBM overall.

These results are hardware-, dataset-, version-, split-, thread-, and workload-dependent. New users
should benchmark on their own data before drawing conclusions.

## Public sanity runner

The repository includes a deliberately small, self-contained sanity benchmark using built-in
scikit-learn and synthetic datasets:

```bash
python benchmarks/run_benchmarks.py --quick
```

The public runner compares native CodAdapt with sklearn HistGradientBoosting only.
The optional benchmark extra supplies system measurement tooling, not LightGBM:

```bash
python -m pip install -e ".[benchmark]"
python benchmarks/run_benchmarks.py --output benchmark_results/results.csv
```

The public runner is not an exact reproduction of the frozen release protocol; it exists so users
can quickly compare quality, fit time, prediction time, and serialized model size in their own
environment.

## Experimental EBM compiler — frozen local validation

This subsequent compiler validation is separate from the native v0.1.0 comparison
above. It evaluates the opt-in `codadapt.experimental` compiler, not a change to the
native learner or default. The compiler remains experimental and non-default.

### Panel and protocol

The frozen panel used **12 known datasets × 3 fixed splits = 36 cases per environment**:
Adult, SDSS STAR, Breast Cancer and binary Wine classification; Diabetes, California,
Superconduct, SGEMM, Buzz, Diamonds, House Sales and Green Taxi Tips regression.
Native Windows and WSL/Linux ran on the **same physical AMD Ryzen 7 255 host** with
32 GB installed RAM (about 15.6 GB exposed to WSL), using a **one-thread protocol**.
This is software-environment replication, not independent-hardware validation or new
dataset confirmation.

Windows used Python 3.12.14; WSL Ubuntu 24.04.4 used Python 3.12.3. Both used NumPy
2.3.5, pandas 2.2.3, SciPy 1.16.2, scikit-learn 1.8.0 and interpret-core 0.7.8.
The fixed additive EBM recipe used `interactions=0`, `max_bins=256`, `outer_bags=4`,
`max_rounds=2000`, `learning_rate=0.04`, `smoothing_rounds=200`,
`early_stopping_rounds=50`, `n_jobs=1` and seeds 44001–44003. The frozen compiler was
the public NumPy runtime; these were newly fitted teachers for that validation,
not a replay of the original research teacher objects.

Timing used three interleaved blocks, three warmups and 15 repetitions. Blocks are
not independent hardware or temporal-session replications. Paired session ratios
were aggregated by median across splits within each source, then by equal-source
median, P90 and worst ratio. The same source-balanced aggregation applies to memory.

### Quality / fidelity

Teacher-to-compiled verification passed **36/36 cases on Windows and 36/36 on WSL**.
Raw binary scores and regression predictions were bitwise identical; AUC, RMSE and
MAE deltas were zero on the measured data. The largest absolute log-loss delta was
approximately 1.86e-15, within the frozen metric tolerance.

Cross-OS raw scores/regression predictions and class labels were also bitwise identical.
Probability differences reached **2.22e-16**, within the frozen compiler contract
`atol=1e-15, rtol=0`. Numerical equivalence is not probability-bitwise equality:
strict cross-OS checks failed for the 12 classifiers in each transfer direction,
while the 24 regressors passed. These bitwise failures remain recorded; they are
not numerical-fidelity failures and the tolerance was not changed. The overall
frozen validation verdict remains mixed rather than an unconditional portability pass.

### Memory

Ratios here and in the latency table are **compiled / EBM**, unlike the native
comparison above. Smaller values favor the compiled model.

| Model-memory measure | Windows median | WSL median | P90, both OS | Worst, both OS |
| --- | ---: | ---: | ---: | ---: |
| Deep retained memory | 0.195x | 0.195x | 0.308x | 0.390x |
| Serialized size | 0.236x | 0.236x | 0.252x | 0.265x |

The reciprocals of the unrounded median ratios are approximately **5.13x deep** and
**4.24x serialized** compression factors. These are descriptive reciprocals, not
separately aggregated median compression factors or universal memory guarantees.
Deep retained memory counts the deduplicated Python/array object graph, not every
native allocation. Whole-job peak RSS included inputs and multiple models, so an
isolated compiled/teacher peak-RSS ratio cannot be inferred.

### Latency

**Ratio >1 means compiled is slower than EBM.** All measured batch sizes and both
environments are shown; the favorable Windows batch100k median is not a general claim.

| Batch | Sources | Windows median | Windows P90 | Windows worst | WSL median | WSL P90 | WSL worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 12 | 2.703x | 3.236x | 3.319x | 2.533x | 3.356x | 3.387x |
| 32 | 12 | 2.684x | 2.839x | 2.906x | 2.621x | 2.929x | 3.116x |
| 1,000 | 12 | 1.307x | 2.088x | 2.273x | 1.484x | 1.985x | 2.824x |
| 100,000 | 9 | 0.926x | 3.897x | 5.416x | 1.115x | 1.996x | 2.739x |

The batch100k comparison covers nine eligible sources under the frozen rule and uses
labeled cyclic replay where needed; it does not always represent 100k unique rows.
**The historical single-row speed advantage did not replicate.** A general
inference-speed advantage is not established, and no universal batch crossover has
been demonstrated. Differences from earlier research timings cannot be attributed
to the OS alone: teacher recipe, cohort and runtime/input paths also differed.

### Standalone

Loading and inference passed **36/36 cases in a local Windows environment with
interpret physically absent**. Compiled artifacts retain no teacher; CodAdapt and
its normal runtime dependencies are still needed. WSL standalone checks blocked
teacher imports, while interpret remained installed in the fitting environment.
Cross-OS loading succeeded even where probability-bitwise checks failed.

This supports compact standalone deployment within the verified contract, not
compatibility with every future platform, package version or hardware configuration.
Teacher training remains an upstream cost. See the [compiler contract](docs/EBM_COMPILER.md)
for supported models, schemas, mandatory verification and explicit `REJECT` behavior.
