# CodAdapt release notes

## 0.2.0rc1 — Experimental release candidate

This candidate adds the optional experimental additive EBM compiler documented in
[EBM_COMPILER.md](docs/EBM_COMPILER.md). The native default remains the v0.1.0 core.
Compilation requires the optional EBM extra; inference from a saved compiled model
does not. Exact raw-score verification and numerical probability tolerance are mandatory.
Remote CI and independent-hardware validation are not claimed until they are run on the uploaded repository. The candidate remains experimental and does not change the native default.

## 0.1.0 — Historical release notes

CodAdapt 0.1.0 is the first experimental public release.

The default `CodAdapt` and `CodAdaptRegressor` estimators now use adaptive coded memory with a shared
multi-resolution encoder. No strategy flag is required or exposed. The promoted default is
prediction-equivalent to the previously validated candidate on the core-promotion benchmark.

The release supports dense NumPy and mixed pandas input, missing and unseen values, binary
classification, regression, sample weights, validation stopping, persistence, deterministic random
states, and scikit-learn `get_params`/`set_params` behavior.

This remains alpha software. The frozen comparison found useful inference and retained-memory
characteristics but no general predictive-quality advantage over budget-matched LightGBM. Validate
quality, latency, memory, and error handling on the intended workload.
