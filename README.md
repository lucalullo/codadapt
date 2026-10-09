# CodAdapt

CodAdapt is an experimental machine-learning library for tabular data. Its native estimator uses **adaptive coded memory with shared multi-resolution encoding** for binary and multiclass classification and single-target regression, while preserving a scikit-learn-style API.

**CodAdapt 0.2.0rc2 keeps the native binary and regression defaults unchanged, adds automatic native single-label multiclass classification through shared OVR, and includes a fully native experimental `SafeBlendRegressor`.** SafeBlend combines the unchanged native Base regressor with a compact native Rational estimator, a frozen blend weight, and validation-based fallback. It requires no LightGBM or other external ML model. The existing experimental EBM compiler remains available as a separate optional import/compilation tool.

CodAdapt remains a pre-1.0 experimental project. It is intended for controlled experiments, reproducible evaluation, and practical tabular workflows. It does not claim universal superiority over established tree-based models.

## Highlights

- automatic native binary/multiclass detection with shared-OVR encoding and artifacts;
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
- Python 3.10–3.14, with separate compatibility gates for the native core and optional extras;
- optional fully native `SafeBlendRegressor` and EBM compilation in `codadapt.experimental`.

The native CodAdapt default remains the architecture selected during the 0.1 development process. No experimental strategy flag is required. The classifier detects multiclass targets automatically without changing binary defaults.

## Installation

### From GitHub

The maintained repository line remains **0.2.0rc2**. Install the current repository from `main`:

```bash
python -m pip install "git+https://github.com/lucalullo/codadapt.git@main"
```

`CodAdapt` and `CodAdaptClassifier` detect binary or multiclass targets automatically. `CodAdaptRegressor` remains the scalar-regression estimator.

`SafeBlendRegressor` uses the same standard installation. No LightGBM, XGBoost, CatBoost, or other external ML model is required for native fitting or prediction.

For the separate optional EBM compiler:

```bash
python -m pip install "codadapt[ebm] @ git+https://github.com/lucalullo/codadapt.git@main"
```

The `ebm` extra is required only when explicitly compiling a supported fitted EBM teacher. Native CodAdapt and native SafeBlend do not use it.

### Kaggle

Native CodAdapt and native SafeBlend:

```python
!pip install -qq --no-cache-dir git+https://github.com/lucalullo/codadapt.git@main
```

Then:

```python
from codadapt.experimental import SafeBlendRegressor

model = SafeBlendRegressor(random_state=42, verbosity=0, n_jobs=4)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

For the optional EBM compiler:

```python
!pip install -qq --no-cache-dir "codadapt[ebm] @ git+https://github.com/lucalullo/codadapt.git@main"
```

Restart the notebook kernel only if the environment changes numerical packages during installation.

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

Core runtime requirements are NumPy 1.24+, pandas 2.0+, scikit-learn 1.4+, and SciPy 1.8+. These are numerical/data dependencies, not external teacher models. `psutil` is optional for benchmarks, and `interpret-core==0.7.8` is available only through the explicit `ebm` extra.

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

### Multiclass classification

```python
from codadapt import CodAdaptClassifier

model = CodAdaptClassifier(random_state=42, verbosity=0)
model.fit(X_train, y_train)

pred = model.predict(X_test)
proba = model.predict_proba(X_test)
```

Multiclass targets are detected automatically; `CodAdapt` is the same classifier
alias. For K classes, `proba` has shape `(n_samples, K)` in `classes_` order.
Native sigmoid head probabilities are normalized across classes; ties select the
first class. Encoding and validation rows are shared, while fitting remains
independent per target class. See the [multiclass contract](docs/API.md#multiclass-shared-ovr).

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

CodAdapt 0.2.0rc2 includes an **experimental, opt-in** compiler for supported additive `interpret-core==0.7.8` EBM models. Install the [optional `ebm` extra](#installation) when compiling a fitted teacher; the native CodAdapt installation remains independent of interpret.

```python
from codadapt.experimental import compile_ebm

compiled = compile_ebm(
    teacher,
    X_verify=X_valid,
)

