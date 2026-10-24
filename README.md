# CodAdapt 2.0.0 — Official Stable Release

> Prepared and fully qualified for official release.
> Native estimators default to `memory_budget_mb="auto"`. See
> [AUTO memory](docs/AUTO_MEMORY.md), [migration](docs/V1_0_1_TO_V2_0_COMPATIBILITY.md)
> and [known limitations](docs/RC1_KNOWN_LIMITATIONS.md).

CodAdapt is a native tabular machine-learning algorithm based on **adaptive coded memory with shared multi-resolution encoding**. Its non-tree, non-neural estimators support binary and multiclass classification and single-target regression through a scikit-learn-compatible API. It is designed for compact models, speed and simple workflows; predictive competitiveness varies across tasks.

**CodAdapt 2.0.0 retains the documented native estimator API for binary classification, Shared OVR multiclass and regression. SafeBlend and the optional EBM compiler remain experimental.** The compiler can export supported additive EBM models into compact standalone CodAdapt lookup models that no longer require the EBM teacher at inference time.

The native API stability contract covers the documented native API. It is intended for reproducible evaluation and practical tabular workflows; stability does not imply benchmark leadership. It does not claim universal superiority over established tree-based models.

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
- compact serialized models are a consistently observed strength on the frozen blind panel;
- an opt-in compact native SafeBlend regression option, with independently replicated serialized compactness and mixed predictive competitiveness;
- sample weights, explicit validation sets, deterministic random states, and best-state restoration;
- pickle/joblib persistence;
- CPU-only NumPy runtime;
- Python 3.10–3.14, with separate compatibility gates for the native core and optional extras;
- optional fully native `SafeBlendRegressor` and EBM compilation in `codadapt.experimental`.

The native CodAdapt default remains the architecture selected during the 0.1 development process. No experimental strategy flag is required. The classifier detects multiclass targets automatically without changing binary defaults.

## Installation

Use Python **3.10–3.14** in a virtual environment:

```bash
python -m venv .venv
# Activate the environment using your platform's normal command.
python -m pip install codadapt
python -c "import codadapt; print(codadapt.__version__)"
```

