> Historical public documentation preserved from the 2.0.0 source line.
> Technical descriptions apply where unchanged; release and platform receipts
> below describe that historical source, not qualification of the present C++
> backend. Current scope: [compatibility](COMPATIBILITY.md), [API](API.md),
> [persistence](PERSISTENCE.md). This copy remains a development review candidate.
> In historical prose, "native" names CodAdapt's own algorithm; it does not
> imply that training runs in C++.

# AUTO memory admission — 2.0.0

CodAdapt 2.0.0 — Official Stable Release integrates frozen C1. Native constructors
default to `"auto"`; 1.0.1 used the historical integer default, 512 MiB. Retain the
exact release artifact and its SHA256. Prepared and fully qualified for official
release. See the [migration contract](V1_0_1_TO_V2_0_COMPATIBILITY.md) and
[known limitations](RC1_KNOWN_LIMITATIONS.md).

## API and migration

```python
from codadapt import CodAdaptClassifier, CodAdaptRegressor

# Native 2.0.0 default, for binary, Shared OVR multiclass and regression.
model = CodAdaptClassifier(random_state=42)  # memory_budget_mb="auto"

# Preserve historical deterministic admission on any machine.
bounded = CodAdaptRegressor(memory_budget_mb=512, random_state=42)
```

`memory_budget_mb` accepts exactly the lowercase string `"auto"` or a positive
integer in **MiB (2**20 bytes)**. Booleans, floats, `None` and other strings are
invalid. Construction stores the value; validation happens at fit. Clone,
`get_params`, `set_params`, Pipeline and CV preserve it. No parameter is renamed
or removed. Code that assumes the default is an integer should pass `512`
explicitly instead of doing arithmetic on the default.

An explicit integer is always a **hard cap on the deterministic estimate E**
in [LARGE_DATASETS.md](LARGE_DATASETS.md). Equality is admitted; AUTO never raises
or overrides that cap, and explicit mode does not query available RAM. Neither
mode is a hard cap on total RSS, an allocation reservation or an OOM guarantee.

SafeBlend remains opt-in and experimental. Its internal native Base is explicitly
pinned to 512 MiB to preserve its frozen recipe; it does not gain an AUTO option.
The EBM compiler is unaffected. Trusted legacy native objects missing the parameter
retain 512 when loaded, rather than silently adopting the new constructor default.
Existing persistence guarantees remain limited to matching environments; retain
the exact artifact and dependency versions.

## Two admission paths

1. **E <= 512 MiB:** preserve the historical admission domain. No OS resource
   query or deep payload scan runs, and the extra detector modules are imported
   lazily only when required. This path preserves existing array-like conversion
   behavior and its inherited memory risks. It is not a newly certified safe fit,
   including when the machine is already under memory pressure.
2. **E > 512 MiB:** require a complete supported input profile and reliable visible
   physical/container/process and virtual-memory observations. Use the minimum
   headroom across two observations, including visible cgroup ancestors on Linux
   and the observable Windows job. A finite virtual-address limit remains finite.
   Unknown, inconsistent or unreadable metadata rejects extension beyond 512 MiB.

The extension uses the frozen conservative budget:

```text
B = max(0, min(available / 4, capacity / 4, available - 1 GiB))
Q = max(E, 2 * profiled_payload) + 256 MiB + retained_class_head_allowance
admit extension only if Q <= B
```

Integer division is used for the fractions. Available headroom already accounts
for resident data/process usage, so RSS is not subtracted twice. Profiling includes
training input, target, weights and external validation; class-head allowance
accounts for multiclass retained state. These are conservative heuristics, not a
proof of every allocator/converter's future peak. The model is never downsized,
subsampled, cast to lower precision or retried with a different recipe.

## Custom inputs, limitations and failure handling

Existing accepted array-likes remain accepted in the historical domain. Training
array-like conversion can allocate **before** admission, as before. Opaque external
validation/conversion metadata cannot justify an AUTO extension. The code avoids
invoking custom metadata hooks merely to estimate size; it does not sandbox an
arbitrary `__array__`, override or native allocator. Prefer ordinary NumPy arrays
or supported pandas frames for large fits. Too many object visits, unsupported
extension metadata or uncertain resource limits cause conservative rejection.

Observations can become stale immediately. Hidden namespace ancestors, nested
Windows constraints, simultaneous fits, fragmentation and external memory pressure
can still cause false admissions. Conservative reserves, opaque metadata and
unavailable OS information can cause false rejections. No universal false-positive
or false-negative rate has been established. Use sequential large fits and retain
OS/container limits. A Python exception during fit/refit leaves prediction
unavailable; a valid complete refit is required. OS termination cannot be rolled
back by Python.

`estimated_memory_bytes_` remains the deterministic estimate E. AUTO also retains
diagnostic attributes such as `effective_memory_budget_mb_`,
`memory_admission_status_`, `memory_admission_tier_`,
`memory_admission_available_bytes_`, `memory_admission_process_RSS_bytes_` and
`memory_admission_required_bytes_`. Unobserved values are `None`, not zero.
Diagnostic strings/layout and other underscore helpers are internal details;
`memory_admission_resource_qualified_` and
`memory_admission_safety_certificate_` do not certify freedom from OOM.

## Evidence boundary and release story

The original 699,635 x 21 satisfaction dataset completed full exact AUTO/control
fits on Windows, WSL and a real Kaggle VM. Real Docker and a real Linux VM with a
distinct finite cgroup ancestor were qualified. Frozen C1 completed the real macOS
Intel/Python 3.12 gate. Earlier hosts ran the frozen V8 extension; C1 preserves that
extension and changes its lazy routing. These are scoped platform receipts,
not a new full OS-by-Python matrix or a guarantee for every dataset of that shape.

CodAdapt 2.0.0 combines automatic admission for eligible larger inputs,
lower numeric-array prediction overhead and smaller artifacts for qualifying
categorical metadata. No predictive-quality improvement or general peak-RAM
reduction is claimed. Small models may grow slightly, DataFrame inference may be
unchanged, and categorical compaction may increase load time. The original slower
V8 result remains historical negative evidence; C1's matched temporal fit tests
addressed that bottleneck. Publication remains a separate maintainer action.