predictions = compiled.predict(X_test)
probabilities = compiled.predict_proba(X_test)  # binary classifiers only
```

The compiler performs preflight checks and post-compilation fidelity verification. Unsupported models, unsupported schemas, insufficient capacity, or failed verification are rejected explicitly rather than silently approximated.

For the verified contract:

- binary additive EBM classification is supported;
- scalar additive EBM regression is supported; interactions and multiclass teachers are not;
- regression predictions and binary raw scores are preserved exactly on verification data;
- classification probabilities must match within `atol=1e-15, rtol=0`, not necessarily bitwise;
- standalone loading and inference without interpret passed 36/36 cases in the frozen local Windows environment; CodAdapt and its normal runtime dependencies remain required;
- the fitted teacher is used during compilation and is not retained in the compiled model;
- the compiler is optional and does not replace the native CodAdapt estimator.

In the frozen Windows/WSL validation panel (12 datasets × 3 splits, 36 cases per environment, one thread on the same physical host), median compiled/EBM memory ratios were **0.195× deep retained memory** and **0.236× serialized size**. These are panel measurements, not universal memory bounds.

Runtime performance is workload- and environment-dependent. **The historical single-row speed advantage did not replicate**, and a general inference-speed advantage has not been established. Independent-hardware validation remains pending. See the complete [compiler benchmark disclosure](BENCHMARKS.md#experimental-ebm-compiler--frozen-local-validation) for fidelity, memory and all measured batch sizes.

See [docs/EBM_COMPILER.md](docs/EBM_COMPILER.md) before deployment.

## Experimental SafeBlendRegressor

`SafeBlendRegressor` is an opt-in, regression-only **native Base + Rational** diversity
blend. It uses the standard CodAdapt installation, with no external teacher or ML
model dependency. Its internal weight is frozen at 0.30; validation fallback selects
Base when the blend does not strictly improve internal validation RMSE. There is no
final refit. `CodAdaptRegressor` remains the default.

```python
from codadapt.experimental import SafeBlendRegressor

model = SafeBlendRegressor(random_state=42, verbosity=0, n_jobs=4)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
print(model.branch_, model.alpha_)
```

Independent confirmation on 18 new real regression datasets × 5 splits found a
median RMSE gain of **+2.061%** versus Base, 95% CI **[+0.403%, +4.695%]**, and
**17/1/0** dataset wins/ties/losses. The worst split lost **6.157%**: validation
fallback reduces observed downside but does not guarantee improvement. These are
panel-specific IID results, not a universal advantage.

Round 78's frozen research recipe was originally measured at approximately **4.13× Base fit time** before the later exact callback optimization. The current implementation removes redundant diagnostic gradient recomputation while preserving coefficients, trace, branch decisions and predictions bitwise-identically in the qualification replay. On the paired six-case engineering panel, Rational fit time fell by **43.55%** and total SafeBlend fit time by **27.27%**; serialized/deep memory and inference were effectively unchanged. These are panel-specific implementation measurements, not universal speed guarantees. See [the native SafeBlend contract](docs/SAFE_BLEND_EXPERIMENTAL.md) for inputs, fitted diagnostics, persistence, costs and limitations.

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

The 0.2.0rc2 EBM compiler has a separate performance profile. It is intended primarily as an experimental compact deployment path, not as a claim that compiled inference is faster for every batch size or workload.

The frozen native multiclass transfer panel (9 datasets × 3 splits) was exactly
equivalent to independent native OVR. Shared-OVR/independent ratios were about
0.605× fit, 0.662× serialized size, 0.232× deep memory and 0.334× batch1k latency.
These are panel-specific engineering comparisons, not superiority over boosting.

See [BENCHMARKS.md](BENCHMARKS.md) for the public benchmark disclosure.

A lightweight sanity benchmark can be run with:

```bash
python benchmarks/run_benchmarks.py --quick
```

## Persistence

Native CodAdapt models support pickle/joblib persistence.

Compiled EBM models retain no teacher. Loading and inference without interpret were verified in the frozen local Windows environment; this is not a guarantee across every platform or future dependency version.

As with any pickle/joblib artifact, load only trusted files and prefer matching dependency versions across environments.

## Documentation

- [API reference, including native multiclass Shared OVR](docs/API.md)
- [Algorithm](docs/ALGORITHM.md)
- [Python compatibility and release gate](docs/PYTHON_COMPATIBILITY.md)
- [Experimental native SafeBlend](docs/SAFE_BLEND_EXPERIMENTAL.md)
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

- single-label binary and multiclass classification;
- single-target regression only;
- no multilabel, ranking, or multi-output interface;
- dense input only; sparse matrices are unsupported;
- mixed NumPy object arrays are unsupported; use pandas DataFrames for heterogeneous data;
- raw datetime, complex, and infinite-valued features are unsupported;
- CPU only; no GPU or online/incremental training interface;
- very high categorical cardinality is capped by `max_categories`, with rare and unseen categories handled through dedicated buckets;
- early stopping reserves validation rows unless an external `eval_set` is provided;
- the EBM compiler supports only its documented additive binary/regression contract;
- compiled EBM classification probabilities are numerically equivalent within tolerance, not guaranteed bitwise-identical;
- compiled EBM runtime is workload- and environment-dependent, with no general speed advantage established or independent-hardware validation completed;
- performance and memory results are hardware- and workload-specific;
- this release does not claim state-of-the-art accuracy or general superiority over established tree-based models.

## Status

CodAdapt 0.2.0rc2 is an experimental pre-release. The binary and regression paths remain unchanged from the validated 0.1 line. Native multiclass shared OVR is included in the current repository line; SafeBlend and the EBM compiler remain opt-in and experimental. The published tag is not rewritten.

The public API, compiler contract, and defaults may evolve as broader external validation continues.

## License

CodAdapt is created by Luca Lullo and released under the [MIT License](LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
