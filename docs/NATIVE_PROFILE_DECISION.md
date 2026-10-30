# Explicit native inference and unchanged automatic selection

The C++17 kernel reads fitted memories in order. Python/NumPy still handles
encoding, training, orchestration and probability normalization. Installing a
native wheel does not automatically select it on Linux.

On the exact verified Kaggle profile:

```python
import numpy as np
from codadapt import CodAdaptClassifier
from codadapt._inference import inference_backend, _active_backend

model = CodAdaptClassifier(random_state=42).fit(X_train, y_train)
with inference_backend("python"):
    reference = model.predict_proba(X_new)
with inference_backend("native"):
    assert _active_backend() == "native"
    result = model.predict_proba(X_new)
np.testing.assert_array_equal(reference, result)
```

The private context is version-specific, thread/context-local and restores the
previous selector on exit. It is not a new stable public API or model parameter.
It loads and checks the extension before the run; an unavailable extension or
DLL/ABI/policy error is visible. Do not call it native if this step fails.
Do not mutate arrays/models concurrently during prediction. The current kernel
retains the GIL and borrowed-buffer owners; this is not a parallel-training API.

The unchanged automatic guard permits native only on historical Windows x64,
CPython 3.12.10 and exact NumPy 2.5.4 / pandas 3.1.0 / SciPy 1.18.1 /
scikit-learn 1.9.1, when a matching extension exists. Expected absence of that
extension falls back to Python. Other import/contract errors are not swallowed.
Normal Linux, Windows 3.10/3.14 and macOS calls choose Python automatically.

The complete original Kaggle qualification counted 200 real kernel calls and
35 exact arrays across three tasks. A new profile or rebuilt kernel must be
qualified independently. Changing dispatch in protected source would change the
serving producer identity; no such change is authorized or applied here.
