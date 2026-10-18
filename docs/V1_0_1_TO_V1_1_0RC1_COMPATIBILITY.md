# 1.0.1 to 1.1.0rc1 compatibility

This compares the preserved qualified 1.0.1 workspace baseline with the locally
integrated C1 release candidate. It does not assert inspection or modification of
a current remote repository. RC preparation introduces no computational change
beyond the already qualified C1 integration; only the version literal changes.

| Contract | Classification | 1.1.0rc1 behavior / migration |
|---|---|---|
| Native constructor memory default | INTENTIONAL_CHANGE | `512` becomes `"auto"` for classifier/alias/regressor, including Shared OVR. |
| Accepted memory argument | NEW | Exact lowercase `"auto"`, in addition to positive integer MiB. Validation occurs at fit; bool/float/None/other strings are invalid. |
| Explicit positive integer | UNCHANGED | Hard cap on deterministic estimated working allocation E, including external validation rows; equality admitted. Never an RSS cap. Pass `512` to preserve old admission. |
| Legacy estimate domain E <= 512 MiB | UNCHANGED | AUTO retains historical admission without OS queries or deep payload scans, including inherited conversion/memory risks. |
| Eligible larger input admission | NEW | Conservative visible-resource/payload checks can admit E > 512 MiB. Unknown information rejects extension. No OOM guarantee. |
| Memory diagnostics | NEW | AUTO retains internal diagnostic attributes. Their layout/strings are not a stable API or safety certificate. |
| Class names and alias | UNCHANGED | `CodAdapt is CodAdaptClassifier`; native classifier and single-target regressor remain available. |
| Constructor / sklearn | UNCHANGED | Keyword-only parameters, get/set_params, clone, Pipeline and CV contracts preserved apart from the documented memory default. |
| Encoder / training / interactions | UNCHANGED | Same train-only encoding, addressing, capacity, learned-value arithmetic and random-state recipe. No subsampling, silent downsizing or precision reduction. |
| Predictions and class ordering | UNCHANGED | Qualified exact comparisons preserve fitted numeric state, predictions and probabilities; no new quality claim. |
| Input compatibility | UNCHANGED | Existing array-like conversion remains in the historical domain; opaque custom conversions cannot justify extension. Their arbitrary allocations are not sandboxed. |
| Failure atomicity | UNCHANGED | Failed Python-level fit/refit leaves no usable partial fitted estimator. OS termination is outside Python rollback. |
| Explicit budget / SafeBlend recipe | UNCHANGED | Experimental SafeBlend internal Base remains pinned to 512 MiB; no new SafeBlend parameter. |
| Experimental EBM compiler | UNCHANGED | Optional teacher compilation, SAFE/REJECT criteria, cells and teacher-free inference remain unchanged. |
| ndarray inference implementation | INTENTIONAL_CHANGE | Exact conversion/address optimizations reduce overhead in qualified workloads; predictive behavior preserved. |
| Categorical artifact representation | INTENTIONAL_CHANGE | Bounded immutable-string sharing reduces qualifying artifact duplication; loading may cost more. No general size guarantee. |
| Same-version trusted persistence | UNCHANGED | Matching-environment pickle/joblib supported. Never load untrusted files. |
| Cross-version persistence | UNCHANGED | Diagnostic replay only, WORKS_NOT_GUARANTEED. Missing historical memory field restores 512, not AUTO. Preserve original environments. |
| Python / dependency scope | UNCHANGED | Python >=3.10,<3.15; declared runtime dependency ranges unchanged. Local exact RC checks are not every allowed dependency combination. |
| Deprecations in this RC | DEPRECATED | None. No new deprecation. Historical removals in earlier versions are not repeated here. |
| Removals in this RC | REMOVED | None. No parameter, class or method removed by this RC. |
| Release availability | INTENTIONAL_CHANGE | Metadata is 1.1.0rc1, a local prerelease candidate. Publishing is a separate manual action. |

## Migration examples

```python
from codadapt import CodAdaptClassifier, CodAdaptRegressor

# New constructor default; eligible extension depends on visible headroom.
model = CodAdaptClassifier(random_state=42)

# Historical deterministic estimate admission, independent of free RAM.
legacy_admission = CodAdaptRegressor(memory_budget_mb=512, random_state=42)

# A user-controlled estimate cap is never overridden by AUTO.
bounded = CodAdaptClassifier(memory_budget_mb=1024, random_state=42)
```

Do not perform integer arithmetic on the default value without checking its type.
Use sequential large fits, process/container limits and trusted persistence.
See [AUTO](AUTO_MEMORY.md), [limitations](RC1_KNOWN_LIMITATIONS.md) and
[stability](STABILITY.md). The four known sklearn scope XFAIL remain disclosed in
the compatibility contract; they are not new failures introduced by this candidate.
