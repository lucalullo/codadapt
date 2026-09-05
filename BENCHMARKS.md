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

Install the optional benchmark dependencies to include LightGBM:

```bash
python -m pip install -e ".[benchmark]"
python benchmarks/run_benchmarks.py --output benchmark_results/results.csv
```

The public runner is not an exact reproduction of the frozen release protocol; it exists so users
can quickly compare quality, fit time, prediction time, and serialized model size in their own
environment.
