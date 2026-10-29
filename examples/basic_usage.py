"""Three small end-to-end engineering examples, not predictive benchmarks."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata as md
import json
import pickle
import sys
import numpy as np
import joblib
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from codadapt import CodAdaptClassifier, CodAdaptRegressor
from codadapt._inference import _active_backend, inference_backend
from codadapt.serving import export_model, load_model

LAB = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output).resolve()
    if not out.is_relative_to(LAB / "qualification_runs"):
        raise ValueError("Example results must stay inside qualification_runs")
    out.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(42)
    X = rng.normal(size=(360, 6))
    score = X[:, 0] + .5*X[:, 1] - .3*X[:, 2]
    targets = {"binary": (score > 0).astype(int), "multiclass": np.digitize(score, [-.5, .5]),
               "regression": score + .15*np.sin(X[:, 3])}
    results = []
    for name, y in targets.items():
        estimator = CodAdaptRegressor(random_state=42) if name == "regression" else CodAdaptClassifier(random_state=42, class_weight="balanced")
        estimator = clone(estimator)
        pipeline = Pipeline([("model", estimator)])
        weights = np.linspace(.5, 1.5, 300)
        weights[:5] = 0
        pipeline.fit(X[:300], y[:300], model__sample_weight=weights)
        query = X[300:]
        prediction = pipeline.predict(query)
        model = pipeline.named_steps["model"]
        with inference_backend("python"):
            assert np.array_equal(prediction, pipeline.predict(query))
        restored = pickle.loads(pickle.dumps(pipeline, protocol=5))
        assert np.array_equal(prediction, restored.predict(query))
        joblib.dump(pipeline, out / f"{name}.joblib")
        assert np.array_equal(prediction, joblib.load(out / f"{name}.joblib").predict(query))
        receipt = export_model(model, out / f"{name}.codadapt")
        served = load_model(out / f"{name}.codadapt", trusted=True, expected_sha256=receipt["artifact_sha256"])
        assert np.array_equal(prediction, served.predict(query))
        if name != "regression":
            probabilities = pipeline.predict_proba(query)
            assert probabilities.shape == (len(query), len(model.classes_))
            np.testing.assert_allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-14)
            assert np.array_equal(probabilities, served.predict_proba(query))
        results.append(dict(task=name, backend=_active_backend(), predictions=len(prediction),
                            predictive_SHA256=hashlib.sha256(prediction.tobytes()).hexdigest(),
                            pipeline_clone_weights_pickle_joblib_serving="PASS", artifact=receipt))
    packages = {d.metadata["Name"]: d.version for d in md.distributions()}
    receipt = dict(status="PASS_LOCAL_EXAMPLES", engineering_fits=3, scientific_fits=0,
                   cases=results, python=sys.version, prefix=sys.prefix, packages=packages)
    (out / "RESULT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps({k: v for k, v in receipt.items() if k not in {"packages", "cases"}}))


if __name__ == "__main__":
    main()
