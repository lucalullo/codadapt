"""Public multiclass exactness and persistence test helpers."""

import inspect
import pickle

import joblib
import numpy as np
from _binary_reference import BinaryClassifier as Binary
from sklearn.base import clone, is_classifier
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from codadapt import CodAdapt, CodAdaptClassifier


def exact(a, b):
    a, b = np.asarray(a), np.asarray(b)
    assert a.dtype == b.dtype and a.shape == b.shape
    assert np.array_equal(a, b)
    if a.dtype.kind in "fi":
        assert a.tobytes() == b.tobytes()


def compare(a, b, x, y):
    for method in ("decision_function", "predict_proba", "predict"):
        exact(getattr(a, method)(x), getattr(b, method)(x))
    exact(a.classes_, b.classes_)
    pa, pb = a.predict_proba(x), b.predict_proba(x)
    metrics_a = [log_loss(y, pa, labels=a.classes_), accuracy_score(y, a.predict(x))]
    metrics_b = [log_loss(y, pb, labels=b.classes_), accuracy_score(y, b.predict(x))]
    exact(metrics_a, metrics_b)
    return dict(
        rows=len(y),
        logit_mismatches=0,
        probability_mismatches=0,
        decision_mismatches=0,
        classes_identical=True,
        metrics_identical=True,
        logloss=metrics_a[0],
        accuracy=metrics_a[1],
    )


def shared_identity(model):
    a = model._ovr_artifact_
    assert model.encoder_ is model.shared_encoder_ is a.shared_state.encoder
    assert model.classes_ is a.shared_state.classes
    assert model.encoders_ is model.encoder_.level_views_
    assert model._heads_ is a.heads
    assert all(h.shared_state is a.shared_state for h in a.heads)
    assert not any("cache" in k.lower() for k in vars(model))
    for h in a.heads:
        for level in h.levels:
            assert all(v.dtype == np.float64 for v in level["main_tables"] + level["tables"])
    return True


def check(x, y):
    model = CodAdaptClassifier(random_state=101)
    assert inspect.signature(CodAdaptClassifier) == inspect.signature(Binary)
    assert CodAdapt is CodAdaptClassifier and is_classifier(model)
    assert model.get_params() == Binary(random_state=101).get_params()
    copied = clone(model).set_params(n_bins=8)
    assert copied.n_bins == 8 and not hasattr(copied, "classes_")
    model.fit(x, y)
    assert model.score(x, y) == accuracy_score(y, model.predict(x))
    pipeline = Pipeline([("scale", StandardScaler()), ("model", clone(model))])
    pipeline.fit(x, y)
    assert pipeline.predict_proba(x).shape == (len(y), len(np.unique(y)))
    scores = cross_val_score(clone(model), x, y, cv=3, error_score="raise", n_jobs=1)
    assert np.isfinite(scores).all()
    return dict(clone=True, pipeline=True, CV=True, accuracy_score=True, alias=True)


def dump(path, model, fmt="pickle"):
    if fmt == "pickle":
        path.write_bytes(pickle.dumps(model, protocol=5))
    else:
        joblib.dump(model, path, compress=0)


def reload(path, fmt="pickle"):
    return pickle.loads(path.read_bytes()) if fmt == "pickle" else joblib.load(path)
