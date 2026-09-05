# CodAdapt 0.1.0 Release Notes

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
