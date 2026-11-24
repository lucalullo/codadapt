# Benchmark methodology and interpretation

## Evidence and scope

The competitive panel is the previously measured 2.1.0 development benchmark: 14 origins, seven estimators, 98 attempted jobs, 97 valid measurements, 83 paired comparisons and one missing pair (Glass/XGBoost). Fourteen 2.2.0 technical replays were reported separately. Internet Firewall is excluded from this panel. These exposed development sources are not independent confirmation data. The original report's outcome classifications are preserved. The separate technical panel uses frozen snapshots and synthetic fixtures; no new training or timing is claimed by this repository review.

Comparators: Logistic / Ridge (task-appropriate linear baseline), Random Forest, HistGradientBoosting, XGBoost, LightGBM and CatBoost. The reported environment was Windows x64, Python backend, one numerical thread. The report records fixed configurations, splits and seeds; the exact complete fit configuration, split indices and source datasets are not bundled. Full-precision aggregate measurements were authenticated against the preserved source and are included in [full_precision.json](data/full_precision.json). Consequently this is a transparent **measurement transcription**, not a fully executable reproduction of the original competitive experiment. See [provenance](data/provenance.json). Underlying datasets are not redistributed. Preserve source citations and applicable data-license obligations when independently reproducing the experiment.

## Dataset inventory

| Dataset | Task | CORE rows | VALID rows | Features | Categorical | VALID groups |
| --- | --- | --- | --- | --- | --- | --- |
| Breast Cancer Wisconsin | binary | 274 | 171 | 9 | 0 | 117 |
| Danish occupancy | binary | 3264 | 1280 | 6 | 1 | 20 |
| Denver trees | binary | 52 | 3372 | 4 | 3 | 1 |
| SECOM | binary | 201 | 279 | 590 | 0 | 10 |
| Statlog German Credit | binary | 426 | 267 | 20 | 13 | 267 |
| Annealing | multiclass | 340 | 213 | 38 | 32 | 211 |
| Forest Types | multiclass | 83 | 53 | 9 | 0 | 53 |
| Glass | multiclass | 91 | 57 | 9 | 0 | 57 |
| Pen Digits | multiclass | 3199 | 1998 | 16 | 0 | 1998 |
| Abalone | regression | 1781 | 1114 | 8 | 1 | 1114 |
| Automobile | regression | 84 | 54 | 24 | 8 | 52 |
| Concrete | regression | 431 | 271 | 8 | 0 | 113 |
| Edge task execution times | regression | 1236 | 502 | 3 | 1 | 12 |
| NYC Reservoir | regression | 588 | 252 | 4 | 1 | 6 |

CORE and VALID are frozen protocol roles; row and group counts are descriptive and do not establish independent subjects. No fresh holdout was opened.

## Metrics

- Classification primary: ROC-AUC for binary, balanced accuracy for multiclass; higher is better. Accuracy, macro F1, log loss and per-class recall supplement the primary metric. FPR is measured at the original native threshold, not a recalibrated common operating point.
- Regression primary: RMSE; MAE is additional. Lower is better. Do not aggregate raw errors across target scales.
- Efficiency: fit time includes preparation; job wall and cold snapshot are distinct. Inference latency includes raw input handling for batches 1 and 3,000; throughput is rows per second. Load includes hashing plus deserialization and is not certified cold-cache. Model bytes are serialized bytes, not in-memory footprint. Train RSS, tree peak, loaded RSS, retained/peak traced allocator and OS peak are distinct measurements.
- Ratios in `paired_comparisons.csv` are calculated from the displayed measurements; the original 15 joint point ratios are preserved separately. Differences at the printed precision may exist relative to full-precision receipts. Missing values are `ND` or empty where inapplicable, never zero.

## Statistical boundaries

There are 14 exploratory favorable, 40 inconclusive and 29 exploratory unfavorable comparisons, plus one missing comparison. Within the 40 inconclusive cases, 14 numerical directions favor CodAdapt, 24 favor the comparator and two have equal displayed primary values. No formal equivalence was established, and no global Holm-confirmed primary superiority was obtained. The original 95% intervals are conditional on the observed groups and original effect scale; they are not new tests or generalization guarantees. Do not pool paired comparisons as independent origins.

The pointwise screen for the 15 joint favorable pairs requires loss ratio ≤1.05, bytes ratio ≤0.50 and each of fit, batch-1, batch-3,000, peak training RSS and load ratios ≤1. It is not evidence of statistically certified Pareto dominance. Independent certification remains 0/20. Operating recall/FPR restrictions may rule out even favorable pointwise observations.

## Figure reproduction

Run `python benchmarks/plot_results.py` with NumPy and Matplotlib installed. This recreates figures from the included measurement CSV files only; it never fits a model, loads pickles, downloads datasets or changes statistical labels. It writes to `benchmarks/figures/`. Rebuilding the repository manifest after intentional edits is necessary. No performance estimate is obtained by running the plotting script.
