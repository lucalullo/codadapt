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
