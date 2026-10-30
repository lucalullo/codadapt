# Kaggle native/Python benchmark — exact returned 2.1.0 artifact

Three synthetic tasks, 3 split seeds (101/202/303), 18 fits plus 3 separate profiling fits.
Same underlying synthetic dataset per task; split seeds are not independent datasets.
No protected scientific TESTs, tuning or general superiority claim. All numbers below come from the original returned logs.

| Task | Seed | Python predict2048 ms | C++ predict2048 ms | Time reduction % |
|---|---:|---:|---:|---:|
|binary|101|2.818093|1.998128|29.10|
|binary|202|2.666808|1.972470|26.04|
|binary|303|2.733113|1.994531|27.02|
|multiclass|101|5.926929|3.662865|38.20|
|multiclass|202|6.283934|3.594386|42.80|
|multiclass|303|6.017370|3.714133|38.28|
|regression|101|2.837602|2.044810|27.94|
|regression|202|2.788605|1.930307|30.78|
|regression|303|2.879969|1.990126|30.90|

Observed multiclass time reductions range 38.20–42.80% in these medians; individual samples/p95 and other methods are retained. This is not a training speedup or accuracy gain.
The native and Python predictive metrics are identical on the measured panel. LightGBM results remain distinct; finite synthetic comparisons cannot establish universal ranking.
Whole-process load RSS is measured in fresh workers; benchmark in-process RSS is cumulative and not isolated model heap. Nonfatal Kaggle sitecustomize/`wrapt` startup warnings are retained in stderr; no host hooks were modified.
No speed is attributed to an unexecuted rebuilt/repaired wheel or automatic dispatcher.
