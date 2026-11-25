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
No source-tree `PYTHONPATH` masks the installed package. The TestPyPI workflow defaults to verification only; a manual run on `main`
with the `publish` input enabled transfers the tested distributions to a
separate publishing job. Only that job uses `id-token: write` and the
`testpypi` environment. It authenticates the exact transferred files and
uses Trusted Publishing at the TestPyPI endpoint. The production PyPI
workflow is verification-only. No push or tag triggers publication.

After intentional source edits, refresh the inventory with
`python tools/update_manifest.py`. This is bookkeeping, not qualification.
Run the checks again. Do not change hashes to conceal an unreviewed change.
Keep original snapshots and environments for rollback. Do not inherit C++
binary claims or independent predictive claims from old artifacts.

[Final local checks and outstanding hosted checks](FINAL_CHECKS.json).
