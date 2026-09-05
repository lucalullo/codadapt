# CodAdapt

CodAdapt is a compact experimental machine-learning library for tabular data. Version 0.1.0 uses
**adaptive coded memory with shared multi-resolution encoding** for binary classification and
single-target regression, while preserving a scikit-learn-style estimator interface.

CodAdapt 0.1.0 is an experimental pre-1.0 release. It is suitable for controlled experiments,
Kaggle notebooks, and reproducible evaluation; it is **not** a claim that CodAdapt will outperform
LightGBM or other established tabular models on every dataset.

## Highlights in 0.1.0

- one simple classifier API through `CodAdapt`, plus `CodAdaptClassifier` and `CodAdaptRegressor`;
- `fit`, `predict`, `predict_proba`, `get_params`, `set_params`, cloning, pipelines, and cross-validation compatibility;
- automatic numerical, string/object, categorical, boolean, nullable-boolean, and missing-value handling for pandas DataFrames;
- dense numeric NumPy input, with optional explicit categorical column indices;
- train-only quantile buckets and categorical vocabularies, with distinct buckets for missing, rare observed, and unseen categories;
- one shared finest encoding that derives nested coarse-to-fine integer resolutions without re-encoding the raw input at every level;
- adaptive residual-memory levels with validation-based stopping and feature-level stopping;
- compact collision-aware coded interaction tables controlled by a lookup budget;
- sample weights, explicit validation sets, deterministic random states, and best-state restoration when early stopping is enabled;
- pickle/joblib persistence and CPU-only NumPy execution;
- Python 3.10-3.12 compatibility gates.

The release default is the architecture selected by the internal development process: shared
multi-resolution encoding feeding adaptive coded memory. No experimental strategy flag is required.

## Installation

From GitHub after the `v0.1.0` tag is published:

```bash
python -m pip install "git+https://github.com/lucalullo/codadapt.git@v0.1.0"
```

In Kaggle:

```python
!pip install -qq git+https://github.com/lucalullo/codadapt.git@v0.1.0
```

From a local checkout:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
```

For tests, lint, package checks, and optional LightGBM benchmarks:

```bash
python -m pip install -e ".[dev,benchmark]"
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Runtime requirements are NumPy 1.24+, pandas 2.0+, and scikit-learn 1.3+. LightGBM and
`psutil` are optional benchmark-only dependencies; they are not required to use CodAdapt.

## Quick start

### Binary classification

```python
import pandas as pd
from codadapt import CodAdapt

X = pd.DataFrame(
    {
        "age": [22, 45, 31, 54, 28, 61, 38, 49],
        "income": [32_000, 78_000, None, 91_000, 46_000, 105_000, 58_000, None],
        "city": ["Rome", "Milan", "Rome", "Turin", None, "Milan", "Rome", "Turin"],
    }
)
y = [0, 1, 0, 1, 0, 1, 0, 1]

model = CodAdapt(random_state=42, verbosity=0, early_stopping=False)
model.fit(X, y)

labels = model.predict(X)
probabilities = model.predict_proba(X)[:, 1]
```

`early_stopping=False` is used above only because the toy dataset is very small. On normal datasets
the default `early_stopping=True` creates a deterministic internal validation split.

### Regression

