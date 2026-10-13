# Contributing

Contributions improving correctness, portability, tests, documentation, and reproducible
measurement are welcome.

```bash
python -m pip install -e ".[dev,benchmark]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Preserve the single public CodAdapt architecture and scikit-learn estimator contract. Add focused
tests for behavior changes. Keep preprocessing train-only, record benchmark versions/seeds/failures,
and never present one split or synthetic result as general superiority. Do not commit credentials,
private data, local environments, caches, or private research records.

Use an activated virtual environment on Python 3.10–3.14. For optional compiler
tests install `.[dev,ebm]`; native training must also pass with external learners
absent. Build distributions before the final packaging tests. See
[the release procedure](docs/RELEASING.md) for installed-package testing, the manual
OS matrix and publication gates; ordinary CI remains smaller for fast feedback.
Document current behavior rather than reactivating removed legacy parameters.

## Native API cleanup and private helpers

Native estimator constructor arguments are keyword-only. Do not add inactive
compatibility controls or use removed legacy parameters in examples or tests,
except explicit rejection/migration tests. See docs/API.md for the removal list.
`codadapt.preprocessing` is a private implementation module: its retained physical
name supports internal imports/pickle paths, not a standalone transformer product.
Internal tests can exercise it without creating a stable user-facing API promise.
