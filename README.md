# CodAdapt

[![PyPI version](https://img.shields.io/pypi/v/codadapt)](https://pypi.org/project/codadapt/)

**Adaptive coded-memory learning for tabular data, with a scikit-learn-compatible Python API.**

## Why CodAdapt?

CodAdapt learns residual contributions through lookup memories for binary classification, multiclass classification and single-target regression. Numerical and categorical inputs are encoded during fitting and the learned preprocessing is reused for predictions. It supports dense numerical arrays and mixed pandas DataFrames.

## Project status

CodAdapt provides combined classifier outputs, optional snapshot compression and prepared immutable inputs for repeated requests. The underlying predictive learner is unchanged. Historical competitive measurements and current technical measurements are reported separately; no new predictive superiority is claimed. See the [release notes](https://github.com/lucalullo/codadapt/blob/main/RELEASE_NOTES.md).

## Install

```bash
python -m pip install codadapt
```

The badge shows the latest published PyPI version. The command installs the latest release compatible with the active Python environment. To install the exact source checkout instead, run `python -m pip install .` from its root.

The current source requires Python 3.12 or later and builds a pure-Python wheel. The C++ inference backend is not included or built by this release. Users who require the previously supported native backend or Python 3.10/3.11 should retain a compatible 2.1.0 distribution. See the [migration notes](https://github.com/lucalullo/codadapt/blob/main/RELEASE_NOTES.md) and [installation guide](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md).

## Quick start

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from codadapt import CodAdaptClassifier

X, y = load_breast_cancer(return_X_y=True, as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
model = CodAdaptClassifier(random_state=42).fit(X_train, y_train)
print("Test accuracy:", model.score(X_test, y_test))
```

The classifier also supports multiclass targets. For regression, use `CodAdaptRegressor` with a numerical target. See [usage and examples](https://github.com/lucalullo/codadapt/blob/main/docs/USAGE.md). This example demonstrates the API, not the benchmark protocol.

## Highlights

- Binary and multiclass classification; single-target regression.
- Automatic numerical/categorical encoding and supported missing-value handling.
- scikit-learn-compatible estimators, cloning and pipelines.
- Sample weights and optional balanced class weights.
- Combined classifier scores, probabilities and labels (`predict_all`).
- Prepared immutable-input sessions (`prepare_inference`) for repeated requests.
- Optional compressed, integrity-checked snapshots and trusted model persistence; producer-bound serving utilities.

## Benchmarks

| Scope | Evidence |
|---|---|
| Competitive evidence | 2.1.0 vs six fixed baseline configurations; 14 development origins. |
| Coverage | 97 of 98 estimator/dataset jobs measured; 83 paired comparisons, one missing. |
| Technical evidence | 2.2.0 combined outputs, prepared inputs and snapshot compression; separate observations. |
| Reproducibility | Per-dataset source and evidence guides, aggregate verification and figure regeneration; a separate historical fold-replay recipe is available. |

The [benchmark overview](https://github.com/lucalullo/codadapt/blob/main/benchmarks/README.md) links predictive quality, computational costs, complete figures, methodology, failures and numerical data. The two evidence scopes must not be combined into a new ranking. See the [reproducibility matrix](https://github.com/lucalullo/codadapt/blob/main/benchmarks/REPRODUCE.md) for exact coverage and missing inputs.

## When to use it

Use it when coded-memory learning and measured quality-resource trade-offs suit the workload. The development panel includes favorable loss/cost observations on Danish occupancy, Concrete and Edge task execution times; the separate technical panel records reduced combined-output time, prepared-request time and serialized size in tested cases.

## When to consider alternatives

Consider alternatives when the primary objective is predictive quality on the evaluated multiclass workloads or when strict recall/FPR or deployment requirements are not satisfied. The six baselines often achieve better primary scores; inconclusive results are not equivalence.

## Limitations

- No universal predictive, timing or memory advantage is established.
- No Holm-confirmed primary superiority or independent Pareto certification; C60 is not qualified.
- A smaller snapshot does not imply lower loaded RAM; compression may increase loading cost.
- Prepared inputs incur setup and retained model/input memory; regression combined requests can add overhead.
- Arbitrary mixed-object NumPy arrays, broader runtime profiles and cross-version persistence are outside the verified contract.

## Documentation

- [Usage and examples](https://github.com/lucalullo/codadapt/blob/main/docs/USAGE.md)
- [API reference](https://github.com/lucalullo/codadapt/blob/main/docs/API.md)
- [Installation](https://github.com/lucalullo/codadapt/blob/main/docs/INSTALLATION.md)
- [Compatibility](https://github.com/lucalullo/codadapt/blob/main/docs/COMPATIBILITY.md)
- [Algorithm and parameters](https://github.com/lucalullo/codadapt/blob/main/docs/ALGORITHM.md)
- [Persistence and serving](https://github.com/lucalullo/codadapt/blob/main/docs/PERSISTENCE.md)
- [Benchmarks](https://github.com/lucalullo/codadapt/blob/main/benchmarks/README.md)
- [Performance](https://github.com/lucalullo/codadapt/blob/main/docs/PERFORMANCE.md)
- [Limitations](https://github.com/lucalullo/codadapt/blob/main/docs/LIMITATIONS.md)
- [Release notes](https://github.com/lucalullo/codadapt/blob/main/RELEASE_NOTES.md)
- [Changelog](https://github.com/lucalullo/codadapt/blob/main/CHANGELOG.md)
- [Reproducing benchmarks](https://github.com/lucalullo/codadapt/blob/main/benchmarks/REPRODUCE.md)
- [Citation](https://github.com/lucalullo/codadapt/blob/main/CITATION.cff)

## License

CodAdapt is created by Luca Lullo. Its original components are released under the [MIT License](https://github.com/lucalullo/codadapt/blob/main/LICENSE), Copyright (c) 2026 Luca Lullo. Third-party components retain their licenses; see the [third-party notices](https://github.com/lucalullo/codadapt/blob/main/licenses/README.md).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
