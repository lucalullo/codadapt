# Release verification

CodAdapt **2.2.0** is a technical release with an unchanged predictive learner. The earlier qualification records refer to the supplied revision. The documentation and reproduction guides change source and artifact hashes, not runtime modules. Hosted checks must be verified for the actual source revision; this document does not assert the current registry state.

## Artifacts and inventory

- `SOURCE_MANIFEST.txt` is the explicit sdist source allowlist.
- `MANIFEST.json` gives the byte count and SHA-256 of every allowlisted source
  file except the manifest and its digest. Its digest is in `SHA256SUMS.txt`.
- `SBOM.json` is the source/dependency inventory, with bundled-file hashes and
  separately identified external reference dependencies.
- Build the wheel and sdist locally using `python -m build`. The generated
  `dist/` directory is excluded from the sdist allowlist and Git tracking.
  The source-only repository archive does not contain prebuilt distributions.
- `STATUS.json` and [qualification](../qualification/README.md) distinguish local
  evidence from checks still required on hosted runners.

## Reproduce checks without publishing

```bash
python -m pip install -r requirements/ci.txt -r requirements/packaging.txt -r requirements/test-optional.txt
python tools/verify_repository.py
python tools/check_workflows.py
python -m build
python -m twine check --strict dist/codadapt-2.2.0-py3-none-any.whl dist/codadapt-2.2.0.tar.gz
python -m pip install --no-deps --force-reinstall dist/codadapt-2.2.0-py3-none-any.whl
python -m pip check
python -m pytest -q tests
```

CI installs the built wheel and tests it using the source-layout test suite.
No source-tree `PYTHONPATH` masks the installed package. Both publishing workflows
are started manually on `main`, with no additional inputs. A manual dispatch
by the repository owner authorizes that channel. OIDC permissions are confined
to the isolated publishing job. No push, tag or release event triggers publication.

## Manual publication

1. Ensure the required CI matrix passes for the final commit, and check the existing
   Trusted Publishers: `publish-testpypi.yml` / `testpypi`, and
   `publish-pypi.yml` / `pypi`. Preserve the original `pypi` environment protection:
   sole owner reviewer, no administrative bypass, owner self-review permitted.
2. Run **Publish to TestPyPI** on `main` using **Run workflow**. No tokens,
   extra inputs or confirmation phrases are required. The job builds and checks
   both distributions, runs the installed-package tests, publishes their
   authenticated bytes through OIDC, then verifies the published files.
   Inspect the rendered project page.
3. Without changing the source commit, run **Publish to PyPI** on `main` using
   **Run workflow**. The workflow automatically finds a successful matching
   TestPyPI publication, retrieves its exact verified artifact without rebuilding,
   and compares it with the downloaded TestPyPI files. The existing production
   environment's owner approval still applies. Only identical distributions
   may be promoted. The complete production release is verified afterward.
4. An existing complete byte-identical release is verified without another upload.
   An unexpected, partial, differing or yanked release is a hard stop; do not use
   skip-existing to conceal a mismatch. If a run must be retried, rerun all jobs
   so the artifacts belong to the current attempt. If the source changes, repeat
   TestPyPI qualification before production promotion.

The workflows use the existing OIDC registrations, not stored API tokens. The
static checker and manifest authenticate the reviewed source; they do not prove
hosted execution or registry acceptance.

After intentional source edits, refresh the inventory with
`python tools/update_manifest.py`. This is bookkeeping, not qualification.
Run the checks again. Do not change hashes to conceal an unreviewed change.
Keep original snapshots and environments for rollback. Do not inherit C++
binary claims or independent predictive claims from old artifacts.

[Final local checks and outstanding hosted checks](FINAL_CHECKS.json).
