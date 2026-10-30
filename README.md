# CodAdapt

**Original adaptive coded-memory learning for tabular data.** CodAdapt 2.1.0
supports binary classification, multiclass classification and regression through
a scikit-learn-compatible Python API. Author: **Luca Lullo**. License: **MIT**.

## Design

CodAdapt learns compact residual memories over train-only numeric and categorical
codes. **Training and encoding use Python/NumPy.** An optional **C++17/pybind11
reader accelerates fitted-memory inference** while preserving the established
order of numerical operations. It is not a C++ training engine or a wrapper
around another predictive algorithm.

The estimators support sample weights, mixed/missing data through supported
pandas inputs, cloning and Pipeline use. `class_weight="balanced"` is computed
internally from positive TRAIN weight masses and combined once with sample
weights. The default is None; balancing does not guarantee better probabilities.

## Installation

Once the owner has published the approved files, install from PyPI:

```text
python -m pip install codadapt==2.1.0
```

This documentation does not assert that those files have already been uploaded.
Before publication, install an approved local wheel instead:

```text
python -m pip install /path/to/codadapt-2.1.0-py3-none-any.whl
```

A pure wheel uses the Python backend. A compatible prebuilt native wheel needs
no compiler. A native source build requires C++17 and a platform SDK; Linux source
builds request the extension by default. Set `CODADAPT_BUILD_NATIVE=0` for a pure
source build or `CODADAPT_BUILD_NATIVE=1` to request native explicitly. Compiler,
ABI and security errors remain visible. Python metadata accepts >=3.10,<3.16;
this is not a declaration that every patch, dependency combination and OS was tested.

## Executable example: multiclass classification

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from codadapt import CodAdaptClassifier

X, y = make_classification(
    n_samples=360, n_features=8, n_informative=5,
    n_redundant=1, n_classes=3, random_state=42,
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42,
)
model = CodAdaptClassifier(random_state=42)
model.fit(X_train, y_train)
prediction = model.predict(X_test)
probability = model.predict_proba(X_test)
print(prediction.shape, probability.shape)
```

For binary classification use the same estimator with two target classes.
For regression import `CodAdaptRegressor`; it provides `fit` and `predict` and
has no class_weight parameter. Complete examples:
[binary](https://github.com/lucalullo/codadapt/blob/main/examples/basic_classification.py),
[multiclass](https://github.com/lucalullo/codadapt/blob/main/examples/basic_multiclass.py),
[regression](https://github.com/lucalullo/codadapt/blob/main/examples/basic_regression.py).

## Persistence and serving

```python
import joblib
from codadapt.serving import export_model, load_model

joblib.dump(model, "model.joblib")
restored = joblib.load("model.joblib")  # load only a trusted file
receipt = export_model(model, "model.codadapt")
served = load_model(
    "model.codadapt", trusted=True,
    expected_sha256=receipt["artifact_sha256"],
)
prediction_after_load = served.predict(X_test)
```

Serving images retain their exact producing source contract and numerical profile.
No format migration or old-producer allowlist is introduced. Preserve matching
old runtimes for earlier images. General cross-major NumPy/pandas pickle
portability is not promised. Hashes check integrity against a trusted reference;
they do not make unknown pickle/joblib files safe.

## Explicit C++ inference

On a profile with a matching installed extension, use this version-specific
advanced context without changing estimator parameters or saved state:

```python
from codadapt._inference import inference_backend

with inference_backend("native"):
    native_prediction = model.predict(X_test)
    native_probability = model.predict_proba(X_test)
```

The `_inference` context is private, not a new stable public estimator option.
An explicit native request fails visibly if the extension is absent or invalid.
**Automatic dispatch is unchanged:** normal Linux/macOS and other unadmitted
profiles use Python. Only the existing exact historical Windows/Python 3.12.10
guard can opt in automatically when its dependency profile and extension match.
No new Linux, macOS or Windows automatic profile is admitted by this release work.

## Platform evidence and artifact qualification

The maintainer reports four green `native-complete.yml` source-workflow runs:

| Source workflow reported by maintainer | Python | Evidence status here |
|---|---|---|
| Linux x86-64 | 3.13.15 | Owner-reported green; not independently replayed here |
| Windows | 3.13.15 | Owner-reported green; inspect raw receipt for architecture |
| macOS 15 Apple Silicon | 3.13.15 | Owner-reported green; not independently replayed here |
| macOS 15 Intel | 3.13.15 | Owner-reported green; not independently replayed here |

The maintainer also reports successful binary/multiclass/regression, persistence
and explicit C++ inference on Kaggle from source commit
`1637747ab0fa4996ca180d3220053bab36b014ec`. These are source-level reports;
**they do not automatically qualify newly built wheel/sdist files**. Final-package
evidence must bind their exact SHA-256, installation, import, calls and tests.

Separately, previously acquired original Kaggle wheel receipts were verified for
their exact Linux/CPython 3.13.15/dependency profile: 1,079 PASS, 3 SKIP, 4 XFAIL,
200 actual C++ calls and 35 exact arrays; the pure consumer had 1,029 PASS,
53 SKIP and 4 XFAIL. Those counts are not new tests of the current packages.
A host-tagged `linux_x86_64` wheel is not a manylinux wheel. Linux portability
requires a real baseline build/audit/repair and tests of the final wheel. macOS
LightGBM benchmarks additionally need Homebrew libomp; it is not a CodAdapt
predictive-engine dependency.

## Limits and performance

No general superiority over LightGBM, XGBoost or CatBoost is claimed. Faster
inference does not establish greater predictive accuracy or lower process RAM.
The recorded synthetic Kaggle panel measured multiclass batch-2048 median time
reductions of 38.20%, 42.80% and 38.28% over Python on three related splits;
these are finite results from the original wheel, not training speedups or
measurements of a new wheel. Multiclass predictive research remains separate.

Use supported pandas inputs for mixed categorical/missing data; arbitrary mixed
NumPy object matrices are outside the input contract. Weighted quantile coding
is not invariant to replacing weighted rows with repeated unweighted rows.
Optional experimental components are separate from the default engine.

## Documentation and qualification

- [API](https://github.com/lucalullo/codadapt/blob/main/docs/API.md)
- [Installation](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md)
- [Persistence](https://github.com/lucalullo/codadapt/blob/main/docs/PERSISTENCE.md)
- [Compatibility and evidence](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md)
- [Build and native-wheel procedures](https://github.com/lucalullo/codadapt/blob/main/docs/BUILD_DISTRIBUTIONS.md)
- [Qualification](https://github.com/lucalullo/codadapt/blob/main/docs/QUALIFICATION.md)
- [Benchmarks and limitations](https://github.com/lucalullo/codadapt/blob/main/docs/PERFORMANCE.md)
- [MIT license](https://github.com/lucalullo/codadapt/blob/main/LICENSE)

Run `python tools/verify_repository.py` against the final manifest. Workflows are
manual qualification procedures and never publish. Release, TestPyPI and PyPI
remain the owner's decisions. The README is embedded in distribution metadata:
changing GitHub alone does not update a description already uploaded to PyPI.