To install the supplied `codadapt-2.0.0-py3-none-any.whl`, use
`python -m pip install /path/to/codadapt-2.0.0-py3-none-any.whl`.
Only after a separate maintainer publication, use
`python -m pip install codadapt==2.0.0` for an exact versioned environment.
Retain artifact SHA256 and dependency versions. See the
[compatibility policy](https://github.com/lucalullo/codadapt/blob/main/docs/PYTHON_COMPATIBILITY.md)
and [release procedure](https://github.com/lucalullo/codadapt/blob/main/docs/RELEASING.md).

To compile an already fitted supported EBM teacher, install the optional dependency:

```bash
python -m pip install "interpret-core==0.7.8"
```

Native fit, validation, prediction and persistence require only CodAdapt and its
numerical dependencies. The EBM dependency is needed only for explicit compilation,
and is not retained or required by the compiled model. Native SafeBlend needs no
external learner. Kaggle/other hosted images require their own smoke test; local
Windows checks do not qualify those images.

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

Runtime requirements are NumPy 1.24+, pandas 2.0+, scikit-learn 1.4+, SciPy 1.8+, and threadpoolctl 3.1+. Native training requires no external ML model. `psutil` is an optional benchmark dependency; the `ebm` extra is only an explicit compiler/import tool.

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
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=240, n_features=6, n_informative=4, n_redundant=0, n_classes=3, random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)
model = CodAdaptClassifier(random_state=42, verbosity=0)
model.fit(X_train, y_train)

pred = model.predict(X_test)
proba = model.predict_proba(X_test)
```

Multiclass targets are detected automatically; `CodAdapt` is the same classifier
alias. For K classes, `proba` has shape `(n_samples, K)` in `classes_` order.
Native sigmoid head probabilities are normalized across classes; ties select the
first class. Encoding and validation rows are shared, while fitting remains
independent per target class. See the [multiclass contract](https://github.com/lucalullo/codadapt/blob/main/docs/API.md#multiclass-shared-ovr).

### Regression

```python
from codadapt import CodAdaptRegressor
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split

X, y = make_regression(n_samples=240, n_features=6, noise=1.0, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
model = CodAdaptRegressor(random_state=42, verbosity=0)
model.fit(X_train, y_train)

predictions = model.predict(X_test)
```

## Cross-validation

CodAdapt follows the scikit-learn estimator protocol:

```python
import numpy as np
from codadapt import CodAdaptClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import cross_val_score

X, y = make_classification(n_samples=240, n_features=6, random_state=42)
model = CodAdaptClassifier(random_state=42, verbosity=0)
scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")

print(f"Mean ROC-AUC: {np.mean(scores):.6f}")
```

## Data handling

In 2.0.0, native estimators default to `memory_budget_mb="auto"`.
AUTO preserves historical admission up to the 512 MiB estimate and can extend it
when supported input metadata and conservative visible headroom permit. Positive
integer budgets remain hard estimate caps, including external validation rows;
pass `memory_budget_mb=512` to preserve historical admission. Neither mode is a
total-RSS cap or an OOM guarantee. See [AUTO and migration](docs/AUTO_MEMORY.md)
and [large-data limits](docs/LARGE_DATASETS.md).

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
from codadapt import CodAdaptRegressor
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split

X, y = make_regression(n_samples=240, n_features=6, random_state=42)
X_train, X_valid, y_train, y_valid = train_test_split(X, y, random_state=42)
model = CodAdaptRegressor(random_state=42).fit(X_train, y_train, eval_set=(X_valid, y_valid))
```

Preprocessing is fitted only on the effective training rows. Validation data does not determine quantile thresholds or categorical vocabularies.

Per-row non-negative sample weights are supported:

```python
import numpy as np
from codadapt import CodAdaptRegressor
from sklearn.datasets import make_regression

X_train, y_train = make_regression(n_samples=240, n_features=6, random_state=42)
weights = np.linspace(0.5, 1.5, len(y_train))
model = CodAdaptRegressor(random_state=42).fit(X_train, y_train, sample_weight=weights)
```

Rows with zero effective weight are removed before preprocessing and validation splitting.

## Experimental native SafeBlend regression

`SafeBlendRegressor` is an opt-in, regression-only **native Base + Rational** diversity
blend. It uses the standard CodAdapt installation, with no external teacher or ML
model dependency. Its internal weight is frozen at 0.30; validation fallback selects
Base when the blend does not strictly improve internal validation RMSE. There is no
final refit. `CodAdaptRegressor` remains the default.

```python
from codadapt.experimental import SafeBlendRegressor
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split

X, y = make_regression(n_samples=240, n_features=6, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
model = SafeBlendRegressor(random_state=42, verbosity=0, n_jobs=4)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
print(model.branch_, model.alpha_)
```

The later [independent regression qualification](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md#independent-safeblend-regression-qualification)
supports SafeBlend as an experimental **compact regression specialist**. Across
**nine NEW_EXTERNAL datasets and 45 frozen group/time splits**, median RMSE was
**+4.62% worse** than the preregistered external leader (Base: **+4.65%**), with
dataset wins/ties/losses **2/0/7**. The worst dataset mean degradation was **+30.85%**
and the worst split **+116.29%**. Predictive quality leadership was not confirmed.

Serialized size was **0.129×** the leader; a deep-RAM advantage was **not demonstrated**.
Warm inference latency ratios for batches 1/32/1k/100k were
**0.765× / 0.765× / 0.684× / 0.807×**, while fit cost was **1.210×** the leader.
These are hardware- and protocol-specific measurements. Validation fallback reduces
risk but does not eliminate harmful admissions on unseen domains: **32 BLEND / 13
BASE** selections included **9 harmful admissions out of 32 BLEND** selections.

The earlier five-dataset blind result (**−0.67% RMSE**, **0.120× serialized size**)
remains historical evidence: its quality advantage **did not replicate** on the
larger independent panel; serialized compactness **did replicate**. The panels use
different leader rules and are not pooled.

Historical Round 78 local research-runtime medians were approximately **4.13× fit time**,
**1.09× serialized memory**, **1.08× deep memory** and **1.19–1.23× inference
latency** versus Base. Public schema validation adds overhead; results depend on
hardware and workload. See [the native SafeBlend contract](https://github.com/lucalullo/codadapt/blob/main/docs/SAFE_BLEND_EXPERIMENTAL.md)
for inputs, fitted diagnostics, persistence, costs and limitations.

## Experimental EBM compilation

CodAdapt 2.0.0 retains an **experimental, opt-in** compiler for supported additive `interpret-core==0.7.8` EBM models. Install the [optional `ebm` extra](#installation) when compiling a fitted teacher; the native CodAdapt installation remains independent of interpret.

```python
from codadapt.experimental import compile_ebm
import pandas as pd
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(n_samples=240, n_features=6, random_state=42)
X = pd.DataFrame(X, columns=[f"feature_{j}" for j in range(X.shape[1])])
X_train, X_valid, y_train, y_valid = train_test_split(X, y, stratify=y, random_state=42)
X_test = X_valid
teacher = ExplainableBoostingClassifier(
    interactions=0, outer_bags=2, max_rounds=100, n_jobs=1, random_state=42
)
teacher.fit(X_train, y_train)
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

Runtime performance is workload- and environment-dependent. **The historical single-row speed advantage did not replicate**, and a general inference-speed advantage has not been established. Independent-hardware validation remains pending. See the complete [compiler benchmark disclosure](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md#experimental-ebm-compiler--frozen-local-validation) for fidelity, memory and all measured batch sizes.

See [docs/EBM_COMPILER.md](https://github.com/lucalullo/codadapt/blob/main/docs/EBM_COMPILER.md) before deployment.

## Main parameters

The defaults are intended to be the starting point. Advanced users can control model size and training behavior explicitly:

```python
model = CodAdapt(
    n_bins=32,
    n_tables=8,
    features_per_table=3,
    table_size=256,
    lookup_budget=24,
    l2=5.0,
    early_stopping=True,
    random_state=42,
    verbosity=0,
)
```

Estimator constructor parameters are keyword-only. The pre-1.0 API cleanup removes
seven inactive legacy controls; existing configurations must drop those arguments.
`features_per_table` controls only the conservative memory estimate, not interaction
order. See the [API and migration guide](https://github.com/lucalullo/codadapt/blob/main/docs/API.md).

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

See [docs/ALGORITHM.md](https://github.com/lucalullo/codadapt/blob/main/docs/ALGORITHM.md) for the detailed formulation.

## Performance

The [independent regression qualification](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md#independent-safeblend-regression-qualification)
takes precedence for SafeBlend positioning: **nine NEW_EXTERNAL datasets, 45 frozen
splits, zero tuning and 270/270 SUCCESS jobs**. It confirms serialized compactness,
with weaker predictive quality than the external leader on median RMSE.

The earlier [Frozen Blind External Benchmark](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md#frozen-blind-external-benchmark)
remains the primary binary/multiclass evidence: **16 NEW_EXTERNAL primary
datasets, 72 conditions and 381 frozen jobs**, with **380 SUCCESS** and one
**MEMORY_GUARD_REJECT** coverage/system limitation. Dataset selection and the
protocol preceded metrics; there was zero tuning and all baseline presets were fixed.

| Earlier blind task / model | Datasets | Median primary-loss delta vs preregistered baseline leader |
| --- | ---: | ---: |
| Regression / CodAdaptRegressor Base | 5 | +2.41% RMSE |
| Regression / SafeBlendRegressor | 5 | −0.67% RMSE |
| Binary / CodAdaptClassifier | 6 | +9.36% logloss |
| Multiclass / CodAdaptClassifier | 5 | +22.03% logloss |

Positive loss deltas mean worse quality. The baseline leader is defined per source
by a preregistered rule across fixed HGB, LightGBM, CatBoost and XGBoost presets;
it is not always HGB. Paired condition deltas are aggregated within each source,
then by equal-source median. The earlier five-source SafeBlend quality advantage
did not replicate: the later independent panel measured **+4.62% RMSE** for SafeBlend
and **+4.65%** for Base. Its serialized ratio remained small (**0.120× → 0.129×**).
The independent verdict is **COMPACT_REGRESSION_SPECIALIST_CONFIRMED**, with the
quality-specialist gate unmet. The earlier blind library-wide verdict remains
**PRODUCT_POSITION_MIXED**; the two panels are not pooled.

Binary remains a known competitive weakness on the current blind panel; its
logloss gap is much less extreme than in the first small external pilot.
Shared OVR is technically validated, compact and robust as an API, but its
predictive competitiveness did not generalize uniformly to this blind panel.
These are single-host, hardware- and protocol-dependent results; performance
depends on domain. NEW_EXTERNAL is qualified against recoverable source history,
with incomplete early research catalogs. See the public
[methodology and limits](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md#blind-methodology-and-limits).

Earlier external pilots are secondary/historical evidence; development and
transfer panels are research evidence. They remain documented separately and
do not override the independent regression qualification or the blind
binary/multiclass panel for current product positioning.

The frozen 0.1 engineering comparison used 12 datasets and five shared splits per dataset against budget-matched LightGBM. CodAdapt did **not** win mean predictive quality on those datasets. It did, however, win median raw-input inference latency on 10/12 datasets and retained-model memory on 12/12.

With ratios defined as `LightGBM / CodAdapt`, the median fit-speed ratio was `0.887x`, the inference-speed ratio was `1.258x`, and the retained-model-memory ratio was `8.830x`.

These are local experimental measurements, not universal performance claims. Hardware, dataset, package versions, thread settings, split choice, and workload can change the result.

The experimental EBM compiler has a separate performance profile. It is intended primarily as a compact deployment path, not as a claim that compiled inference is faster for every batch size or workload.

The frozen native multiclass transfer panel (9 datasets × 3 splits) was exactly
equivalent to independent native OVR. Shared-OVR/independent ratios were about
0.605× fit, 0.662× serialized size, 0.232× deep memory and 0.334× batch1k latency.
These are panel-specific engineering comparisons, not superiority over boosting.

The earlier leakage-audited external pilot covered **6 real datasets, 11 evaluation
units and 36 valid fits** against fixed HGB and Dummy references. Technical checks
passed while predictive results varied by task, source and metric. Its small-panel
quality estimates are retained in the [historical external qualification disclosure](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md#external-leakage-audited-product-qualification),
separately from the stronger blind evidence above.

See [BENCHMARKS.md](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md) for the public benchmark disclosure.

A lightweight sanity benchmark can be run with:

```bash
python benchmarks/run_benchmarks.py --quick
```

## Persistence

Native CodAdapt models support pickle/joblib persistence in matching environments.
Cross-version, cross-Python and cross-dependency loading is not guaranteed. See
[the stability and persistence contract](https://github.com/lucalullo/codadapt/blob/main/docs/STABILITY.md).

```python
import pickle
import numpy as np
from codadapt import CodAdaptClassifier
from sklearn.datasets import make_classification
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(n_samples=160, n_features=4, random_state=42)
model = make_pipeline(StandardScaler(), CodAdaptClassifier(random_state=42)).fit(X, y)
restored = pickle.loads(pickle.dumps(model))  # only trusted, locally created bytes
np.testing.assert_array_equal(model.predict_proba(X), restored.predict_proba(X))
```

Compiled EBM models retain no teacher. Loading and inference without interpret were verified in the frozen local Windows environment; this is not a guarantee across every platform or future dependency version.

As with any pickle/joblib artifact, load only trusted files and prefer matching dependency versions across environments.

## Documentation

- [Stability and persistence contract](https://github.com/lucalullo/codadapt/blob/main/docs/STABILITY.md)
- [Release qualification procedure](https://github.com/lucalullo/codadapt/blob/main/docs/RELEASING.md)
- [API reference, including native multiclass Shared OVR](https://github.com/lucalullo/codadapt/blob/main/docs/API.md)
- [Algorithm](https://github.com/lucalullo/codadapt/blob/main/docs/ALGORITHM.md)
- [Python compatibility and release gate](https://github.com/lucalullo/codadapt/blob/main/docs/PYTHON_COMPATIBILITY.md)
- [Experimental native SafeBlend](https://github.com/lucalullo/codadapt/blob/main/docs/SAFE_BLEND_EXPERIMENTAL.md)
- [Experimental EBM compiler](https://github.com/lucalullo/codadapt/blob/main/docs/EBM_COMPILER.md)
- [Research master](https://github.com/lucalullo/codadapt/blob/main/docs/research/RESEARCH_MASTER.md)
- [Research state](https://github.com/lucalullo/codadapt/blob/main/docs/research/RESEARCH_STATE.json)
- [Benchmark disclosure](https://github.com/lucalullo/codadapt/blob/main/BENCHMARKS.md)
- [Release notes](https://github.com/lucalullo/codadapt/blob/main/RELEASE_NOTES.md)
- [Changelog](https://github.com/lucalullo/codadapt/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/lucalullo/codadapt/blob/main/CONTRIBUTING.md)
- [Security](https://github.com/lucalullo/codadapt/blob/main/SECURITY.md)

## Research continuity

`docs/research/RESEARCH_MASTER.md` and `docs/research/RESEARCH_STATE.json` are tracked in the repository so future development sessions can reconstruct the experimental history, rejected directions, open questions, and next research steps without requiring the private raw experiment tree.

These files are development documentation and are intentionally excluded from the Python wheel and source distribution.

## Limitations

- `features_per_table` affects only the memory estimate; numeric resolution is capped at 16 bins;
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
- binary classification has a +9.36% median blind logloss gap versus the preregistered baseline leader on six datasets;
- multiclass has a +22.03% median blind logloss gap on five datasets, despite successful technical qualification of Shared OVR;
- Base regression has a +2.41% median blind RMSE gap on five datasets;
- SafeBlend's later independent panel was weaker than external leaders: +4.62% median RMSE, 2/0/7 dataset wins/ties/losses, worst dataset mean +30.85% and worst split +116.29%; predictive quality varies by domain;
- validation fallback does not eliminate downside: 9 of 32 admitted blends harmed test RMSE relative to their internal Base;
- independently replicated serialized compactness (0.129× the leader) is stronger evidence than predictive quality leadership; no deep-RAM advantage was demonstrated;
- the earlier five-dataset −0.67% RMSE advantage did not replicate; neither repeated splits nor the separate historical panel enlarge the nine-source independent sample;
- Covtype-like large-N multiclass workloads remain excluded by the conservative safe-memory guard in the tested configuration; no actual out-of-memory event was measured;
- the blind benchmark's single MEMORY_GUARD_REJECT is a coverage/system limitation; successful predictions do not guarantee every large-batch measurement fits the budget;
- the blind benchmark covers only 16 datasets (5 regression, 6 binary, 5 multiclass); repeated conditions are not independent datasets, and performance depends on domain;
- this release does not claim state-of-the-art accuracy or general superiority over established tree-based models.

## Status

CodAdapt 2.0.0 combines resource-aware admission for eligible larger native
inputs with about 19.2% lower ndarray inference latency and 25.2% smaller
categorical pickle artifacts in the respective qualified workloads. The matched
C1 AUTO fit ratio was about 0.997x versus explicit admission; this measures low
admission overhead, not a new general training speedup. Exact qualified comparisons
preserve predictions; no predictive-quality gain or general peak-RAM reduction is
claimed. DataFrame inference can be unchanged, small artifacts can grow, and
compacted high-cardinality models can load more slowly. The 1.0.1 training-speed
patch is retained. SafeBlend and EBM compilation remain experimental.
CodAdapt 2.0.0 is prepared and fully qualified for official release. The frozen
public basis passed a dedicated native macOS gate; this is not a full OS-by-Python
matrix.

Current independent evidence supports SafeBlend as a **compact regression specialist**,
with strong serialized-size savings and faster inference on the tested hardware,
but weaker median predictive quality than the external leader. Classification
competitiveness remains mixed on the earlier blind panel.

The native API follows the contract described in
[STABILITY.md](https://github.com/lucalullo/codadapt/blob/main/docs/STABILITY.md).
Experimental and private components are excluded from the stable contract. See the [release notes](https://github.com/lucalullo/codadapt/blob/main/RELEASE_NOTES.md)
for migration, known limitations and persistence scope.

## License

CodAdapt is created by Luca Lullo and released under the [MIT License](https://github.com/lucalullo/codadapt/blob/main/LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
