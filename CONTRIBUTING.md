# Contributing

Keep changes scoped and preserve third-party copyright and license notices.
Use the [source layout](docs/SOURCE_LAYOUT.md) and documented input/API contracts.

```bash
python -m pip install -r requirements/ci.txt -r requirements/packaging.txt -r requirements/test-optional.txt
python tools/verify_repository.py
python tools/check_workflows.py
python -m build
python -m pip install --no-deps --force-reinstall dist/codadapt-2.2.0-py3-none-any.whl
python -m pytest -q tests
```

Software tests include small fitting checks and are distinct from competitive
benchmarking. Preserve the original strict expected failures as documented
limitations; do not relax assertions or suppress checks to obtain a pass. After
intentional reviewed edits, refresh the explicit source inventory using
`python tools/update_manifest.py`, then repeat the relevant verification.
Never include private data, credentials, caches, generated model artifacts or
unapproved research results. Publication is not part of the validation workflows.
