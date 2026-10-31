# CodAdapt

**Adaptive coded-memory learning for tabular data, with a scikit-learn-compatible Python API.**

CodAdapt is a machine-learning library for binary classification, multiclass
classification, and single-target regression. It encodes numerical and categorical
features and learns residual contributions through lookup memories. Preprocessing
is learned during fitting and reused when making predictions.

## Install

```bash
pip install codadapt
```

See the [installation guide](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md)
for local wheel installation and source-build requirements.

## Quick start

### Binary classification

```python
from sklearn.datasets import load_breast_cancer
from codadapt import CodAdaptClassifier

X, y = load_breast_cancer(return_X_y=True)
model = CodAdaptClassifier(random_state=42)
model.fit(X, y)

predictions = model.predict(X)
probabilities = model.predict_proba(X)
```

### Multiclass classification

The same classifier handles multiclass targets without a task parameter.

```python
from sklearn.datasets import load_iris
from codadapt import CodAdaptClassifier

X, y = load_iris(return_X_y=True)
model = CodAdaptClassifier(random_state=42)
model.fit(X, y)

predictions = model.predict(X)
probabilities = model.predict_proba(X)
```

Probability column `j` corresponds to `model.classes_[j]`.

### Regression

```python
from sklearn.datasets import load_diabetes
from codadapt import CodAdaptRegressor

X, y = load_diabetes(return_X_y=True)
model = CodAdaptRegressor(random_state=42)
model.fit(X, y)

predictions = model.predict(X)
```

These snippets demonstrate the interface using training rows. Evaluate predictive
quality on separate validation and test data.

## Highlights

- Adaptive coded-memory learning for numerical and categorical tabular features.
- Binary and multiclass classification through one estimator, plus a separate regressor.
- Preprocessing fitted on training data, with supported missing-value handling.
- `sample_weight` for both estimators and optional `class_weight="balanced"` for classification.
- Familiar estimator methods, parameter inspection, cloning, and Pipeline integration.
- Model persistence and integrity-checked serving utilities.

## API and scikit-learn integration

Use `CodAdaptClassifier` for single-label classification and `CodAdaptRegressor`
for single-target regression. Both accept `random_state` and provide `fit`,
`predict`, `get_params`, and `set_params`. Classifiers also provide `predict_proba`,
`decision_function`, and `classes_` after fitting.

Dense numerical NumPy arrays and supported pandas DataFrames are accepted.
Use DataFrames for mixed numerical and categorical columns; preserve the training
feature schema when predicting. Arbitrary mixed-object NumPy arrays are outside
the input contract.

The estimators can be cloned and used in scikit-learn pipelines. For parameter
semantics, categorical inputs, validation, and sample weights, see the
[API reference](https://github.com/lucalullo/codadapt/blob/main/docs/API.md).

## Compatibility and source installation

The package declares Python `>=3.10,<3.16`. Available wheels and supported dependency
combinations vary by platform; see the
[compatibility guide](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md)
for the exact runtime scope.

Training and feature encoding use Python/NumPy. Some wheels also include an optional
C++ inference backend, with a Python fallback. Installing a native wheel does not
enable automatic native execution on every platform; explicit backend selection
is described in the
[native inference guide](https://github.com/lucalullo/codadapt/blob/main/docs/NATIVE_PROFILE_DECISION.md).

A compatible prebuilt wheel needs no compiler. Building the optional native
extension from source requires a C++17 compiler and the build dependencies specified
by the package. Follow the
[source installation instructions](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md).

## Persistence

After fitting a model, save and restore it with `joblib`:

```python
import joblib

joblib.dump(model, "codadapt-model.joblib")
restored = joblib.load("codadapt-model.joblib")  # Trusted files only
restored_predictions = restored.predict(X)
```

Load only artifacts from trusted sources and keep compatible package and dependency
versions. Cross-version serialization compatibility is not guaranteed. See
[persistence and serving](https://github.com/lucalullo/codadapt/blob/main/docs/PERSISTENCE.md)
for export, integrity checks, and loading requirements.

## Limitations

Predictive quality, training cost, inference time, and memory use depend on the
dataset and configuration. CodAdapt does not claim universal superiority over
other tabular learning methods.

`class_weight="balanced"` is optional and does not guarantee higher accuracy or
better-calibrated probabilities. Backend controls are separate from the public
estimator parameters. See the
[limitations](https://github.com/lucalullo/codadapt/blob/main/docs/LIMITATIONS.md)
and [performance documentation](https://github.com/lucalullo/codadapt/blob/main/docs/PERFORMANCE.md).

## Documentation

- [API reference](https://github.com/lucalullo/codadapt/blob/main/docs/API.md)
- [Installation](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md)
- [Compatibility](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md)
- [Persistence and serving](https://github.com/lucalullo/codadapt/blob/main/docs/PERSISTENCE.md)
- [Examples](https://github.com/lucalullo/codadapt/tree/main/examples)
- [Performance](https://github.com/lucalullo/codadapt/blob/main/docs/PERFORMANCE.md)
- [Source repository](https://github.com/lucalullo/codadapt)

## License

CodAdapt is created by Luca Lullo and released under the
[MIT License](https://github.com/lucalullo/codadapt/blob/main/LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
