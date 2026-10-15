# Releasing CodAdapt

This is the manual procedure for CodAdapt1.0.1. Local preparation creates no
commit, tag, index upload, workflow run or GitHub Release. The1.0.1 exact training-speed patch preserves
the stable1.0 API, learned model and predictions; experimental components
remain opt-in. See [STABILITY.md](STABILITY.md) and [LARGE_DATASETS.md](LARGE_DATASETS.md).

## Local qualification

1. Identify the current public main from the authoritative read-only clone, not laboratory Git metadata.
2. Freeze the qualified exact speed patch, API/defaults and scientific claims. Release preparation changes only version/docs/metadata.
3. Set1.0.1, build wheel/sdist from a clean public-only snapshot, run Ruff/format,
   full pytest and Twine; record hashes and four disclosed scope XFAIL.
4. Install wheel and sdist in clean package environments outside the source checkout.
   Run pip check, numerical imports/Cholesky, native tasks, SafeBlend branches,
   clone/Pipeline/CV, memory_budget, fresh-process pickle/joblib and reinstall checks.
5. Qualify Python3.10–3.14 and available WSL. Record actual platform evidence,
   standalone DLL failures and any reused numerical dependencies accurately.
6. Check archive contents/license/metadata/README, teacher-free inference, API and
   trusted1.0.0 artifact replay. Preserve original environments; cross-version persistence is not guaranteed.
7. Review consolidated handoff paths/SHA256 and the exact candidate manifest.
   Research memory is intentionally tracked in the repository, excluded from wheel/sdist;
   research_private is never copied or distributed.

## Maintainer-only external gates, in order

1. Integrate the qualified changed public files manually and record the new commit.
2. Commit/push manually and obtain push CI PASS on that exact commit.
3. Run Manual release qualification (no publishing), including Windows/Linux/macOS
   and Python3.10–3.14. Confirm stable macOS separately from historical RC2 success.
4. Publish candidate1.0.1 to TestPyPI through the manual testpypi environment workflow.
5. Verify fresh external TestPyPI install, provenance/version, pip check, tasks,
   SafeBlend, memory admission, persistence and uninstall/reinstall; review README rendering.
6. Create the future v1.0.1 tag and GitHub Release only after qualification approval.
7. Publish1.0.1 to production PyPI through the manual pypi environment workflow.
8. Repeat external PyPI smoke and verify final published artifact hashes/metadata.

Both publish workflows remain workflow_dispatch only with trusted publishing;
never add passwords/tokens to source or enable automatic push publishing.
Package-name/environment ownership and publishing authorization are manual gates.
Never overwrite a published version or relabel an older archive. Resolve ordinary
dependencies from the trusted production index, then install the explicit TestPyPI
package artifact without an unreviewed mixed-index dependency search.

## Integrity and observation

Preserve PRODUCT_POSITION_MIXED blind evidence and compact-specialist SafeBlend
positioning; stable API does not imply benchmark superiority. Repeated splits are
not new sources. Large-N700k receipts are shape-equivalent synthetic engineering,
not validation of an undisclosed real dataset. Record actual RC feedback/observation
without inventing a duration. A critical/high runtime defect blocks stable; research
failure alone does not. Retain release receipts and plan rollback/yank decisions
rather than replacing published files. No automatic stable promotion is performed.
