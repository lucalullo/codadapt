# CodAdapt release notes

## 0.2.0rc2 — Experimental release candidate

### NEW

This candidate adds the opt-in, regression-only `SafeBlendRegressor` under
`codadapt.experimental`. The optional `safeblend` extra supplies LightGBM for offline
fit; the deployed artifact retains no teacher and supports trusted pickle/joblib.
The frozen validation rule chooses Base-only or the compiled blend, without a final
refit. The standalone deployment artifact is non-tree/non-neural; the API recipe is
frozen experimentally. Native defaults and the existing EBM compiler are unchanged.

### VALIDATED

The frozen independent confirmation used 18 new regression dataset sources × 5 splits:
median dataset-mean RMSE gain versus CodAdapt Base +5.20%, 95% dataset-bootstrap CI
[+2.87%, +15.37%], and 17 wins / 1 tie / 0 losses. These are panel-specific results,
not a universal guarantee. The RC2 integration replay preserved all 90 frozen predictions, branch decisions and RMSE,
with zero bitwise mismatches.

The local integration measured serialized/deep memory 1.433× / 0.819× Base and latency
0.477× / 0.621× / 1.546× / 4.692× Base for batches 1 / 32 / 1k / 100k. Measurements
used Windows/Python3.12, four BLAS threads, 18 first-seed workloads and paired warm
benchmarks; see the contract for the full hardware/protocol and scope.

### LIMITATIONS

**SafeBlendRegressor remains experimental.** Offline fit is expensive (archived full
pipeline median 75.71× Base); large batches are slower than Base on the measured panel.
Validation fallback is not a test-set or future-data guarantee. This is a regression-only
convenience panel with overlapping IID splits, not independent-hardware or universal validation.
Numeric multiclass IDs are indistinguishable from valid count regression; callers must
respect the regression-only contract. Trusted pickle/joblib needs compatible dependencies.

The validation cited here is local and does not establish independent-hardware performance. See [the contract](docs/SAFE_BLEND_EXPERIMENTAL.md) for measured panel evidence, expensive fitting and large-batch limitations.

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
