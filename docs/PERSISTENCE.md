# Persistence and serving

Use trusted models and compatible dependency versions. Keep an authenticated
digest, the original model, and its original environment for rollback.

## Native persistence

The supported native pickle/joblib path is retained. Version 2.2.0 also exposes:

```python
from codadapt import CodAdaptClassifier

model.save("model.cda", compress=True)
restored = CodAdaptClassifier.load(
    "model.cda", expected_sha256=authenticated_digest
)
```

`save` creates a new file and refuses to overwrite an existing file. `compress=True`
uses zlib level 6. Loading validates the envelope and its bounds. The bounded
envelope supports up to 32 MiB of pickle payload and 33 MiB of file data. Larger
models retain the original native persistence path and its trust requirements.
Compression changes storage and loading costs.

## Compatibility and rollback

The previous technical build verified supported 2.1.0 native snapshots. The
revised codec passes the supplied synthetic snapshot tests. On pandas 2.2.3,
archived nonmissing Python string indexes can be migrated; unsupported missing
semantics and unlisted constructors are refused. This is not a universal
cross-version guarantee. Keep the original snapshot and environment. The
[conversion tool](../tools/convert_snapshot_to_native_pickle.py) can extract a
native pickle from an authenticated envelope without executing it:

```bash
python tools/convert_snapshot_to_native_pickle.py model.cda restored.pkl --expected-sha256 AUTHENTICATED_SHA256
```

Only replace the digest placeholder with an independently authenticated value.
Existing output files are refused. Extraction preserves the trust requirements
of the resulting pickle.

## Native serving API

```python
from codadapt.serving import export_model, load_model

receipt = export_model(model, "serving.image")
served = load_model(
    "serving.image", trusted=True,
    expected_sha256=receipt["artifact_sha256"]
)
```

Serving images bind their producer version, source contract, and profile.
For migration, load a compatible native snapshot and export a new image.
Images exported before the compatibility revision have a different source
fingerprint and are not accepted automatically. Preserve the original environment when only a previous serving image is
available. Hash validation preserves integrity and does not establish trust in an
unknown pickle.

## Separate lightweight companion

A separate stdlib serving and trace companion was reported and measured on three synthetic schemas. It is not present in this source bundle and must not be described as a bundled feature. See the [technical benchmark](../benchmarks/TECHNICAL.md) for measured costs and the scope of the recorded checks.
