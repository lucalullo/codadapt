# Measured competitiveness and limitations

Historical fixed panel: 90 fits, three public sources, five grouped folds,
six fixed presets, tuning budget zero. Windows11 x64, AMD Ryzen7 255,
8physical/16logical cores, about32GB RAM, one numerical thread. CPU affinity
and frequency were not pinned. Python3.12.10, NumPy2.5.4, pandas3.1.0,
SciPy1.18.1, sklearn1.9.1, LightGBM4.6.0. No fits repeated for this handoff.

| Source | CodAdapt BA / logloss | RandomForest | HGB | LightGBM |
|---|---|---|---|---|
| Music (4classes) | .7450 / .71474 | .7925 / .66724 | .8000 / .85197 | .7875 / .74840 |
| Wireless (4classes) | .9720 / .13803 | .9850 / .05875 | .9810 / .08621 | .9825 / .07270 |
| Rice (binary) | .92462 / .19845 | .91843 / .34571 | .91943 / .22696 | .91544 / .23246 |

Balanced CodAdapt matches default on Music/Wireless here; Rice balanced BA
.92067 and logloss .19992 are worse overall despite class-recall tradeoffs.
All fold observations, accuracy and macro-F1 are in benchmarks/observed_classification.csv.
The reproduction tool also reports per-class recall and confusion matrices.
Music has65 of102 CodAdapt errors between relax and sad; their recall is
.69/.53. This locates errors but does not identify a representation, selection
or optimization cause. No new multiclass rule is admitted or integrated.

Music CodAdapt mean fit48.26ms, batch2048 inference3.672ms, pickle87.86KiB;
HGB531.96ms/32.65ms/634.25KiB, RF222.08ms/10.00ms/972.14KiB.
Whole-process RAM is different from model bytes or incremental allocator usage.
Raw per-fold measurements retain slower and unfavorable cases. The three-source
inference is underpowered; adjusted comparisons do not establish general superiority.

Earlier finite engineering workloads measured native multiclass inference
36.83% faster than the original Python reader at batch2048; the later guarded
numeric-DataFrame optimization reduced median18.27% against its immediate
predecessor. These are different experiments and the percentages must not be
added. Batching reduced whole-process peak working set11.6–13.3%, with MC
latency+1.8% and p95+5.7% on that measured large-batch workload.
No native training speedup or new predictive-accuracy improvement is claimed.

New Python3.10/3.14 Windows receipts establish finite native/Python equality,
separate clean pure/native consumers, and timing/memory observations. They do
not turn these synthetic probes into independent predictive benchmarks.
See compatibility for exact profiles and the conservative automatic dispatcher.

## Final explicit-native check

A separate serial, no-fit benchmark on saved engineering models measured MC
batch2048 median reductions of41.58% on Windows3.10.22 and41.18% on3.14.10.
Normal automatic predictions remain Python on these profiles. See
[NATIVE_PROFILE_DECISION.md](NATIVE_PROFILE_DECISION.md) for process repetitions,
exact equivalence, p95, RAM, all batch sizes and finite limitations. These gains
are not added to historical percentages or interpreted as accuracy improvements.
