# CodAdapt

**Adaptive coded-memory learning for tabular data, with a simple scikit-learn-compatible Python API.**

CodAdapt is a non-tree, non-neural tabular learner for **binary classification,
multiclass classification, and single-target regression**. It combines train-only
multi-resolution encoding with compact, adaptive coded-memory tables. Training
uses Python/NumPy; an **optional C++17 inference kernel** accelerates some
qualified workloads without changing the learning rule.

> **Release status:** This repository is a **proposed CodAdapt 2.1.0 candidate**
> for manual review, **not an approved or published 2.1.0 release**. The previously
> published 2.0.0 remains separate. Qualification is limited to the exact
> environments listed in [Compatibility](docs/COMPATIBILITY.md) and
> [Qualification](docs/QUALIFICATION.md). No new multiclass accuracy improvement
> has been certified. See [Current gates](GATES_REPORT.md).

## Installation

To try **this 2.1.0 candidate locally**, create an isolated Python environment
and install a locally built distribution or a matching, authorized wheel:

```bash
python -m venv .venv
# Activate .venv using the instructions for your operating system.
python -m pip install .
python -c "import codadapt; print(codadapt.__version__)"
```

Building from this checkout without an explicit native-build setting produces
the Python implementation. To build the optional C++ extension, use an authorized
C++17 toolchain and the documented native-build procedure. A **prebuilt native
wheel does not require a compiler** on the consuming machine, but it must match
the operating system, CPU, CPython ABI, dependency profile, and OS permissions.

**`pip install codadapt` uses the version currently available on PyPI; it does
not install this unapproved 2.1.0 candidate.** Platform coverage is not implied
by the Python version range in package metadata. See
[installation and source builds](docs/INSTALLATION.md),
[dependency profiles](requirements/) and [actual compatibility](docs/COMPATIBILITY.md).

## Quick start

The examples below are self-contained. They use public scikit-learn datasets and
a held-out split to demonstrate the API; they are **not claims of predictive
superiority**.

### Binary classification

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from codadapt import CodAdaptClassifier

