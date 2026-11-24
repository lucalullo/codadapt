# API

The public estimators are `CodAdaptClassifier` and `CodAdaptRegressor`.
`CodAdapt` remains an alias for the classifier. Both estimators retain `fit`,
`predict`, `get_params`, and `set_params`, with scikit-learn cloning and Pipeline
integration. Classifiers expose `decision_function`, `predict_proba`, and
`classes_` after fitting.

## Classification

```python
from codadapt import CodAdaptClassifier

classifier = CodAdaptClassifier(random_state=42)
classifier.fit(X_train, y_train)
scores, probabilities, labels = classifier.predict_all(X_query)
```

`predict_all` evaluates the native scores once. Binary decisions retain the native
`score > 0` rule. Multiclass probabilities, class order, and tie-breaking retain
their verified behavior. Probability column `j` corresponds to `classes_[j]`.
`sample_weight` and optional `class_weight="balanced"` keep their existing semantics.

## Regression

```python
from codadapt import CodAdaptRegressor

regressor = CodAdaptRegressor(random_state=42)
regressor.fit(X_train, y_train)
predictions = regressor.predict(X_query)
```

`predict_all` returns a one-element tuple in regression. Use `predict` when a
single output is required. Its additional overhead is documented in the
[technical performance evidence](PERFORMANCE.md).

## Parameters and weights

`fit(X, y, sample_weight=None, eval_set=None)` uses single-target labels or values.
Inherited main defaults include `n_bins=32`, `max_categories=128`, `n_tables=8`,
`features_per_table=3`, `table_size=256`, `lookup_budget=24`, `l2=5.0`,
`memory_budget_mb="auto"`, `early_stopping=True`, `validation_fraction=0.15` and
`random_state=None`. See constructor signatures for the full list. Set a seed for
repeatable experiments; private backend selectors are not stable hyperparameters.
`class_weight="balanced"` rescales positive training class masses only, once before
multiclass heads. It does not guarantee better accuracy or calibration. The regressor
has no class-weight parameter.

## Inputs

Dense numeric NumPy arrays and supported pandas DataFrames are accepted. Preserve
column names, order, and the training schema. DataFrames support the documented
numeric, categorical, boolean, and missing-value handling. Arbitrary mixed-object
NumPy arrays are outside this contract. Encoding is learned from construction data.

## Prepared immutable inputs

```python
session = classifier.prepare_inference(X_fixed)
scores, probabilities, labels = session.predict_rows(row_ids)
```

`row_ids` contains valid integer indices into `X_fixed`. Preparation validates and
encodes the input and owns a frozen model copy. Subsequent mutations of the
original input or estimator leave the session fixed. Account for preparation,
retained codes, the model copy, and temporary peaks. The qualification covers nine
observed cases.

## Persistence and serving

`save`, `load`, optional zlib compression, legacy native snapshots, and
producer-bound serving images follow the [persistence contract](PERSISTENCE.md).
The separate stdlib reader and trace companion remain optional attachments.

Inherited `codadapt.experimental` modules retain their pre-existing API status.
The 2.2.0 technical review changes neither the learning algorithm nor these
modules' qualification. The learning code is unchanged; the codec and serving identity files were revised.
