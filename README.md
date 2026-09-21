# CodAdapt

CodAdapt is an experimental machine-learning library for tabular data. Its native estimator uses **adaptive coded memory with shared multi-resolution encoding** for binary classification and single-target regression, while preserving a scikit-learn-style API.

**CodAdapt 0.2.0rc1 adds an optional experimental EBM compiler while keeping the native CodAdapt core and default behavior unchanged.** The compiler can export supported additive EBM models into compact standalone CodAdapt lookup models that no longer require the EBM teacher at inference time.

CodAdapt remains a pre-1.0 experimental project. It is intended for controlled experiments, reproducible evaluation, and practical tabular workflows. It does not claim universal superiority over established tree-based models.

## Highlights

- simple estimator API through `CodAdapt`, `CodAdaptClassifier`, and `CodAdaptRegressor`;
- `fit`, `predict`, `predict_proba`, `get_params`, `set_params`, cloning, pipelines, and cross-validation compatibility;
- automatic handling of numerical, string/object, categorical, boolean, nullable-boolean, and missing values in pandas DataFrames;
- dense numeric NumPy input, with optional explicit categorical column indices;
- train-only quantile buckets and categorical vocabularies;
- explicit handling of missing, rare observed, and unseen categories;
- shared finest encoding with nested coarse-to-fine integer resolutions;
- adaptive residual-memory levels with validation-based and feature-level stopping;
- compact coded interaction tables controlled by a lookup budget;
- sample weights, explicit validation sets, deterministic random states, and best-state restoration;
- pickle/joblib persistence;
- CPU-only NumPy runtime;
- Python 3.10-3.12 compatibility gates;
- optional experimental EBM compilation in `codadapt.experimental`.

The native CodAdapt default remains the architecture selected during the 0.1 development process. No experimental strategy flag is required.

## Installation

### From GitHub

Install the release candidate directly from GitHub:

```bash
python -m pip install "git+https://github.com/lucalullo/codadapt.git@v0.2.0rc1"
```

For the optional EBM compiler:

```bash
python -m pip install "codadapt[ebm] @ git+https://github.com/lucalullo/codadapt.git@v0.2.0rc1"
```

The normal CodAdapt installation does **not** require EBM. The optional dependency is needed only when compiling an EBM teacher.

### Kaggle

Native CodAdapt:

```python
!pip install -qq git+https://github.com/lucalullo/codadapt.git@v0.2.0rc1
```

With the experimental EBM compiler:

```python
!pip install -qq "codadapt[ebm] @ git+https://github.com/lucalullo/codadapt.git@v0.2.0rc1"
```

Then restart the notebook kernel only if the environment requires it.

### Local checkout

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
```

For development, tests, lint, and benchmark helpers:

```bash
python -m pip install -e ".[dev,benchmark]"
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Runtime requirements are NumPy 1.24+, pandas 2.0+, scikit-learn 1.3+, and SciPy 1.8+. LightGBM and `psutil` are optional benchmark-only dependencies.

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

`early_stopping=False` is used here only because the example is extremely small. On normal datasets the default `early_stopping=True` creates a deterministic internal validation split.

### Regression

```python
from codadapt import CodAdaptRegressor

model = CodAdaptRegressor(random_state=42, verbosity=0)
model.fit(X_train, y_train)

predictions = model.predict(X_test)
```

## Cross-validation

CodAdapt follows the scikit-learn estimator protocol:

```python
import numpy as np
from codadapt import CodAdaptClassifier
from sklearn.model_selection import cross_val_score

model = CodAdaptClassifier(random_state=42, verbosity=0)
scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")

print(f"Mean ROC-AUC: {np.mean(scores):.6f}")
```

## Data handling

With pandas DataFrames, supported numeric columns are treated as numerical features. String/object, `category`, boolean, and nullable-boolean columns are handled as categorical features. Missing values are handled natively.

Integer-coded categorical columns should be declared explicitly:

```python
model = CodAdapt(
    categorical_features=["postal_code"],
    random_state=42,
)
```

For dense NumPy arrays, input must be numeric. Integer column indices may be supplied through `categorical_features` when numeric codes should be interpreted as categories.

At prediction time, DataFrames must contain the same unique column names used during fitting. Column order may differ and is realigned automatically; missing or unexpected columns are rejected.

## Validation and sample weights

Without an explicit validation set, CodAdapt creates an internal validation split when `early_stopping=True`.

For a user-controlled holdout:

```python
model.fit(
    X_train,
    y_train,
    eval_set=(X_valid, y_valid),
)
```

Preprocessing is fitted only on the effective training rows. Validation data does not determine quantile thresholds or categorical vocabularies.

Per-row non-negative sample weights are supported:

```python
model.fit(X_train, y_train, sample_weight=weights)
```

Rows with zero effective weight are removed before preprocessing and validation splitting.

## Experimental EBM compilation

