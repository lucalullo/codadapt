# 1.1.0rc1 audited limitations

The preceding trust audit recorded three MEDIUM and three LOW rows. All six are
retained below; L2 is resolved by this release preparation rather than hidden or
counted as an unresolved defect. No CRITICAL or HIGH issue is open.

| ID | Severity | Type | Status and scope |
|---|---|---|---|
| M1 | MEDIUM | KNOWN_LIMITATION | OPEN: AUTO observes visible resources heuristically. Hidden/namespaced limits, concurrent pressure, stale observations, fragmentation and allocator behavior can cause false admissions. Conservative reserves and missing metadata can cause false rejections. No absolute OOM guarantee or universal error rate. The <=512 MiB historical domain retains its inherited risks. |
| M2 | MEDIUM | KNOWN_LIMITATION | OPEN: arbitrary custom array-like conversion can allocate before admission. The estimator cannot sandbox `__array__` or native allocators; opaque metadata conservatively prevents extension beyond the historical domain. Existing conversion compatibility remains. |
| M3 | MEDIUM | KNOWN_LIMITATION | OPEN: predictive competitiveness remains mixed, particularly classification relative to strong tree learners. This RC provides no quality gain and does not resolve the frozen blind benchmark's predictive weaknesses. |
| L1 | LOW | PERFORMANCE_TRADEOFF | OPEN: small model artifacts may grow; DataFrame inference may be unchanged; categorical string compaction can slow trusted loading (about 1.58x pickle and 1.21x joblib in the qualified high-cardinality regime). The size/speed advantages are scoped, not universal. |
| L2 | LOW | DOCUMENTATION_NOTE | RESOLVED: placeholder 1.0.1 metadata and future-release notebook/releasing instructions are replaced by exact 1.1.0rc1 local-candidate metadata and explicit manual publication steps. Historical 1.0.1 references remain historical. |
| L3 | LOW | DOCUMENTATION_NOTE | OPEN, chronology only: a frozen internal macOS scope string predates the actual macOS C1 PASS receipt. It is not an admission predicate. Public documentation describes actual source-bound evidence; the frozen computational source is unchanged. |

Explicit integer budgets cap E, not RSS. Same-version persistence requires trusted
files and matching environments; cross-version portability is not promised.
Optional compiler and SafeBlend remain experimental. Local RC installation covers
five Windows Python minors and primary-runtime sdist; scoped actual platform
receipts do not imply a fresh full RC OS-by-Python remote matrix. Release workflows
and future index smokes remain manual and unexecuted by this preparation.

[Migration](V1_0_1_TO_V1_1_0RC1_COMPATIBILITY.md) · [AUTO policy](AUTO_MEMORY.md) ·
[Python evidence boundaries](PYTHON_COMPATIBILITY.md)