```python
from codadapt import CodAdaptRegressor

model = CodAdaptRegressor(random_state=42, verbosity=0)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

## Data handling

With pandas DataFrames, numeric columns are treated as numeric and supported string/object,
`category`, boolean, and nullable-boolean columns are treated as categorical. Missing values are
handled natively.

Integer-coded categorical columns should be declared explicitly:

```python
model = CodAdapt(categorical_features=["postal_code"], random_state=42)
```

For dense NumPy arrays, input must be numeric. Integer column indices may be supplied through
`categorical_features` when numeric codes should be treated as categories.

At prediction time, DataFrames must contain the same unique column names used during fitting.
Different column order is accepted and realigned; missing or unexpected columns are rejected.

## Validation and sample weights

Without an explicit validation set, CodAdapt creates an internal validation split when
`early_stopping=True`. For a user-controlled holdout:

```python
model.fit(X_train, y_train, eval_set=(X_valid, y_valid))
```

Preprocessing is fitted only on the effective training rows. Validation data does not determine
quantile thresholds, categorical vocabularies, or adaptive code proposals.

Per-row non-negative weights are supported:

```python
model.fit(X_train, y_train, sample_weight=weights)
```

Rows with zero weight are removed before preprocessing and validation splitting.

## Main parameters

The defaults are intended to be the starting point. Advanced users can control model size and
training behavior explicitly:

```python
model = CodAdapt(
    n_bins=32,
    n_tables=8,
    features_per_table=3,
    table_size=256,
    max_iter=20,
    lookup_budget=24,
    l2=5.0,
    early_stopping=True,
    random_state=42,
    verbosity=0,
)
```

See [docs/API.md](docs/API.md) for the complete parameter contract.

## How CodAdapt works

At a high level:

```text
raw tabular features
        ↓
train-only shared bucket encoding
        ↓
nested coarse-to-fine integer resolutions
        ↓
adaptive feature and interaction allocation
        ↓
compact coded-memory lookups
        ↓
residual corrections across accepted levels
        ↓
prediction
```

Numeric features are discretized from train-only quantiles. Categorical features use stable integer
buckets. The finest representation is computed once and mapped to coarser resolutions through cached
integer maps. Each accepted level adds compact main-effect and coded interaction tables; validation
stopping prevents unnecessary deeper levels. Prediction is then dominated by integer addressing,
table lookups, and additions rather than tree traversal or neural-network layers.

See [docs/ALGORITHM.md](docs/ALGORITHM.md) for the detailed formulation.

## Performance

The frozen local comparison behind 0.1.0 used 12 datasets and five shared splits per dataset against
budget-matched LightGBM. CodAdapt did **not** win mean predictive quality on those datasets. It did,
however, win median raw-input inference latency on 10/12 datasets and retained-model memory on 12/12.

With ratios defined as `LightGBM / CodAdapt`, the median fit-speed ratio was `0.887x`, inference-speed
ratio `1.258x`, and retained-model-memory ratio `8.830x`. Therefore the measured release candidate
was slightly slower in median training overall, faster in median inference, and substantially more
compact in retained model memory on that limited benchmark.

These are local experimental results, not universal throughput or quality claims. Hardware, dataset,
versions, thread settings, split choice, and workload can change the outcome. See
[BENCHMARKS.md](BENCHMARKS.md) for the disclosure and use the bundled lightweight runner for your own
sanity comparisons:

```bash
python benchmarks/run_benchmarks.py --quick
```

## scikit-learn use

CodAdapt follows the estimator parameter protocol, so standard composition works:

```python
from codadapt import CodAdapt
from sklearn.base import clone
from sklearn.model_selection import cross_val_score

base = CodAdapt(max_iter=10, early_stopping=False, random_state=7)
copy = clone(base)
scores = cross_val_score(copy, X, y, cv=3, scoring="roc_auc")
```

The classifier returns the original two class labels from `predict`; `predict_proba` returns two
columns in the order stored in `classes_`. The regressor uses the same common estimator API and
returns one-dimensional real-valued predictions.

## Documentation

- [API reference](docs/API.md)
- [Algorithm](docs/ALGORITHM.md)
- [Benchmark disclosure](BENCHMARKS.md)
- [Release notes](RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## Limitations

- binary classification only;
- single-target regression only;
- no multiclass, multilabel, ranking, or multi-output interface;
- dense input only; sparse matrices are unsupported;
- mixed NumPy object arrays are unsupported; use pandas DataFrames for heterogeneous data;
- raw datetime, complex, and infinite-valued features are unsupported;
- CPU only; no GPU or online/incremental training interface;
- very high cardinality is capped by `max_categories`, with rare and unseen categories handled through dedicated buckets;
- early stopping reserves validation rows unless an external `eval_set` is provided;
- performance and memory results are hardware- and workload-specific;
- this release does not claim state-of-the-art accuracy or general superiority over gradient-boosted trees.

## License

CodAdapt is created by Luca Lullo and released under the [MIT License](LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