CodAdapt 0.2.0rc1 introduces an **experimental** compiler for a deliberately limited subset of additive EBM models.

```python
from codadapt.experimental import compile_ebm

compiled = compile_ebm(
    teacher,
    X_verify=X_valid,
)

predictions = compiled.predict(X_test)
probabilities = compiled.predict_proba(X_test)
```

The compiler performs preflight checks and post-compilation fidelity verification. Unsupported models, unsupported schemas, insufficient capacity, or failed verification are rejected explicitly rather than silently approximated.

For the verified contract:

- binary additive EBM classification is supported;
- single-target additive EBM regression is supported;
- regression predictions and binary raw scores are preserved exactly on verification data;
- classification probabilities are preserved within numerical tolerance, not promised bitwise-identical;
- compiled models can be saved, loaded, and used without the EBM package installed;
- the EBM teacher is required only during compilation;
- the compiler is optional and does not replace the native CodAdapt estimator.

Observed benefits are mainly compact model memory and low single-row latency. Large-batch throughput can be workload-dependent and is not guaranteed to outperform the original EBM.

See [docs/EBM_COMPILER.md](docs/EBM_COMPILER.md) before deployment.

## Main parameters

The defaults are intended to be the starting point. Advanced users can control model size and training behavior explicitly:

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

Numeric features are discretized from train-only quantiles. Categorical features use stable integer buckets. The finest representation is computed once and mapped to coarser resolutions through cached integer maps. Each accepted level adds compact main-effect and coded interaction tables; validation stopping prevents unnecessary deeper levels.

Prediction is dominated by integer addressing, table lookups, and additions rather than tree traversal or neural-network layers.

See [docs/ALGORITHM.md](docs/ALGORITHM.md) for the detailed formulation.

## Performance

The frozen 0.1 engineering comparison used 12 datasets and five shared splits per dataset against budget-matched LightGBM. CodAdapt did **not** win mean predictive quality on those datasets. It did, however, win median raw-input inference latency on 10/12 datasets and retained-model memory on 12/12.

With ratios defined as `LightGBM / CodAdapt`, the median fit-speed ratio was `0.887x`, the inference-speed ratio was `1.258x`, and the retained-model-memory ratio was `8.830x`.

These are local experimental measurements, not universal performance claims. Hardware, dataset, package versions, thread settings, split choice, and workload can change the result.

The 0.2.0rc1 EBM compiler has a separate performance profile. It is intended primarily as an experimental compact deployment path, not as a claim that compiled inference is faster for every batch size or workload.

See [BENCHMARKS.md](BENCHMARKS.md) for the public benchmark disclosure.

A lightweight sanity benchmark can be run with:

```bash
python benchmarks/run_benchmarks.py --quick
```

## Persistence

Native CodAdapt models support pickle/joblib persistence.

Compiled EBM models are also designed to be standalone after compilation: the teacher does not need to be installed when loading and using the compiled artifact.

As with any pickle/joblib artifact, load only trusted files and prefer matching dependency versions across environments.

## Documentation

- [API reference](docs/API.md)
- [Algorithm](docs/ALGORITHM.md)
- [Experimental EBM compiler](docs/EBM_COMPILER.md)
- [Research master](docs/research/RESEARCH_MASTER.md)
- [Research state](docs/research/RESEARCH_STATE.json)
- [Benchmark disclosure](BENCHMARKS.md)
- [Release notes](RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## Research continuity

`docs/research/RESEARCH_MASTER.md` and `docs/research/RESEARCH_STATE.json` are tracked in the repository so future development sessions can reconstruct the experimental history, rejected directions, open questions, and next research steps without requiring the private raw experiment tree.

These files are development documentation and are intentionally excluded from the Python wheel and source distribution.

## Limitations

- binary classification only;
- single-target regression only;
- no multiclass, multilabel, ranking, or multi-output interface;
- dense input only; sparse matrices are unsupported;
- mixed NumPy object arrays are unsupported; use pandas DataFrames for heterogeneous data;
- raw datetime, complex, and infinite-valued features are unsupported;
- CPU only; no GPU or online/incremental training interface;
- very high categorical cardinality is capped by `max_categories`, with rare and unseen categories handled through dedicated buckets;
- early stopping reserves validation rows unless an external `eval_set` is provided;
- the EBM compiler supports only its documented additive binary/regression contract;
- compiled EBM classification probabilities are numerically equivalent within tolerance, not guaranteed bitwise-identical;
- compiled EBM throughput advantages are workload- and batch-size-dependent;
- performance and memory results are hardware- and workload-specific;
- this release does not claim state-of-the-art accuracy or general superiority over established tree-based models.

## Status

CodAdapt 0.2.0rc1 is an experimental pre-release. The native core remains unchanged from the validated 0.1 line, while the EBM compiler is opt-in and experimental.

The public API, compiler contract, and defaults may evolve as broader external validation continues.

## License

CodAdapt is created by Luca Lullo and released under the [MIT License](LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
