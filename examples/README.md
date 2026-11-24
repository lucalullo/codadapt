# Examples

The four small Python examples are preserved from the previous public source tree. They are API demonstrations using synthetic data, not benchmarks or independent qualification. They are exercised with the installed wheel in the verified Windows CI dependency profile. The original notebooks are not part of this distribution.

- [Basic classification](basic_classification.py)
- [Multiclass classification](basic_multiclass.py)
- [Regression](basic_regression.py)
- [Basic usage](basic_usage.py)

From the repository root, with the wheel installed:

```bash
python examples/basic_classification.py
python examples/basic_multiclass.py
python examples/basic_regression.py
python examples/basic_usage.py --output qualification_runs/example
```

The final example creates its output directory and refuses an existing one. Its
`--output` must be inside the checkout's `qualification_runs/` directory. It
checks weights, cloning, Pipeline, pickle/joblib roundtrips and serving on three
small generated tasks. These output artifacts are not part of the distributions.

See [API reference](../docs/API.md) and [installation](../docs/INSTALLATION.md).
