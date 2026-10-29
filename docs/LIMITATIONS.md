# Known limitations

- Multiclass predictive gaps remain. No new accuracy improvement is certified.
- AUTO memory admission estimates selected working allocations, not process RSS,
  a reservation, or an OOM guarantee. Custom array conversion may allocate before
  shape inspection. Internal and explicit validation have different accounting.
- Cost improvements are finite workload measurements, not universal speedups.
- The native kernel retains the GIL; mutable input arrays must not be concurrently
  modified by callers. Private backend selectors are not stable public parameters.
- Raw pickle/joblib requires trusted input and compatible dependencies. Serving
  images are producer-contract bound; arbitrary version migration is unavailable.
- Linux/macOS and blocked Windows profiles require actual authorized execution.
  Old macOS evidence belongs to the original implementation, not this backend.
- The independent physical backup remains unverified. Release is HOLD.

See [API](API.md), [memory](AUTO_MEMORY.md), [large inputs](LARGE_DATASETS.md),
[persistence](PERSISTENCE.md), [current platform matrix](COMPATIBILITY.md).
