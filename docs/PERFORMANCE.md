# Performance and applicability

The supplied 68-page development benchmark report is the source evidence. This repository transcribes its displayed 97 algorithm-origin records, 83 paired comparisons and one missing comparison into standalone tables and figures. The [full-precision aggregate measurements](../benchmarks/data/full_precision.json) are supplied separately; they do not contain dataset rows. [Complete benchmark navigation](../benchmarks/README.md)

## Observed predictive advantages

The measured competitive quality and costs belong to CodAdapt 2.1.0. The 2.2.0
technical qualification verifies parity and separate implementation benefits.
There are 14 exploratory wins, 40 inconclusive comparisons, and 29 losses. Their
intervals remain conditional on the observed groups and the frozen protocol.

| Dataset | Competitor | Metric | CodAdapt 2.1.0 | Competitor | Recorded interpretation |
|---|---|---|---:|---:|---|
| Danish occupancy | Logistic Regression | ROC-AUC | 0.939468 | 0.839356 | Exploratory win |
| Danish occupancy | Random Forest | ROC-AUC | 0.939468 | 0.901309 | Exploratory win |
| Concrete | Ridge | RMSE | 7.67013 | 11.2413 | Exploratory win |
| Edge task execution times | Random Forest | RMSE | 0.0819445 | 0.180472 | Exploratory win |
| Danish occupancy | CatBoost | ROC-AUC | 0.939468 | 0.951437 | Inconclusive, numerical direction favors CatBoost |
| Annealing | Logistic Regression | Balanced accuracy | 0.610802 | 0.822531 | Loss |
| Pen Digits | CatBoost | Balanced accuracy | 0.927756 | 0.994546 | Loss |
| NYC Reservoir | Ridge | RMSE | 2.86138 | 0.941486 | Loss |

These examples direct readers to the full record. All algorithms, datasets,
metric values, uncertainty, unfavorable costs, and missing observations remain
available in the report. Operating recall and FPR must be assessed together with
ranking and probability quality.

## Performance-efficiency trade-offs

Fifteen points on six origins meet the loss margin, the byte ratio, and all five
other measured cost conditions simultaneously. The origins are Danish occupancy,
Denver trees, Statlog German Credit, Concrete, Edge task execution times, and NYC
Reservoir. Each point retains its original competitor and protocol. Their loss
ratio is at most 1.05, byte ratio at most 0.50, and the measured cost ratios meet
the preregistered conditions. Joint uncertainty certification remains incomplete.

For Danish occupancy versus Random Forest, point P02 records logloss 0.272298
versus 0.453711, with point reductions of 83.34% in fit time, 99.02% in model bytes,
88.14% in single-row inference, 92.27% in batch inference, 10.15% in training peak
RSS, and 91.78% in loading. These remain workload-specific measurements.

The 20 historical loss-byte points use fewer cost conditions. The stricter 15
joint points are identified separately in development benchmark report. Neither set constitutes a clean
independent Pareto confirmation. [All 15 joint cases](../benchmarks/COMPARISONS.md#joint-qualityresource-observations)

## Technical 2.2.0 versus 2.1.0

The following ratios are from the existing technical three-fixture panel at
batch 512. A value below one indicates less elapsed time in that case.

| Task | Combined 2.2 / three separate 2.1 calls | Combined 2.2 / efficient fused 2.1 | Prepared immutable input / fused 2.1 |
|---|---:|---:|---:|
| Binary | 0.3472275 | 1.013239 | 0.3579112 |
| Multiclass | 0.3345491 | 0.9947802 | 0.5733094 |
| Regression | 1.108536 | 1.092575 | 0.2076392 |

The nine-case prepared-input qualification has a defined scope. Setup, retained
codes, model copies, and memory peaks remain costs. Repeated requests must reuse
the authenticated immutable input contract. The regression combined path can add
overhead.

Across the archived models, median compressed/raw file ratios are approximately
0.2306 for binary, 0.2253 for multiclass, and 0.2556 for regression. Loaded RAM,
decompression, and latency retain their separate measurements. Fresh 2.2.0
training speed is unmeasured.

## Choosing a model

Choose CodAdapt where the measured quality, operational recall, and resource
trade-off fit the deployment. Prefer a measured stronger competitor where the
quality gap or operational limits dominate. The 40 inconclusive comparisons
remain inconclusive and establish no formal equivalence. On an unmeasured workload,
evaluate quality, preparation, training, inference, RAM, bytes, and loading together.

The optional serving and trace companion has separate qualification. Trace
reconstructs ordered memory contributions and adds work to prediction.
[Serving and trace evidence](../benchmarks/TECHNICAL.md#separate-lightweight-serving-and-trace)

[Complete applicability guide](../benchmarks/README.md)
· [Scientific and platform limitations](LIMITATIONS.md)