X, y = load_breast_cancer(return_X_y=True, as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
model = CodAdaptClassifier(random_state=42).fit(X_train, y_train)
labels = model.predict(X_test)
probabilities = model.predict_proba(X_test)
```

`CodAdapt` is an alias for `CodAdaptClassifier`. For imbalanced labels, the
optional `class_weight="balanced"` uses only effective training weights; it is
**not** the default and does not guarantee better Balanced Accuracy or logloss.

### Multiclass classification

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from codadapt import CodAdaptClassifier

X, y = load_iris(return_X_y=True, as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
model = CodAdaptClassifier(random_state=42).fit(X_train, y_train)
labels = model.predict(X_test)
probabilities = model.predict_proba(X_test)
# Probability columns follow model.classes_.
```

Multiclass learning uses shared encoding and separate one-vs-rest memory heads;
normalized sigmoid probabilities are **not** the output of a joint softmax
learner. This implementation is functional, but its predictive competitiveness
is mixed across datasets.

### Regression

```python
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from codadapt import CodAdaptRegressor

X, y = load_diabetes(return_X_y=True, as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
model = CodAdaptRegressor(random_state=42).fit(X_train, y_train)
predictions = model.predict(X_test)
```

More workflows: [binary](examples/basic_classification.py),
[multiclass](examples/basic_multiclass.py),
[regression](examples/basic_regression.py), and
[combined fit/predict/persistence](examples/basic_usage.py).

## Highlights

- **Three tasks, one familiar API:** `fit`, `predict`, `predict_proba` for
  classifiers, `get_params`, `set_params`, cloning and scikit-learn pipelines.
- **Mixed tabular data:** pandas numeric, string/category, boolean, nullable
  columns and missing values, with train-only schema and vocabulary learning.
- **Shared multi-resolution coding:** compact main-effect and coded interaction
  memories with residual refinement and validation-based stopping.
- **Budget-aware training:** `memory_budget_mb="auto"` estimates selected
  allocations; it is **not** a process-RAM guarantee.
- **Compact fitted state:** training caches are discarded; frozen memory tables
  support deterministic inference within the declared runtime contract.
- **Optional accelerated inference:** a C++17 ordered-reader kernel is available
  on qualified profiles; automatic dispatch and explicit native execution have
  **different** qualification scopes.
- **Optional experiments:** SafeBlend regression and an additive EBM compiler
  remain outside the stable default estimator path.

## Tabular inputs and defaults

Use pandas DataFrames for heterogeneous data; dense numeric NumPy arrays are
also supported. Integer-coded categories should be declared explicitly:

```python
model = CodAdaptClassifier(
    categorical_features=["postal_code"],
    random_state=42,
)
```

During prediction, DataFrame columns must match the fitted schema; column
order can be realigned, but missing/extra columns are rejected. Missing and
unseen categorical values have defined treatment. Mixed object NumPy arrays,
sparse inputs, raw datetimes, and infinite numeric features are outside the
declared contract.

Main defaults include `n_bins=32`, `n_tables=8`,
`features_per_table=3`, `table_size=256`, `lookup_budget=24`, `l2=5.0`,
`memory_budget_mb="auto"`, and `early_stopping=True`. A fixed `random_state`
helps reproducibility. The default classifier `class_weight` is `None`.
See [API and defaults](docs/API.md) and
[resource limitations](docs/LARGE_DATASETS.md).

## How the algorithm works

```text
Tabular input
    -> train-only shared numeric/categorical encoding
    -> nested coarse-to-fine resolutions
    -> bounded feature and interaction-memory selection
    -> residual memory updates with validation stopping
    -> compact fitted tables
    -> prediction (Python or qualified C++ reader)
```

For multiclass targets, each head learns its own memory corrections against a
shared input encoding. The optional C++ implementation optimizes inference,
**not** how training chooses memories or learns coefficients. See
[algorithm details](docs/ALGORITHM.md).

## Measured performance and limitations

In a historical preregistered **90-fit, three-source** classification panel,
CodAdapt achieved the following out-of-fold Balanced Accuracy (higher is better):

| Source | CodAdapt | HGB | LightGBM | RandomForest |
| --- | ---: | ---: | ---: | ---: |
| Music (4 classes) | 0.7450 | 0.8000 | 0.7875 | 0.7925 |
| Wireless (4 classes) | 0.9720 | 0.9810 | 0.9825 | 0.9850 |
| Rice (binary) | 0.92462 | 0.91943 | 0.91544 | 0.91843 |

CodAdapt led this panel on Rice; it trailed on Music and Wireless. These three
sources do **not** establish general superiority. For logloss, class recall,
model size, hardware, train time, reproducibility and unfavorable results, see
[performance](docs/PERFORMANCE.md) and [full benchmarks](BENCHMARKS.md).

An explicitly selected C++ reader reduced median multiclass batch-2048
inference latency by **41.58%** on a qualified Windows/Python 3.10.22 profile
and **41.18%** on Windows/Python 3.14.10, on the measured saved-model workloads.
**Normal automatic selection remains Python on those two profiles**; these
figures must not be presented as default acceleration. No native training
speedup or new multiclass accuracy gain is certified. See
[backend decision](docs/NATIVE_PROFILE_DECISION.md).

CodAdapt is CPU-only, single-label for classification and single-target for
regression. No multilabel, ranking, multi-output, sparse-input or incremental
`partial_fit` interface is claimed. See [known limits](docs/LIMITATIONS.md).

## Persistence, serving and optional components

Native estimators support pickle/joblib in compatible, trusted environments.
Never load untrusted pickle/joblib files. The serving export interface supports
source-bound artifacts:

```python
from codadapt.serving import export_model, load_model

receipt = export_model(model, "model.codadapt")  # model must be fitted
predictor = load_model(
    "model.codadapt",
    trusted=True,
    expected_sha256=receipt["artifact_sha256"],
)
```

Serving images are bound to the producer source contract. A previous 2.0.0 or
G6-R1 image must be used with its matching original runtime; this 2.1.0
candidate does not silently migrate old serving formats. SHA-256 verifies
consistency against a **trusted** digest, not authenticity by itself. See
[persistence](docs/PERSISTENCE.md) and [versioning](docs/VERSIONING.md).

Experimental features are opt-in: [SafeBlend](docs/SAFE_BLEND_EXPERIMENTAL.md)
and the [EBM compiler](docs/EBM_COMPILER.md). The compiler's optional dependency
may be blocked by platform security policy; it is not the native CodAdapt engine.

## Development and documentation

For local development, use a fresh environment and the declared development
extras and prerequisites:

```bash
python -m pip install -e ".[dev,benchmark]"
python -m pytest
python -m ruff check .
```

The default pytest command selects native, legacy and tools tests with a
documented historical packaging-harness exclusion. Some tests require a
matching local wheel/sdist, optional dependencies or a qualified native build;
read [installation](docs/INSTALLATION.md) and
[qualification](docs/QUALIFICATION.md) before interpreting failures.

- [API](docs/API.md) · [Algorithm](docs/ALGORITHM.md) · [Stability](docs/STABILITY.md)
- [Installation](docs/INSTALLATION.md) · [Compatibility](docs/COMPATIBILITY.md)
- [Performance](docs/PERFORMANCE.md) · [Persistence](docs/PERSISTENCE.md)
- [Examples](examples/) · [Benchmarks](BENCHMARKS.md)
- [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)
- [Changelog](CHANGELOG.md) · [Proposed release notes](RELEASE_NOTES.md)

## Project status and release decisions

**This 2.1.0 candidate is not approved for publication.** Windows x64 /
CPython 3.14.10 has a qualified finite local consumer path; Windows 3.10.22
has a qualified core with optional EBM DLL restrictions. Fresh 2.1.0 Windows
3.12, Linux, and macOS remain unqualified in the stated scope. A physically
independent project backup and the human review of historical repository
removals are still pending. See [gate report](GATES_REPORT.md),
[qualification matrix](docs/COMPATIBILITY.md),
[38 proposed historical removals](REMOVALS_REQUIRING_APPROVAL.md) and
[manual transfer instructions](ISTRUZIONI_TRASFERIMENTO_GITHUB.md).

Neither a ready source tree nor an installable local wheel implies authorization
to publish, replace the original 2.0.0, or claim that CodAdapt beats other
algorithms generally.

## License

CodAdapt is created by Luca Lullo and released under the [MIT License](https://github.com/lucalullo/codadapt/blob/main/LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
