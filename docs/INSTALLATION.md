# Installation

When version 2.2.0 is available on PyPI:

```bash
python -m pip install codadapt==2.2.0
```

For this source revision, install locally from the repository root. Use a compatible dependency environment; the [CI dependency profile](../requirements/ci.txt) matches the tested core dependency versions. The [historical Windows lock](../requirements/verified.lock) describes the preceding build and is not a portable resolver lock.

```bash
python -m pip install -r requirements/ci.txt
python -m pip wheel --no-build-isolation --no-deps . --wheel-dir dist
python -m pip install --no-deps dist/codadapt-2.2.0-py3-none-any.whl
python -m pip check
python -m pytest -q tests
```

Alternatively use `python -m pip install --no-build-isolation --no-deps .` in an existing compatible environment. The standard-library PEP 517 backend generates metadata directly from `pyproject.toml` and `README.md` and builds a pure-Python distribution. Run `python tools/verify_repository.py` to check source integrity and deterministic archives. See [compatibility](COMPATIBILITY.md) for the precise tested profile. The MIT terms and third-party notices are described in the [license guide](../licenses/README.md).
