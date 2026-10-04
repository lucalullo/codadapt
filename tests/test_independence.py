"""Native estimators must work without external model packages."""

import importlib.abc
import pickle
import sys

import numpy as np
import pandas as pd

from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor, experimental


def test_native_experimental_api_is_exposed():
    assert "SafeBlendRegressor" in experimental.__all__
    assert hasattr(experimental, "SafeBlendRegressor")


def test_native_fit_predict_reload_without_external_models():
    class NoExternalModels(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".")[0] in {"lightgbm", "xgboost", "catboost", "interpret"}:
                raise AssertionError(
                    f"Native execution attempted external model import: {fullname}"
                )

    blocker = NoExternalModels()
    rng = np.random.default_rng(472)
    value = rng.normal(size=160)
    x = pd.DataFrame({"x": value, "category": np.where(value > 0, "a", "b")})
    x.loc[::13, "x"] = np.nan
    x.loc[::17, "category"] = None
    sys.meta_path.insert(0, blocker)
    try:
        assert CodAdapt is CodAdaptClassifier
        for cls, target in [
            (CodAdaptClassifier, (value > 0).astype(int)),
            (CodAdaptRegressor, value),
            (experimental.SafeBlendRegressor, value),
        ]:
            model = cls(random_state=4, verbosity=0).fit(x, target)
            expected = model.predict(x)
            np.testing.assert_array_equal(pickle.loads(pickle.dumps(model)).predict(x), expected)
    finally:
        sys.meta_path.remove(blocker)
