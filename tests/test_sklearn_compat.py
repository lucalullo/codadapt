"""Official checks with two exact, documented scope exceptions per estimator.

``check_dtype_object`` requires NumPy object arrays, which are intentionally
unsupported; mixed data must use pandas. ``check_sample_weight_equivalence``
requires repeated rows to reproduce weighted fitting, but weights affect the
objective while quantiles are unweighted and coordinate support counts rows.
Zero-weight exclusion is separately tested exactly in test_no_leakage.py.
Both scope checks still execute as strict expected failures. Separately, the
readonly-memmap pickle check is xfailed on scikit-learn <1.4 due to an upstream
bug. All other checks emitted from the supported scikit-learn version and
estimator tags execute normally.
"""

import numpy as np
import pytest
import sklearn
from numpy.testing import assert_allclose
from packaging.version import Version
from sklearn.base import clone, is_classifier, is_regressor
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils import estimator_checks

from codadapt import CodAdaptClassifier, CodAdaptRegressor

OFFICIAL_SCOPE_EXCEPTIONS = {
    "check_dtype_object": "NumPy object arrays are outside scope; use a pandas DataFrame for mixed data.",
    "check_sample_weight_equivalence_on_dense_data": "Unweighted quantiles and row support counts are not invariant to weighted row repetition.",
}


def official_cases():
    models = [
        CodAdaptClassifier(
            n_bins=8, n_tables=2, table_size=32, max_iter=8, early_stopping=False, random_state=0
        ),
        CodAdaptRegressor(
            n_bins=8, n_tables=2, table_size=32, max_iter=8, early_stopping=False, random_state=0
        ),
    ]
    cases = []
    for model in models:
        if hasattr(estimator_checks, "estimator_checks_generator"):
            checks = estimator_checks.estimator_checks_generator(model)
        else:
            checks = estimator_checks.check_estimator(model, generate_only=True)
        for estimator, check in checks:
            name = check.func.__name__ if hasattr(check, "func") else check.__name__
            reason = OFFICIAL_SCOPE_EXCEPTIONS.get(name)
            marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
            variants = str(getattr(check, "keywords", {}))
            cases.append(
                pytest.param(
                    estimator, check, marks=marks, id=f"{type(model).__name__}-{name}-{variants}"
                )
            )
    return cases


@pytest.mark.parametrize("estimator,check", official_cases())
def test_official_sklearn_checks(estimator, check):
    name = check.func.__name__ if hasattr(check, "func") else check.__name__
    if (
        name == "check_estimators_pickle"
        and getattr(check, "keywords", {}).get("readonly_memmap") is True
        and Version(sklearn.__version__) < Version("1.4")
    ):
        pytest.xfail("Upstream scikit-learn <1.4 readonly_memmap pickle-check bug")
    check(estimator)


@pytest.mark.parametrize("binary", [True, False])
def test_pipeline_cross_validation_scoring_and_clone(binary):
    rng = np.random.default_rng(920)
    X = rng.normal(size=(240, 3))
    y = (X[:, 0] > 0).astype(int) if binary else 3 * X[:, 0]
    estimator = CodAdaptClassifier if binary else CodAdaptRegressor
    model = estimator(n_tables=1, table_size=32, max_iter=6, early_stopping=False, random_state=42)
    assert is_classifier(model) == binary
    assert is_regressor(model) != binary
    pipeline = Pipeline([("scale", StandardScaler()), ("model", model)])
    splitter = (
        StratifiedKFold(3, shuffle=True, random_state=42)
        if binary
        else KFold(3, shuffle=True, random_state=42)
    )
    scores = cross_val_score(
        pipeline,
        X,
        y,
        cv=splitter,
        scoring="roc_auc" if binary else "neg_mean_squared_error",
        error_score="raise",
    )
    assert scores.shape == (3,) and np.isfinite(scores).all()
    if binary:
        assert scores.mean() > 0.85
    else:
        baseline = cross_val_score(
            DummyRegressor(), X, y, cv=splitter, scoring="neg_mean_squared_error"
        )
        assert scores.mean() > baseline.mean()
    first, second = pipeline.fit(X, y), clone(pipeline).fit(X, y)
    assert_allclose(first.predict(X), second.predict(X))
