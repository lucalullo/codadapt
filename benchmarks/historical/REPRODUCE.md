# Reproduce the historical classification panel

This recipe is separate from the 14-origin development panel. The original 2.1.0 source archive contained 15 public normalized folds and a fixed runner for six algorithms. All 15 fold SHA-256 values match that archive. The [original fold manifest](FOLD_MANIFEST_210.json) (seeds, row counts and digests) and [original runner](reproduce_classification.py) are retained without changes. The runner was designed to fit one frozen case. No fresh fit is executed by the documentation update.

## Environment and data

Use a separate environment with CodAdapt **2.1.0**, NumPy, pandas, scikit-learn, SciPy, threadpoolctl, psutil and LightGBM 4.6.0. The original results used Windows 11 x64, CPython 3.12.10, AMD Ryzen 7 255 and one numerical thread. The complete original dependency lock is not included in this historical receipt; record exact versions when rerunning. Matching fold bytes and seeds authenticates the split, but does not guarantee identical timing or scores across environments.

The folds are licensed CC BY 4.0; consult [source attribution](DATA_LICENSE.md). They are not redistributed here. Supply the original 2.1.0 checkout or ZIP containing `benchmarks/data/MANIFEST.json` and its 15 NPZ files. The commit recorded in the supplied original checkout is `b51c2c84929152966478e696e2710ed214090031`; the [historical source location](https://github.com/lucalullo/codadapt/tree/b51c2c84929152966478e696e2710ed214090031/benchmarks) may be used if it is available. The hosted availability of that exact commit was not verified. The staging tool also accepts a local copy of the old ZIP, verifies every fold and creates a separate replay directory; it performs no fits and no network access.

From the current repository root:

```bash
python benchmarks/historical/prepare_replay.py --source PATH_TO_210_ZIP_OR_CHECKOUT --output benchmark_runs/historical_210
```

Run the following commands in an environment with CodAdapt 2.1.0 installed (not the current package). Each output path must not already exist. The staging tool verifies the original runner bytes before copying; outputs are separate from the recorded CSV. Other algorithms are `CodAdaptBalanced`, `DecisionTree`, `RandomForest`, `HGB` and `LightGBM`. Fold IDs end in 0 through 4; their seeds are 17, 43, 89, 137, 223. The frozen NPZ files embody the original split; no newly generated split indices are asserted.

## Music

[Turkish Music Emotion (UCI 862)](https://archive.ics.uci.edu/dataset/862/turkish+music+emotion), 320 training / 80 evaluation rows per fold.

```bash
python benchmark_runs/historical_210/run.py --case music_0 --algorithm CodAdapt --output benchmark_runs/music_0_codadapt
```

## Wireless

[Wireless Indoor Localization (UCI 422)](https://archive.ics.uci.edu/dataset/422/wireless+indoor+localization), 1600 training / 400 evaluation rows per fold.

```bash
python benchmark_runs/historical_210/run.py --case wireless_0 --algorithm RandomForest --output benchmark_runs/wireless_0_rf
```

## Rice

[Rice Cammeo and Osmancik (UCI 545)](https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik), 3048 training / 762 evaluation rows per fold.

```bash
python benchmark_runs/historical_210/run.py --case rice_0 --algorithm LightGBM --output benchmark_runs/rice_0_lgbm
```

Compare with [recorded fold observations](observed_classification.csv) and the [historical panel](../HISTORICAL_210.md). Repeat for the remaining folds and algorithms only if a full replay is desired. The original runner specifies the estimator parameters, defaults, thread limits and timings; the wrapper rejects the wrong CodAdapt version. New measurements are distinct from the archived ones. Physical independence of artists, recording sessions, buildings and grain lots was not established, so this does not provide independent validation.
