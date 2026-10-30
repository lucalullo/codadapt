# Persistence and serving

Models contain Python/numeric state, not serialized native pointers. Load only
trusted pickle/joblib files and trusted serving images. SHA-256 detects changes
against a trusted reference; it does not authenticate a sender or make arbitrary
unpickling safe. Keep the producer's dependency environment with saved models.

```python
import joblib
from codadapt.serving import export_model, load_model

joblib.dump(model, "model.joblib")
restored = joblib.load("model.joblib")  # only a trusted file
receipt = export_model(model, "model.codadapt")
served = load_model("model.codadapt", trusted=True,
                    expected_sha256=receipt["artifact_sha256"])
prediction = served.predict(X_new)
```

Serving exports retain the exact source-bound 2.1.0 contract:
`940f9fd84198feb1f6d6fb1a515ca2028a5f7a9ca65c4f98c8713391f58f462b`.
This update changes no protected source, format, numerical profile, producer
allowlist or loader validation. The fitted-only serving object has no fit method.
Export commit/receipt binding and integrity checks remain in effect.

Earlier source-bound images still require their matching producer runtime.
Unchanged predictions or a successful pickle load do not prove cross-contract
serving compatibility. Do not rename versions or widen hashes to force loading.
Arbitrary cross-major NumPy/pandas pickle portability is not promised. A future
migration needs explicit approval and old/new runtime replay; none is included.
The exact Kaggle wheel/profile has export/load and persistence evidence. Newly
built artifacts retain separate verification status in the delivery manifest.
