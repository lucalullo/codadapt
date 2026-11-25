# CodAdapt 2.1.0 benchmark summary

Fixed configurations on the 14 development origins; aggregate printed-precision measurements. Select the numerically best available external comparator for each primary metric. Missing results remain missing; 2.2.0 technical evidence is separate.

## Predictive performance

| Dataset | Primary metric | Project | Best eligible external baseline | Baseline value | Directional ratio |
|---|---|---:|---|---:|---:|
| Breast Cancer Wisconsin | ROC-AUC (higher is better) | 0.989778 | Logistic / Ridge | 0.989194 | 0.99941 |
| Danish occupancy | ROC-AUC (higher is better) | 0.939468 | CatBoost | 0.951437 | 1.01274 |
| Denver trees | ROC-AUC (higher is better) | 0.5 | CatBoost | 0.655039 | 1.31008 |
| SECOM | ROC-AUC (higher is better) | 0.5 | HistGradientBoosting | 0.691078 | 1.38216 |
| Statlog German Credit | ROC-AUC (higher is better) | 0.770989 | Logistic / Ridge | 0.784626 | 1.01769 |
| Annealing | Balanced accuracy (higher is better) | 0.610802 | Random Forest | 0.861111 | 1.4098 |
| Forest Types | Balanced accuracy (higher is better) | 0.85 | CatBoost | 0.88125 | 1.03676 |
| Glass | Balanced accuracy (higher is better) | 0.432456 | CatBoost | 0.794956 | 1.83824 |
| Pen Digits | Balanced accuracy (higher is better) | 0.927756 | CatBoost | 0.994546 | 1.07199 |
| Abalone | RMSE (lower is better) | 2.48144 | CatBoost | 2.23701 | 1.10927 |
| Automobile | RMSE (lower is better) | 4668.95 | XGBoost | 2682.1 | 1.74078 |
| Concrete | RMSE (lower is better) | 7.67013 | CatBoost | 6.22256 | 1.23263 |
| Edge task execution times | RMSE (lower is better) | 0.081945 | HistGradientBoosting | 0.062866 | 1.30349 |
| NYC Reservoir | RMSE (lower is better) | 2.86138 | Logistic / Ridge | 0.941486 | 3.03921 |

The quality ratio is project / baseline for lower-is-better loss, and baseline / project for higher-is-better scores. A ratio below one favors the project numerically; this is not a confidence interval or an equivalence test. Ties are broken alphabetically for choosing the resource comparator. Metrics differ between rows (ROC-AUC, balanced accuracy and RMSE); compare within each row, not the bar lengths as a cross-task quality ranking.

## Computational efficiency

| Dataset | Quality-selected comparator | Fit + preparation s: project / baseline | Training RSS MiB: project / baseline | Serialized KiB: project / baseline |
|---|---|---:|---:|---:|
| Breast Cancer Wisconsin | Logistic / Ridge | 0.0626 / 0.0891 | 142.1 / 143.16 | 39.9111 / 3.2207 |
| Danish occupancy | CatBoost | 0.079 / 0.5687 | 143.22 / 163.24 | 35.7197 / 86.3232 |
| Denver trees | CatBoost | 0.0611 / 0.3562 | 144.46 / 159.13 | 6.93457 / 54.3213 |
| SECOM | HistGradientBoosting | 0.1337 / 0.3262 | 150.08 / 163.96 | 285.553 / 553.978 |
| Statlog German Credit | Logistic / Ridge | 0.0776 / 0.1266 | 142.82 / 144.06 | 19.9854 / 4.94824 |
| Annealing | Random Forest | 0.1042 / 0.1901 | 144.66 / 149.93 | 141.73 / 648.439 |
| Forest Types | CatBoost | 0.0816 / 0.5497 | 142.28 / 159.66 | 121.932 / 534.812 |
| Glass | CatBoost | 0.0739 / 1.4199 | 142.57 / 163.81 | 106.035 / 1175.79 |
| Pen Digits | CatBoost | 0.1483 / 23.6405 | 145.82 / 185.18 | 262.249 / 5684.91 |
| Abalone | CatBoost | 0.0679 / 0.9913 | 142.25 / 161.72 | 22.835 / 208.816 |
| Automobile | XGBoost | 0.0688 / 0.2248 | 142.46 / 148.08 | 30.4404 / 100.729 |
| Concrete | CatBoost | 0.0633 / 1.1074 | 141.84 / 163.21 | 36.2119 / 802.013 |
| Edge task execution times | HistGradientBoosting | 0.0643 / 0.1378 | 142.66 / 146.34 | 10.3564 / 188.239 |
| NYC Reservoir | Logistic / Ridge | 0.0724 / 0.1029 | 142.12 / 142.52 | 44.6641 / 2.98242 |

The comparator is selected by predictive quality, not by resource cost. Training and RSS definitions are protocol-specific; do not compare the two repositories as if they used a common workload. Stored bytes are not loaded RAM. See the [benchmark overview](../README.md) for coverage, detailed timing and scientific limitations.

[Machine-readable summary](summary.csv). Regenerate from the recorded source CSV with `python benchmarks/plot_overview.py`. No new measurements are generated.
