# CodAdapt

Adaptive coded-memory learning for tabular binary classification, multiclass
classification and regression, with a scikit-learn-compatible Python API.

```python
from codadapt import CodAdaptClassifier, CodAdaptRegressor

model = CodAdaptClassifier(random_state=42)
model.fit(X_train, y_train)
prediction = model.predict(X_new)
probability = model.predict_proba(X_new)
```

## Features

- Compact train-only numeric/categorical encoding and residual coded memories.
- Binary and multiclass classification, regression, sample weights and missing data.
- Optional `class_weight="balanced"`, computed internally from positive TRAIN
  weight masses and combined once with `sample_weight`; the default remains None.
- Clone/Pipeline-compatible estimators and trusted pickle/joblib persistence.
- Source-bound serving export, integrity checking and fitted-only loading.
- Ordered C++17 inference with Python fallback; training and encoding use Python/NumPy.

No new predictive strategy or universal accuracy advantage is claimed. Class
balancing can improve recall while worsening logloss. See [API](docs/API.md),
[algorithm](docs/ALGORITHM.md), [limitations](docs/LIMITATIONS.md) and
[measured performance](docs/PERFORMANCE.md).

## Installation and verified scope

The supplied verified native wheel is for Kaggle Linux x86-64 / CPython 3.13.15
and the exact dependency profile in [compatibility](docs/COMPATIBILITY.md).
It is tagged `cp313-cp313-linux_x86_64`, **not manylinux**. Install a matching
prebuilt wheel with pip; no C++ compiler is needed for that wheel. A pure Python
wheel is also provided. Distribution manifests distinguish the originally tested
artifacts from refreshed documentation/metadata builds.

See [installation](docs/INSTALLATION.md) for local wheel and source commands.
Building the extension requires a C++17 compiler and SDK; Linux builds request it
by default. `CODADAPT_BUILD_NATIVE=0` requests a pure build. Compilation errors are
visible, not silently treated as native success. Metadata's Python range is not
certification of every Python/OS combination. macOS and unqualified native
Windows distributions are excluded from current native-support claims.

## Using the native reader

**Normal Linux predictions use Python.** The automatic guard is unchanged and
only opts into native inference on the historical exact Windows CPython 3.12.10
profile when the extension is present. This is not a fresh Windows qualification.
Other profiles retain Python automatically; explicit native requests fail visibly
on a missing/invalid extension. DLL/ABI/security errors are not hidden.

For the exact verified Kaggle profile, this version-specific advanced context
selects the C++ reader without changing estimator state or model files:

```python
from codadapt._inference import inference_backend

with inference_backend("native"):
    prediction = model.predict(X_new)
    probability = model.predict_proba(X_new)
```

`codadapt._inference` is a private, version-specific interface, not a new public
estimator parameter. [Native usage](docs/NATIVE_PROFILE_DECISION.md) describes
diagnostics and restrictions. No automatic-dispatch or serving-contract migration
is included in this repository update.

## Evidence and examples

The original owner-provided Kaggle receipts record **1,079 PASS, 3 SKIP, 4 XFAIL**,
zero failures/errors, **200 actual C++ calls** and **35 exact array comparisons**.
The separate pure consumer records 1,029 PASS, 53 SKIP and 4 XFAIL. These results
apply to the exact original hashes in [the evidence](qualification/KAGGLE_NATIVE_20261029.json).
They do not qualify rebuilt wheels or every Linux host. A receipt/hash is not an
independent cryptographic attestation of the remote runner.

The fixed synthetic benchmark has three tasks and three related splits per task;
native and Python predictions are identical. Multiclass batch-2048 median latency
reductions were 38.20%, 42.80% and 38.28%. Training remains Python; these are not
accuracy improvements or a universal performance ranking. See
[the benchmark](docs/KAGGLE_BENCHMARK_20261029.md) and [qualification](docs/QUALIFICATION.md).

Self-contained examples: [binary](examples/basic_classification.py),
[multiclass](examples/basic_multiclass.py), [regression](examples/basic_regression.py)
and [Pipeline/weights/save-load](examples/basic_usage.py).

## Models, tests and release review

Load only trusted artifacts. Serving images must match their producing source
contract and numerical profile. Unchanged model arithmetic does not establish
arbitrary cross-version pickle or serving compatibility. See [persistence](docs/PERSISTENCE.md).

Run `python tools/verify_repository.py` for file integrity. Actual-host build,
install, native calls, API, persistence and tests use the bounded manual runners
in [qualification](docs/QUALIFICATION.md). Workflow files are procedures, not
evidence that a platform passed. No publishing workflow is included.

Version remains **2.1.0**. This repository is prepared for owner review; copying
or publishing is the owner's decision. Multiclass research is separate and does
not gate this engineering delivery. Original implementations and previous
deliveries remain preserved. The deferred independent full backup is not replaced
by the compact release ZIP; it remains required before replacing/deleting the
original implementation. [Release procedure](docs/RELEASE_210.md).

## License

CodAdapt is created by Luca Lullo and released under the [MIT License](https://github.com/lucalullo/codadapt/blob/main/LICENSE).

## Author

Created by [Luca Lullo](https://github.com/lucalullo).
