# Experimental EBM compilation

This opt-in API exports a fitted additive Explainable Boosting Machine to standalone
NumPy lookup tables. It does not train a new learner or replace CodAdapt's default core.
It is experimental and is not enabled automatically.

```bash
python -m pip install ".[ebm]"  # from this checkout
```

```python
from interpret.glassbox import ExplainableBoostingClassifier
from codadapt.experimental import compile_ebm

# X_train and X_verify are separate DataFrames with the same named columns.
teacher = ExplainableBoostingClassifier(interactions=0, n_jobs=1)
teacher.fit(X_train, y_train)
compiled = compile_ebm(teacher, X_verify=X_verify, max_states=8192)
logits = compiled.decision_function(X_verify)
probabilities = compiled.predict_proba(X_verify)  # shape (n, 2)
labels = compiled.predict(X_verify)  # original teacher class labels
```

Use `ExplainableBoostingRegressor(interactions=0)` for scalar regression;
the returned regressor exposes `predict`, not `predict_proba`.

## Verified contract

- Only fitted, standard `interpret-core==0.7.8` EBM classifier/regressor classes.
  Differentially private variants, subclasses, other teachers, interactions and
  multiclass models are rejected. The optional extra pins this validated version.
- Ordered univariate additive terms, finite scalar intercept and finite cell values;
  continuous numeric features or nominal/ordinal string categories.
- Input is a DataFrame with unique string names. Verification columns must match
  teacher order. Prediction permits reordered columns but rejects missing/extra ones.
  Numeric columns must have real numeric dtype, including nullable numeric types;
  strings pretending to be numeric, complex/datetime values and boolean numeric columns
  are rejected. Categorical values and declared levels must be strings or missing;
  numeric, bytes and object-valued category labels are outside this initial public scope.
- Numeric missing values and string categorical missing/unseen values use the teacher's
  corresponding states. No local fitting, lossy compression or automatic tuning occurs.
- Raw binary logits and regression predictions must be bitwise equal on `X_verify`.
  Class probabilities must have absolute error at most `1e-15` (relative tolerance zero).
  **Bitwise equality of probabilities is not promised:** sigmoid implementations can
  differ in the last floating-point bit. Labels use probability argmax in `classes_` order.

## Admission and diagnostics

`compile_ebm(teacher, *, X_verify, max_states=None)` requires nonempty verification data.
Use a held-out set representative of deployment dtypes, categories and missingness;
the compiler cannot determine whether these rows were used for teacher training.

`max_states` caps exact lookup entries, including missing/unknown states. `None` allows
the audited exact capacity; it is not a process-RAM limit. Only adjacent numeric cells
with identical float64 bits can be coalesced. A too-small budget raises
`CompilationError` (`compiler_status_ == "REJECT"`); no degraded model is returned.
Schema, structure or fidelity failures also reject explicitly. Missing optional EBM
installation produces an actionable `ImportError` during compilation only.

Successful results expose `compiler_status_ == "SAFE"`, `required_capacity_`,
`compiled_state_count_`, `estimated_memory_bytes_`, `verification_error_`,
`teacher_type_`, `task_`, `n_features_in_`, `feature_names_in_` and classifier `classes_`.
Estimated memory describes lookup payload, **not** deep Python memory or peak RSS.
`SAFE` describes supported fidelity, not latency superiority or a guarantee for arbitrary
schemas, modified artifacts, numerical libraries or hardware. Verify again when migrating
the environment. Serialization is ordinary trusted Python pickle/joblib.

## Persistence without a teacher

```python
import pickle

with open("compiled.pkl", "wb") as file:
    pickle.dump(compiled, file)
del teacher

# Another process needs CodAdapt and its normal dependencies, not interpret/EBM.
with open("compiled.pkl", "rb") as file:
    restored = pickle.load(file)
restored.predict(X_verify)
```

Only model tables, schema, original class labels and compact diagnostics are retained;
no teacher, training/verification rows, callback or teacher module is stored. Never load
untrusted pickle files. Experimental serialization compatibility across future releases
is not guaranteed; retain the package version alongside the artifact.

The returned estimators support prediction and sklearn scoring/type inspection. They
are compiler products: `fit` raises `TypeError`, and sklearn `clone` returns an unfitted
shell, not a copied compiled model. Use pickle/joblib for fitted copies; do not put them
in a fitting/CV pipeline expecting retraining.

## Deployment limits

The general runtime uses ordered NumPy searchsorted/gather/addition with small-batch
blocks and compact numeric buffers. No native extension, Numba or teacher is required
for inference. Observed advantages are primarily model memory and single-row latency;
large-batch throughput and end-to-end RSS gains are not guaranteed. Benchmark the exact
artifact, input schema and batch sizes on the target host. Independent hardware validation
remains pending; this is an opt-in experimental candidate, not a final release or default.
