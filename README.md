# CodAdapt

**Adaptive coded-memory learning for tabular data, with a scikit-learn-compatible Python API.**

CodAdapt is a machine-learning library for binary classification, multiclass classification, and single-target regression. It learns compact coded representations of numerical and categorical features and uses residual memories to produce predictions. The estimators provide familiar `fit`, `predict`, and, for classification, `predict_proba` methods.

## Installation

Install CodAdapt 2.1.0 from PyPI:

```bash
python -m pip install codadapt==2.1.0
```

For source builds and platform-specific installation requirements, see the [installation guide](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md). The package declares Python `>=3.10,<3.16`; the declared range is not a guarantee that every environment has been independently tested. See the [compatibility notes](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md).

## Quick start

### Binary classification

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from codadapt import CodAdaptClassifier

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

model = CodAdaptClassifier(random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)
print("Accuracy:", accuracy_score(y_test, predictions))
print("Probability shape:", probabilities.shape)
```

### Multiclass classification

The same classifier supports more than two classes, with probability columns corresponding to `model.classes_`.

```python
from sklearn.datasets import load_wine
from codadapt import CodAdaptClassifier

X, y = load_wine(return_X_y=True)
model = CodAdaptClassifier(random_state=42).fit(X, y)
probabilities = model.predict_proba(X[:5])
print("Classes:", model.classes_)
print("Probability shape:", probabilities.shape)
```

### Regression

```python
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from codadapt import CodAdaptRegressor

X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = CodAdaptRegressor(random_state=42)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
print("MAE:", mean_absolute_error(y_test, predictions))
```

These examples illustrate the API, not a general accuracy guarantee. Evaluate predictive quality on data kept separate from training.

## What makes CodAdapt different?

- **Coded-memory learning.** Numerical and categorical features are encoded into compact representations used to build residual predictive memories.
- **Three supervised tasks.** One classifier handles binary and multiclass targets; a separate regressor handles continuous targets.
- **Training-only preprocessing.** Supported numerical, categorical, and missing-value inputs are processed without using test data to learn encodings.
- **Sample weighting.** Both estimators accept `sample_weight`; the classifier also supports optional `class_weight="balanced"`.
- **scikit-learn integration.** Estimators support cloning and Pipeline usage with familiar method conventions.
- **Model persistence.** Fitted models can be saved and restored in trusted environments, with additional integrity-checked serving utilities.

The method is distinct from conventional gradient-boosted tree training, but no universal predictive advantage over established tabular learners is claimed.

## Data and API

CodAdapt accepts dense numeric NumPy arrays and supported pandas DataFrames. Use DataFrames for mixed categorical columns and missing values; arbitrary mixed-object NumPy arrays are not part of the supported input contract.

```python
from codadapt import CodAdaptClassifier, CodAdaptRegressor

classifier = CodAdaptClassifier(random_state=42, class_weight="balanced")
regressor = CodAdaptRegressor(random_state=42)
```

`class_weight="balanced"` is optional and does not guarantee higher accuracy or better-calibrated probabilities. For parameters, input rules, and sample-weight behavior, see the [API reference](https://github.com/lucalullo/codadapt/blob/main/docs/API.md).

## Persistence

Models can be stored with `joblib` and restored in compatible, trusted environments:

```python
import joblib

joblib.dump(model, "codadapt-model.joblib")
restored = joblib.load("codadapt-model.joblib")  # Trusted files only
```

Load only artifacts from trusted sources. Cross-version serialization compatibility is not guaranteed. For serving export, source-contract verification, and loading requirements, see [persistence and serving](https://github.com/lucalullo/codadapt/blob/main/docs/PERSISTENCE.md).

## Execution and compatibility

Training and feature encoding run in Python/NumPy. Compatible distributions may also include an optional compiled inference backend. Its availability and automatic selection depend on the installed package and verified environment; a native wheel does not imply native execution on every platform. Advanced backend usage is documented in the [native inference guide](https://github.com/lucalullo/codadapt/blob/main/docs/NATIVE_PROFILE_DECISION.md).

Platform support, package-build requirements, and qualification scope are maintained in the [compatibility documentation](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md). Native Linux distributions require genuine manylinux qualification before being described as portable manylinux wheels.

## Limitations

CodAdapt is an independent approach to tabular learning. Accuracy, training costs, inference time, and memory use depend on the dataset and configuration. Existing tests establish functional behavior within their tested environments, not universal superiority over LightGBM, XGBoost, CatBoost, or other methods.

Model persistence requires trusted inputs and compatible dependencies. Advanced inference controls are not stable public estimator parameters. See the [limitations](https://github.com/lucalullo/codadapt/blob/main/docs/LIMITATIONS.md) and [performance documentation](https://github.com/lucalullo/codadapt/blob/main/docs/PERFORMANCE.md).

## Documentation

- [API reference](https://github.com/lucalullo/codadapt/blob/main/docs/API.md)
- [Installation](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md)
- [Compatibility](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md)
- [Persistence and serving](https://github.com/lucalullo/codadapt/blob/main/docs/PERSISTENCE.md)
- [Examples](https://github.com/lucalullo/codadapt/tree/main/examples)
- [Performance](https://github.com/lucalullo/codadapt/blob/main/docs/PERFORMANCE.md)
- [Source repository](https://github.com/lucalullo/codadapt)

## License

CodAdapt is created by Luca Lullo and released under the [MIT License](https://github.com/lucalullo/codadapt/blob/main/LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
