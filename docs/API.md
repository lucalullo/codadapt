# Python API

`from codadapt import CodAdaptClassifier, CodAdaptRegressor`.
Both estimators implement `fit(X, y, sample_weight=None, eval_set=None)`,
`predict`, `get_params`, `set_params`, scikit-learn cloning and Pipeline use.
Classifier additionally provides `predict_proba`, `decision_function` and
`classes_`; probability columns follow `classes_`. More than two effective
classes use shared encoding and independent OVR heads with normalized sigmoid
probabilities. This is not a softmax learner.

Main defaults: n_bins=32, max_categories=128, n_tables=8,
features_per_table=3, table_size=256, lookup_budget=24, l2=5.0,
memory_budget_mb="auto", early_stopping=True, validation_fraction=0.15,
random_state=None. Set random_state for repeatable runs. See constructor
signatures for the full parameter list; do not treat private selectors as
stable public hyperparameters.

Classifier `class_weight` accepts None or "balanced". If positive TRAIN
sample masses are W_k, total W and K effective classes, multiply each
sample weight by W/(K*W_k). Zero-weight rows do not affect effective class
masses; validation/test labels do not participate. Balancing is applied once
before the multiclass heads. It does not guarantee better accuracy or logloss.
The regressor has no class_weight parameter.

Dense numeric NumPy arrays and supported pandas numeric/categorical/missing
values are accepted. Mixed object NumPy arrays are outside the declared
input contract; use DataFrames. Rare classes may warn. Quantile-based coding
is not invariant to replacing weighted rows with repeated unweighted rows.
The four historical expected sklearn failures remain documented in tests.

`codadapt.experimental` retains optional historical components; they are not
the default coded-memory engine. The optional EBM extra is interpret-core0.7.8.
No new experimental multiclass strategy is included.
