# CodAdapt 2.0.0 — Official Stable Release

## Publication handoff

Prepared and fully qualified for official release. CodAdapt 2.0.0 derives from the
qualified public RC1 basis, with version/documentation changes only. No Next-Gen
private component is included. Publication remains a separate maintainer action.

## Required local evidence

- Exact frozen source, source/test hashes, version-only semantic comparison and
  unchanged public API, predictions, learned arithmetic and AUTO/integer semantics.
- Real final-public-basis Intel macOS15/Python3.12 receipt, kept distinct from old
  C1 AUTO acceptance and from the later2.0.0 metadata-only local artifact checks.
- Wheel/sdist metadata2.0.0, privacy/content audit, Ruff, public tests, known XFAIL,
  Twine, clean wheel installs on Windows Python3.10–3.14 and primary3.12 sdist.
- Installed-artifact release contracts, persistence, sklearn, AUTO and large-N;
  quality non-regression and scoped prior platform evidence linked by source.
- Zero CRITICAL, unresolved HIGH or test FAIL. No inferred full OS-by-minor matrix.

## Human actions after separate authorization

1. Review the exact local handoff paths/hashes. Manually copy approved public
   files only; never research_private, caches, environments or private components.
2. Manually commit/push and inspect CI on that public commit. The task-only Mac
   gate does not establish CI status for a different public commit.
3. Review publishing credentials/environments and exact built artifacts. If
   separately authorized, use TestPyPI first, checking downloaded metadata/hash
   and clean-install behavior without mixed-index dependency resolution.
4. Publication to production PyPI, tags and a GitHub Release each remain separate
   human decisions. Do not overwrite a published version or publish automatically.

For direct artifact installation, use `codadapt-2.0.0-py3-none-any.whl`.
`python -m pip install codadapt==2.0.0` is appropriate only after an approved
artifact is available on the intended index. PyPI and GitHub Release availability
is subject to maintainer publication.

## Claim lock

Retain mixed blind quality and compact-specialist SafeBlend positioning. Qualified
C1 ratios (fit about0.997x, ndarray latency0.808x, categorical pickle0.748x) are
separate workload measurements, not new2.0.0 benchmarks or universal guarantees.
AUTO is a visible-resource heuristic; integer caps constrain estimated allocation,
not RSS. No new accuracy, general RAM or Next-Gen systems benefit is claimed.
Trusted persistence requires matching versions/environments; replay across versions
is diagnostic. See [migration](V1_0_1_TO_V2_0_COMPATIBILITY.md),
[stability](STABILITY.md), [Python coverage](PYTHON_COMPATIBILITY.md),
[AUTO](AUTO_MEMORY.md) and [limitations](RC1_KNOWN_LIMITATIONS.md).
