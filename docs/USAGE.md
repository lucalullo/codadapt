# Usage and examples

For an initial held-out example, see the [README](../README.md).

## API and scikit-learn integration

Use `CodAdaptClassifier` for single-label classification and `CodAdaptRegressor`
for single-target regression. Both accept `random_state` and provide `fit`,
`predict`, `get_params`, and `set_params`. Classifiers also provide `predict_proba`,
`decision_function`, and `classes_` after fitting.

When all classifier outputs are needed, use the fitted classifier:

```python
scores, probabilities, labels = model.predict_all(X)
```

For repeated inference on the same input, prepare it once and query row indices:

```python
session = model.prepare_inference(X)
scores, probabilities, labels = session.predict_rows([0, 1, 2])
```

The session owns a fixed model snapshot and encoded input. Rebuild it after
changing the model or input. These examples require a fitted classifier.

Dense numerical NumPy arrays and supported pandas DataFrames are accepted.
Use DataFrames for mixed numerical and categorical columns; preserve the training
feature schema when predicting. Arbitrary mixed-object NumPy arrays are outside
the input contract.

The estimators can be cloned and used in scikit-learn pipelines. For parameter
semantics, categorical inputs, validation, sample weights, and prepared-input
sessions, see the [API reference](https://github.com/lucalullo/codadapt/blob/main/docs/API.md).

## Compatibility and source installation

Version 2.2.0 declares Python `>=3.12`. The verified runtime profile is Windows
11 x64, CPython 3.12.10, the Python backend, and the recorded dependency versions.
Other operating systems, Python versions, and dependency combinations are not
covered by this qualification.

The source includes a restricted snapshot compatibility fix. The supplied
143-test suite passes locally on Windows with CPython 3.12.10 and the recorded
CI dependencies. Additional restored regression tests are listed in the
qualification records. GitHub-hosted Linux, Windows and macOS jobs must pass
before their results can be claimed. Software tests do not establish a
predictive improvement. See the
[compatibility guide](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md)
for the exact scope and known limitations.

Training and feature encoding use Python/NumPy. The 2.2.0 source build produces
a pure-Python wheel and does not build the historical optional C++ inference
extension. The previous native-wheel qualification applies to the corresponding
2.1.0 artifacts only.

A compatible pure-Python wheel needs no C++ compiler. Follow the
[source installation instructions](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md)
for local builds and dependency requirements.

## Persistence

After fitting a model, save and restore it with `joblib`:

```python
import joblib

joblib.dump(model, "codadapt-model.joblib")
restored = joblib.load("codadapt-model.joblib")  # Trusted files only
restored_predictions = restored.predict(X)
```

Version 2.2.0 also provides an integrity-checked snapshot format with optional
compression:

```python
model.save("codadapt-model.cda", compress=True)
restored = type(model).load("codadapt-model.cda")  # Trusted files only
```

An independently authenticated SHA-256 digest may also be supplied through the
`expected_sha256` argument. Snapshot creation refuses to overwrite existing
files. Load only artifacts from trusted sources and keep compatible package and
dependency versions. Native snapshots and producer-bound serving images have
different compatibility contracts. Serving images from before the snapshot
compatibility revision require their original producer or a fresh export.
Preserve the original model and environment
for rollback. See [persistence and serving](https://github.com/lucalullo/codadapt/blob/main/docs/PERSISTENCE.md)
for format limits, integrity checks, migration, and loading requirements.

