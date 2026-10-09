# CodAdapt: Exploratory Repeated Cross-Validation Benchmark

**Date:** 9 October 2026  |  **Status:** Author-run exploratory experiment, **not** independent validation.

## Scope and protocol

- Models: CodAdapt, LightGBM, Random Forest, scikit-learn HistGradientBoosting.
- Datasets: scikit-learn breast_cancer (569 × 30), diabetes (442 × 10), wine (178 × 13), digits (1,797 × 64).
- Repeated 5-fold cross-validation, 3 repeats, 15 held-out scores for each model and dataset (240 fit/evaluation records).
- Identical task-appropriate scoring per dataset: ROC-AUC for binary classification, macro one-versus-rest ROC-AUC for multiclass classification, RMSE for regression.
- No hyperparameter tuning. Single-thread configuration. Training-time values come from one measurement per fold; prediction times from the median of five runs after warm-up.
- No claim of statistical independence among folds, model superiority, or external replication.

## Predictive performance: average over 15 folds

| Dataset (metric) | CodAdapt | LightGBM | Random Forest | HistGradientBoosting |
|---|---:|---:|---:|---:|
| breast_cancer (ROC-AUC ↑) | 0.9849 | 0.9931 | 0.9908 | 0.9941 |
| diabetes (RMSE ↓) | 61.46 | 60.86 | 58.87 | 60.73 |
| wine (ROC-AUC OVR macro ↑) | 0.9981 | 0.9981 | 0.9992 | 0.9992 |
| digits (ROC-AUC OVR macro ↑) | 0.9886 | 0.9996 | 0.9994 | 0.9995 |

Higher ROC-AUC is better; lower RMSE is better. These are **descriptive means**, not statistical significance tests.

## Median fit time and serialized model size

| Dataset | Model | Median fit (s) | Median pickle size (KiB) |
|---|---|---:|---:|
| breast_cancer | codadapt | 0.0193 | 50.0 |
| breast_cancer | lightgbm | 0.0836 | 273.3 |
| breast_cancer | random_forest | 0.1624 | 303.8 |
| breast_cancer | hist_gb | 0.1626 | 273.1 |
| diabetes | codadapt | 0.0057 | 14.2 |
| diabetes | lightgbm | 0.0139 | 129.6 |
| diabetes | random_forest | 0.1122 | 3093.4 |
| diabetes | hist_gb | 0.0383 | 164.3 |
| wine | codadapt | 0.0228 | 93.0 |
| wine | lightgbm | 0.0181 | 263.0 |
| wine | random_forest | 0.0672 | 192.5 |
| wine | hist_gb | 0.0504 | 177.9 |
| digits | codadapt | 0.1345 | 274.7 |
| digits | lightgbm | 0.3708 | 2607.5 |
| digits | random_forest | 0.1877 | 4926.6 |
| digits | hist_gb | 1.2762 | 2320.9 |

Timing is strongly hardware/software dependent and especially noisy for very short operations. Pickle size is **not** necessarily runtime memory usage.

## Interpretation and limitations

- CodAdapt produced smaller serialized models on all four datasets and had low measured fitting times. It did not have the highest **mean** predictive performance on any dataset in this experiment.
- An apparent CodAdapt advantage on the diabetes single holdout benchmark did **not** persist in repeated cross-validation; Random Forest had the lowest mean RMSE.
- The Wine task is close to the metric ceiling for all models, limiting discrimination. Digits reveals a marked predictive-quality gap.
- These datasets are small and widely reused; the evaluation lacks larger independent datasets, task-specific tuning budgets, independent reruns, and uncertainty procedures accounting for correlated folds.
- All benchmark design and execution were done within the project effort, so this is not an external or peer-reviewed validation.

## Reproduction

The public repository must include **the exact script used**, `benchmarks/reproducibility/benchmark_codadapt_cv.py`, as well as its raw CSV and JSON metadata. Run from the repository root.

```bash
python -m pip install -e ".[dev,benchmark]"
python -m pip install lightgbm==4.7.0
python benchmarks/reproducibility/benchmark_codadapt_cv.py
```

Observed environment: Python 3.12.10 on Windows; codadapt 0.2.0rc2, NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1, LightGBM 4.7.0; threads=1. See `benchmark_cv_full.json` for all logged protocol and dataset hashes.

Git revision: `6f058d838077f693f810d4bf779c009bb7149a56`. Script SHA-256: `42791b18f001749710cf4bd42752ec58710686a279841a4405086d46ef17c896`.

Raw outputs: `benchmark_cv_full.csv` and `benchmark_cv_full.json`.

## Next validation steps

- Independent rerun by someone else, confirming the script hash and using a clean environment.
- Broader real-world tabular benchmarks with pre-defined splits and matched tuning budgets.
- Report within-dataset paired differences and meaningful uncertainty, avoiding independence assumptions for folds.

