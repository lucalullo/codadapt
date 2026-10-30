# Tests and actual-host qualification

The default suite is selected by pyproject.toml: native, legacy and tool tests.
Four historical expected failures remain explicit; the old path-injection
packaging test remains retained but excluded. No test was deleted to gain PASS.
Build distributions first or supply CODADAPT_TEST_DIST to artifact tests.

```text
python tools/verify_repository.py
python -m pytest
```

The original Kaggle native/pure consumers and exact hashes are recorded in
[KAGGLE_NATIVE_20261029.json](../qualification/KAGGLE_NATIVE_20261029.json).
These full-suite results are reused only for unchanged product bytes, not as
newly executed tests of refreshed metadata or another consumer. New tool tests
and delivery checks are separately recorded in the delivery report.

For a real authorized Windows/Linux/macOS host, install psutil==7.2.2 in the
launcher environment, then use a NEW output and the exact artifact/paired sdist:

```text
python -I -B tools/run_external.py --context ci --output qualification_runs/new_host --native-wheel /path/native.whl --expected-wheel-sha256 TRUSTED_SHA256 --sdist /path/paired.tar.gz --allow-public-index
```

For actual Kaggle choose --context kaggle --expected-python 3.13.15. An authorized
offline wheelhouse can replace --allow-public-index. This full runner tests the
native consumer, exact outputs, persistence, pure fallback and fixed benchmarks.
It returns logs and failure/skips as well as success. Do not execute unknown
returned code or load unknown models merely to validate a receipt.

To build and test a new target from source:

```text
python tools/qualify_platform.py --run-id new_native --backend native
python tools/qualify_platform.py --run-id new_pure --backend pure
python tools/verify_qualification_receipt.py qualification_runs/new_native
```

Follow the exact target pins. A compatibility range or CI file is not evidence.
Fresh dependency installation, native import/calls, numerical equality, API,
persistence and costs need real execution. A package-only installation without
dependencies or a smoke using existing host dependencies has a narrower scope.
Never label it a fully clean consumer. No App Control, WSL or admin restriction
may be bypassed. Prepared workflows are manual and do not publish packages.
See [CI review](CI_AND_RUNNER_REVIEW.md) and [compatibility](COMPATIBILITY.md).
