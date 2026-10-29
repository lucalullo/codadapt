# Persistence, source identity and trusted artifacts

Models contain Python/numeric state, not serialized native pointers. Load only
trusted pickle, joblib and serving images. A digest checks integrity against a
trusted reference; it does not establish sender authenticity or safe unpickling.

## Pickle and joblib

Round trips and predecessor-model reads must be evaluated in the exact declared
Python/dependency profiles. Their current results are in [the gate report](../GATES_REPORT.md).
An unchanged predictive algorithm does not establish arbitrary pickle portability.
Historical newer NumPy/pandas pickles failed under older major dependency stacks;
cross-major NumPy/pandas migration is not promised. Preserve the producing
environment, or retrain from trusted data in an appropriate environment.

## Serving export and load

```python
from codadapt.serving import export_model, load_model

receipt = export_model(fitted_model, "model.codadapt")
predictor = load_model(
    "model.codadapt", trusted=True,
    expected_sha256=receipt["artifact_sha256"],
)
prediction = predictor.predict(X_new)
```

The serving predictor is fitted-only; it is not an estimator providing fit/clone.
Its loader validates framing, version/source contract, integrity and artifact
structure. Export receipt binding and post-publication mutation detection remain
part of the existing contract. Concurrent model mutation is unsupported.

## Predecessor serving images

The proposed 2.1.0 identity is regenerated from actual source bytes. Changing
`_version.py` changes both its fingerprint and the combined producer contract.
The loader remains restricted to its exact producer contract and declared
runtime profile. It does not silently accept or rewrite old contracts.

Keep G6-R1 serving images paired with the preserved G6-R1 runtime. The same rule
applies to original 2.0.0 and other source-bound images. A model's successful
pickle load, prediction equivalence or metadata-only version change does not
prove cross-contract serving compatibility. Only explicitly executed tests may
be listed as predecessor-model evidence; see the gate report for scope.

No predecessor allowlist, unchecked migration path or new artifact format is
introduced here. A future migration would require its own qualified procedure.
See [VERSIONING.md](VERSIONING.md) for the copy-only preparation algorithm.

## Actual finite2.1.0 replay

Saved G6-R1 pickle/joblib models loaded exactly under the matched310/314 profiles;
new export/load passed; old serving images were correctly rejected by source
contract.3original numeric models also replayed exactly on314. These finite
results do not widen arbitrary cross-version/cross-major guarantees. See
FINAL_QUALIFICATION.md and qualification/GATES.json.

## Definitive technical revision: unchanged 2.1.0 contract

The cache/receipt and documentation fixes modify no product-source file. The
2.1.0 source contract remains byte-identical (SHA-256
`940f9fd84198feb1f6d6fb1a515ca2028a5f7a9ca65c4f98c8713391f58f462b`).
No compatibility allowlist, format change, guard expansion or migration is added.
Saved exports from the preceding 2.1.0 candidate are checked on exact rebuilt
wheel consumers; their recorded replay is in the final report. Earlier G6-R1
serving images still require their matching old runtime. Receipt-tool identity
changes do not rewrite earlier receipts or promote old test runs to new ones.
