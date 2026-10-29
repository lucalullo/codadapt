# Reproduce the fixed classification panel
These are historical observations, not a new experiment or universal ranking.
Install the verified runtime pins plus lightgbm==4.6.0 and psutil==7.2.2.
Each of the 15 cases in data/MANIFEST.json can be run for each of the six
presets (90 total). Example, from repository root:
`python benchmarks/reproduce_classification.py --case music_0 --algorithm HGB --output benchmark_runs/music0_hgb`.
Use a new output directory and one fresh process per case. For the original
order, rotate algorithm order by case index modulo 6. Set numerical thread
environment variables to 1 before Python startup. The script also limits
threadpools. Do not rerun completed cases merely to choose favorable scores.

Split: StratifiedGroupKFold(5,shuffle=True,random_state=20261028), with groups
defined by exactly identical predictor rows. Fold learner seeds17,43,89,137,223.
DataFrames float64, features renamed f0..., no scaling, imputation or tuning.
The packaged folds preserve every original normalized value and label; object
string labels are stored as Unicode in NPZ to avoid pickle loading.
CodAdapt/default and balanced, DecisionTree/default, RandomForest100/one thread,
HGB100 and LightGBM100/lr0.1/leaves31. Internal stopping stays algorithm-specific;
this is not a causal comparison at equal functional capacity.

Training timer excludes data acquisition. Inference batches1/32/2048 use3warmups
and7timings, median/p95. Repeated query rows do not create new predictive data.
Model size is protocol5pickle; process RAM includes imports, inputs and model.
A non-Windows RSS observation is not a Windows lifetime peak measurement.
Aggregate held-out predictions over the five folds for OOF metrics; do not
average different-task error scales. Overlapping training folds are not five
independent datasets. Only three source units: no general statistical superiority.
These sources are now exposed and cannot confirm a rule designed from their results.
