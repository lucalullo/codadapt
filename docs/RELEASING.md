# Release qualification and manual publishing

This is a procedure, not an announcement. The current candidate is **1.0.0rc1**,
not stable 1.0.0. No workflow publishes packages or creates a tag/release. The
maintainer controls publication; no remote action is implied by local preparation.

## Local candidate checks

1. Record the actual public commit from the public clone, candidate public-file
   manifest/SHA256 and dependency environment. Preserve qualified unpublished fixes.
2. In an activated development environment run:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m build
python -m twine check dist/*
python -m pytest
```

Build before the final suite so package tests cannot silently skip for missing
archives. Use a short dedicated pytest temporary path on Windows. Build wheel and
sdist from a clean copy containing only declared public inputs; record both SHA256s.
Inspect archives for private research/data/cache/environment files and secrets.

3. Create separate new environments for wheel and sdist. Install the artifact,
   `pip check`, import numerical dependencies and run Cholesky before product checks.
   Verify installed provenance, version, binary/multiclass/regression/SafeBlend,
   clone/Pipeline/CV, and trusted pickle/joblib in a fresh process. Run public examples
   and the notebook with the installed wheel. Do not supply the checkout via PYTHONPATH.
4. Run the manual release-qualification CI after manually integrating the reviewed
   files. It must pass for this exact payload on all declared Python/OS combinations.
   Keep core physically independent of external learners. Test optional EBM separately.
   A previous commit's CI does not qualify newly copied files.

## Qualifying the 1.0.0rc1 candidate

The pre-1.0 cleanup removes seven inactive controls, makes native construction
keyword-only and keeps BucketEncoder private with its import/pickle path retained.
Review the migration in [API.md](API.md) and the future stable contract in
[STABILITY.md](STABILITY.md) when integrating this candidate.
Review platform results, documentation, license/ownership, scientific limitations and
persistence policy. The RC1 source version is already prepared; qualify this exact
version/payload, integrate manually, and obtain push CI plus the manual full release
matrix before TestPyPI/index checks. Recommended sequence: **1.0.0rc1 candidate** →
qualified RC1 publication → observation → separately qualified **1.0.0**. Any later
correction needs a new unique candidate version and qualification; never overwrite
RC2 or RC1 index artifacts. The Beta classifier describes the prerelease candidate,
not a stable release or stronger benchmark result.

## Manual TestPyPI and stable release checklist

- Confirm package-name ownership and repository credentials manually, without putting
  credentials in files. Use least privilege; publishing authorization is separate.
- Manually commit the qualified payload and obtain green CI. Record the commit and
  archive hashes. Version-bump changes require a new qualified build, not relabeling.
- Rehearse metadata/build/archive checks and clean installs locally.
- Only when authorized, upload those exact new-version archives to TestPyPI. Install
  the package from TestPyPI in a fresh environment, resolving ordinary dependencies
  from the trusted production index; avoid an unreviewed mixed-index search.
- Smoke-test installed version/provenance/native APIs, optional compiler and persistence.
  Check rendered README and installation instructions. Keep a record of results.
- Review RC feedback and all known incompatibilities. Repeat failed/relevant gates
  after any fix. Before stable, bump to 1.0.0 and rerun the final qualification.
- Only the maintainer creates the final tag, GitHub Release and PyPI publication,
  using the already verified matching artifacts and release notes.
- Verify the published hashes/metadata, a fresh index install and essential examples;
  retain receipts and the qualified environment. Document rollback/yank decisions
  rather than replacing an existing file under the same version.

Local rehearsal can be ready while real TestPyPI/index ownership, CI and publication
remain **manual external gates**. No successful upload is implied by local checks.
