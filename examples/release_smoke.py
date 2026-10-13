"""Installed-artifact contract and trusted persistence smoke, without a teacher.

Run with an installed wheel/sdist: python -I examples/release_smoke.py OUTPUT fit
then repeat with OUTPUT load in a new process. OUTPUT stores trusted local artifacts.
"""

import argparse
import importlib.metadata
import json
import pickle
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import scipy.linalg
import sklearn
from sklearn.base import clone
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor, __version__
from codadapt.experimental import SafeBlendRegressor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("phase", choices=["fit", "load"])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    assert __version__ == importlib.metadata.version("codadapt")
    assert CodAdapt is CodAdaptClassifier
    np.testing.assert_array_equal(scipy.linalg.cholesky(np.eye(3)), np.eye(3))
    rng = np.random.RandomState(82)
    x = rng.normal(size=(160, 4))
    regression = 2 * x[:, 0] + x[:, 1] ** 2 + 0.01 * rng.normal(size=len(x))
    cases = {
        "binary": (CodAdaptClassifier(random_state=82), x, np.arange(len(x)) % 2),
        "multiclass": (CodAdaptClassifier(random_state=82), x, np.arange(len(x)) % 3),
        "regression": (CodAdaptRegressor(random_state=82), x, regression),
        "safe_blend": (SafeBlendRegressor(random_state=82), x, regression),
        "safe_base": (SafeBlendRegressor(random_state=7), np.zeros((40, 2)), np.full(40, 3.5)),
    }
    for name, (model, values, target) in cases.items():
        expected_path = args.output / (name + ".npz")
        if args.phase == "fit":
            model.fit(values, target)
            if name.startswith("safe"):
                assert model.branch_ == ("BASE" if name == "safe_base" else "BLEND")
            expected = {"prediction": model.predict(values)}
            if hasattr(model, "predict_proba"):
                expected["probability"] = model.predict_proba(values)
                expected["classes"] = model.classes_
            np.savez(expected_path, **expected)
            for extension in ("pickle", "joblib"):
                path = args.output / (name + "." + extension)
                if extension == "pickle":
                    path.write_bytes(pickle.dumps(model, protocol=5))
                else:
                    joblib.dump(model, path)
            other = clone(model).fit(values, target)
            assert model.predict(values).tobytes() == other.predict(values).tobytes()
            if name not in {"safe_base", "safe_blend"}:
                pipeline = make_pipeline(StandardScaler(), clone(model))
                assert np.isfinite(
                    cross_val_score(pipeline, values, target, cv=2, n_jobs=1, error_score="raise")
                ).all()
            else:
                make_pipeline(StandardScaler(), clone(model)).fit(values, target).predict(values)
            frame = pd.DataFrame({"value": values[:, 0], "category": values[:, 1] > 0})
            frame.loc[::11, "value"] = np.nan
            mixed = clone(model).fit(frame, target)
            assert mixed.predict(frame).shape == (len(values),)
        else:
            with np.load(expected_path) as expected:
                for extension in ("pickle", "joblib"):
                    path = args.output / (name + "." + extension)
                    restored = (
                        pickle.loads(path.read_bytes())
                        if extension == "pickle"
                        else joblib.load(path)
                    )
                    assert restored.predict(values).tobytes() == expected["prediction"].tobytes()
                    if "probability" in expected:
                        assert (
                            restored.predict_proba(values).tobytes()
                            == expected["probability"].tobytes()
                        )
                        np.testing.assert_array_equal(restored.classes_, expected["classes"])
    print(
        json.dumps(
            dict(
                status="PASS",
                phase=args.phase,
                version=__version__,
                python=sys.version,
                prefix=sys.prefix,
                numpy=np.__version__,
                scipy=scipy.__version__,
                pandas=pd.__version__,
                sklearn=sklearn.__version__,
                cases=list(cases),
            )
        )
    )


if __name__ == "__main__":
    main()
