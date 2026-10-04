# Release notes

## 0.2.0rc2 — current repository line

The native CodAdapt classifier/regressor, their defaults and algorithms are unchanged.
Python 3.10–3.14 is supported; core dependencies are NumPy, pandas, scikit-learn and
SciPy. No external ML model is required for native fit, validation, prediction or reload.

The experimental `SafeBlendRegressor` is fully native: unchanged Base plus a
complementary Rational estimator, frozen weight 0.30 and internal validation fallback.
It uses the normal core install with no external model dependency. Round 78 independent
confirmation found +2.061% median RMSE gain, CI [+0.403%, +4.695%], on 18 new datasets
× five splits; the worst split lost 6.157%. This is panel-specific evidence, not a
no-harm guarantee. Fit remains about 4.13× Base in the frozen research panel.
See [the native SafeBlend contract](docs/SAFE_BLEND_EXPERIMENTAL.md).

The optional `ebm` extra remains solely an explicit experimental compiler/import tool
for already fitted additive interpret-core 0.7.8 models. It is not a native trainer,
is never invoked by native estimators and is unnecessary for compiled-model inference.
Its fidelity and runtime contract remain unchanged. See [the compiler documentation](docs/EBM_COMPILER.md).

Local package validation is recorded separately from remote CI and independent-hardware
validation. No release, tag, publication or version increment is created by this cleanup.
The historical published tag is unchanged; current files and rebuilt local distributions
must be distinguished from older artifacts bearing the same version.

## 0.2.0rc1 — Experimental release candidate

This candidate adds the optional experimental additive EBM compiler documented in
[EBM_COMPILER.md](docs/EBM_COMPILER.md). The native default remains the v0.1.0 core.
Compilation requires the optional EBM extra; inference from a saved compiled model
does not. Exact raw-score verification and numerical probability tolerance are mandatory.

Subsequent frozen local validation covered 12 datasets × 3 splits (36 cases per
environment), using one thread on native Windows and WSL/Linux on the same physical
host. Supported teacher-to-compiled fidelity passed 36/36 cases in each environment;
standalone inference without interpret passed 36/36 in Windows. Median compiled/EBM
memory ratios were 0.195x deep retained memory and 0.236x serialized size.

These results support compact standalone export, not a general inference accelerator.
The historical single-row speed advantage did not replicate; runtime depends on
workload and environment. Cross-OS raw scores and classes were bitwise identical,
while probability differences reached 2.22e-16, within the frozen 1e-15 absolute
tolerance (relative tolerance zero). Strict cross-OS probability-bitwise checks did
not all pass. See [the full benchmark disclosure](BENCHMARKS.md#experimental-ebm-compiler--frozen-local-validation).

This local validation does not establish remote CI or independent-hardware performance.
The compiler remains opt-in, experimental and non-default; the native core is unchanged.

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
