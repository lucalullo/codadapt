"""Fixed public-like contract panel; no predictive architecture selection."""

import copy
import pickle

import numpy as np
import pandas as pd
import pytest
from _binary_reference import BinaryClassifier as Binary
from _multiclass_helpers import check, compare, dump, exact, reload, shared_identity
from scipy import sparse
from sklearn.exceptions import DataConversionWarning, NotFittedError

from codadapt import CodAdapt
from codadapt import CodAdaptClassifier as Candidate
from codadapt._core import sigmoid
from codadapt._multiclass import is_multiclass, prepare
from codadapt.preprocessing import BucketEncoder


def data(k=3):
    rng = np.random.RandomState(9201)
    x = rng.normal(size=(max(180, 20 * k), 5))
    y = np.tile(np.arange(k), len(x) // k)
    return x[: len(y)], y


def without_clock(value):
    if isinstance(value, dict):
        return {k: without_clock(v) for k, v in value.items() if k != "fit_seconds"}
    if isinstance(value, list):
        return [without_clock(v) for v in value]
    return value


def reference(model, x, y, weight=None, eval_set=None):
    d = prepare(model, x, y, weight, eval_set)
    return d, [
        Binary(**model.get_params()).fit(
            d.x,
            (d.y == c).astype(int),
            sample_weight=d.weight,
            eval_set=(d.xv, (d.yv == c).astype(int)) if d.xv is not None else None,
        )
        for c in d.classes
    ]


@pytest.mark.parametrize("weighted", [False, True])
def test_binary_exact(weighted, tmp_path):
    x, y = data(2)
    w = np.linspace(0.1, 3, len(y)) if weighted else None
    a, b = Binary(random_state=99), Candidate(random_state=99)
    for m in (a, b):
        m.fit(x, y, sample_weight=w)
    compare(a, b, x, y)
    assert set(vars(a)) == set(vars(b))
    for key in vars(a):
        if key.endswith("_") and key != "timings_" and not key.endswith("seconds_"):
            # Array/object structures use their native state serialization, timing excluded.
            assert pickle.dumps(without_clock(getattr(a, key)), protocol=5) == pickle.dumps(
                without_clock(getattr(b, key)), protocol=5
            ), key
    for fmt in ("pickle", "joblib"):
        path = tmp_path / fmt
        dump(path, b, fmt)
        compare(a, reload(path, fmt), x, y)


@pytest.mark.parametrize("kind", ["None", "positive", "nonuniform", "zero"])
def test_weights_exact(kind):
    x, y = data()
    w = None if kind == "None" else np.ones(len(y)) * 2
    if kind == "nonuniform":
        w = np.linspace(0.01, 4.5, len(y))
    if kind == "zero":
        w[::7] = 0
        x[::7] = 1e20
    m = Candidate(random_state=78)
    d, heads = reference(m, x, y, w)
    m.fit(x, y, sample_weight=w)
    expected = np.column_stack([h.decision_function(x) for h in heads])
    exact(expected, m.decision_function(x))
    p = sigmoid(expected)
    exact(p / p.sum(1, keepdims=True), m.predict_proba(x))
    assert shared_identity(m)
    assert len(d.train_ids) + len(d.valid_ids) == np.count_nonzero(w) if w is not None else len(y)


@pytest.mark.parametrize("kind", ["negative", "length", "nan", "infinity", "allzero", "matrix"])
def test_invalid_weights(kind):
    x, y = data()
    w = np.ones(len(y))
    if kind == "negative":
        w[0] = -1
    if kind == "length":
        w = w[:-1]
    if kind == "nan":
        w[0] = np.nan
    if kind == "infinity":
        w[0] = np.inf
    if kind == "allzero":
        w[:] = 0
    if kind == "matrix":
        w = w[:, None]
    with pytest.raises(ValueError, match="sample_weight"):
        Candidate(random_state=78).fit(x, y, sample_weight=w)


def test_positive_weight_dispatch():
    x, y = data()
    w = (y != 2).astype(float)
    assert not is_multiclass(y, w)
    a, b = Binary(random_state=81), Candidate(random_state=81)
    a.fit(x, y, sample_weight=w)
    b.fit(x, y, sample_weight=w)
    compare(a, b, x[w > 0], y[w > 0])
    assert not hasattr(b, "_ovr_artifact_")


@pytest.mark.parametrize("labels", ["int", "str", "categorical", "noncontiguous"])
def test_labels_and_mixed(labels):
    x, y = data(5)
    if labels == "str":
        y = np.array(["e", "a", "d", "b", "c"])[y]
    if labels == "categorical":
        y = pd.Categorical(
            np.array(["e", "a", "d", "b", "c"])[y], categories=["c", "d", "e", "b", "a"]
        )
    if labels == "noncontiguous":
        y = np.array([-11, 9, 83, 7, 500])[y]
    x = pd.DataFrame(x, columns=list("abcde"))
    x["f"] = pd.Categorical(np.where(np.arange(len(x)) % 2, "yes", "no"))
    x["g"] = np.arange(len(x)) % 2 == 0
    x.loc[::8, "a"] = np.nan
    x.loc[::9, "f"] = np.nan
    m = Candidate(random_state=79).fit(x, y)
    exact(m.classes_, np.unique(y))
    exact(m.feature_names_in_, np.asarray(x.columns, dtype=object))
    assert m.n_features_in_ == 7 and m.n_classes_ == 5
    probe = x.copy()
    probe["f"] = probe["f"].astype(object)
    probe.loc[0, "f"] = "unseen"
    p = m.predict_proba(probe)
    assert p.shape == (len(y), 5) and np.isfinite(p).all() and (p >= 0).all()
    np.testing.assert_allclose(p.sum(1), 1, atol=2e-15, rtol=0)
    exact(m.predict(probe), m.classes_[p.argmax(1)])
    assert shared_identity(m)


def test_eval_encoded_once(monkeypatch):
    x, y = data()
    xv = x[:45].copy() + 100
    counts = {"fit": 0, "validation": 0}
    f, t = BucketEncoder.fit_transform_levels, BucketEncoder.transform_levels

    def ft(self, raw, levels):
        counts["fit"] += 1
        assert raw.max() < 100
        return f(self, raw, levels)

    def tv(self, raw):
        if raw is xv:
            counts["validation"] += 1
        return t(self, raw)

    monkeypatch.setattr(BucketEncoder, "fit_transform_levels", ft)
    monkeypatch.setattr(BucketEncoder, "transform_levels", tv)
    m = Candidate(random_state=83).fit(x, y, eval_set=(xv, y[:45]))
    assert counts == {"fit": 1, "validation": 1}
    assert shared_identity(m)


@pytest.mark.parametrize("mode", ["internal", "external", "allrows", "RandomState"])
def test_common_split_exact(mode):
    x, y = data()
    rng = np.random.RandomState(86) if mode == "RandomState" else 86
    m = Candidate(random_state=rng, validation_fraction=0.25, early_stopping=mode != "allrows")
    before = copy.deepcopy(rng.get_state()) if mode == "RandomState" else None
    ev = (x[:45], y[:45]) if mode == "external" else None
    d, heads = reference(m, x, y, eval_set=ev)
    m.fit(x, y, eval_set=ev)
    exact(np.column_stack([h.decision_function(x) for h in heads]), m.decision_function(x))
    if ev is None and mode != "allrows":
        assert not np.intersect1d(d.train_ids, d.valid_ids).size
        assert len(d.valid_ids) == 45
    if mode == "allrows":
        assert len(d.train_ids) == len(y) and d.valid_ids is None
    if before is not None:
        after = rng.get_state()
        assert before[0] == after[0] and before[2:] == after[2:]
        exact(before[1], after[1])


def test_rare_classes():
    x, y = data()
    y[1:] = np.tile([0, 1], (len(y) - 1) // 2 + 1)[: len(y) - 1]
    y[0] = 2
    with pytest.raises(ValueError, match="common stratified internal validation"):
        Candidate(random_state=81).fit(x, y)
    with pytest.warns(UserWarning, match="Rare class"):
        m = Candidate(random_state=81, early_stopping=False).fit(x, y)
    assert m.predict_proba(x).shape[1] == 3
    with pytest.warns(UserWarning, match="Rare class"):
        Candidate(random_state=81).fit(x, y, eval_set=(x[:10], y[:10]))


@pytest.mark.parametrize(
    "bad",
    [
        "oneclass",
        "continuous",
        "multioutput",
        "missing",
        "complex",
        "sparse",
        "unseen_eval",
        "wrong_schema",
        "empty_eval",
    ],
)
def test_errors_clear_state(bad):
    x, y = data()
    m = Candidate(random_state=85).fit(x, y)
    args = dict(X=x, y=y)
    if bad == "oneclass":
        args["y"] = np.zeros(len(y))
    if bad == "continuous":
        args["y"] = np.arange(len(y)) / 3.3
    if bad == "multioutput":
        args["y"] = np.column_stack([y, y])
    if bad == "missing":
        args["y"] = y.astype(float)
        args["y"][0] = np.nan
    if bad == "complex":
        args["y"] = y.astype(complex)
    if bad == "sparse":
        args["X"] = sparse.csr_matrix(x)
    if bad == "unseen_eval":
        args["eval_set"] = (x[:4], np.full(4, 300))
    if bad == "wrong_schema":
        args["eval_set"] = (x[:4, :-1], y[:4])
    if bad == "empty_eval":
        args["eval_set"] = (x[:0], y[:0])
    with pytest.raises((ValueError, TypeError)):
        m.fit(**args)
    with pytest.raises(NotFittedError):
        m.predict(x)


def test_refit_cleanup():
    x, y = data()
    m = CodAdapt(random_state=87)
    m.fit(pd.DataFrame(x, columns=list("abcde")), y % 2)
    m.fit(x, y)
    assert not hasattr(m, "feature_names_in_") and not hasattr(m, "intercept_")
    shared_identity(m)
    m.fit(x, y % 2)
    assert not hasattr(m, "_ovr_artifact_") and not hasattr(m, "n_classes_")
    compare(Binary(random_state=87).fit(x, y % 2), m, x, y % 2)


def test_sklearn():
    x, y = data()
    check(x, y)
    with pytest.raises(NotFittedError):
        Candidate().predict(x)


@pytest.mark.parametrize("k", [20, 40])
def test_large_K(k):
    x, y = data(k)
    m = Candidate(random_state=89, early_stopping=False).fit(x, y)
    p = m.predict_proba(x[:50])
    assert p.shape == (50, k) and np.isfinite(p).all()
    np.testing.assert_allclose(p.sum(1), 1, atol=2e-15, rtol=0)
    exact(m.classes_, np.arange(k))
    shared_identity(m)


@pytest.mark.parametrize(
    "params",
    [
        dict(n_bins=8, n_tables=0),
        dict(table_size=64, lookup_budget=8, max_categories=8, quantile_sample_size=30),
        dict(main_effects=False, l2=2, patience=2, tol=1e-4),
        dict(
            max_iter=1,
            adapt_codes=False,
            adapt_every=1,
            n_candidates=2,
            min_code_count=2,
            max_code_updates=0,
            features_per_table=2,
        ),
    ],
)
def test_all_parameters_forwarded(params):
    x, y = data()
    m = Candidate(random_state=88, **params)
    d, heads = reference(m, x, y)
    m.fit(x, y)
    exact(m.decision_function(x), np.column_stack([h.decision_function(x) for h in heads]))
    assert m.encoder_.n_bins == min(16, m.n_bins)
    assert d.estimated_bytes == m.estimated_memory_bytes_


def test_column_target_warning():
    x, y = data()
    with pytest.warns(DataConversionWarning):
        Candidate(random_state=88).fit(x, y[:, None])


def test_multiclass_persistence(tmp_path):
    x, y = data()
    m = Candidate(random_state=91).fit(x, y, sample_weight=np.linspace(0.1, 2, len(y)))
    for fmt in ("pickle", "joblib"):
        p = tmp_path / fmt
        dump(p, m, fmt)
        loaded = reload(p, fmt)
        compare(m, loaded, x, y)
        shared_identity(loaded)
        assert loaded.get_params() == m.get_params()
    wire = pickle.dumps(m, protocol=5)
    for legacy in (b"multiclass_shared_ovr.", b"shared_state", b"NativeHead", b"XCache"):
        # shared_state is a slot key, not a module path; check actual legacy paths only.
        if legacy == b"shared_state":
            continue
        assert legacy not in wire


def test_ties():
    x, y = data()
    m = Candidate(random_state=94, early_stopping=False).fit(x, y)
    for h in m._heads_:
        h.intercept, h.levels = 0.0, []
    exact(m.predict(x), np.full(len(y), m.classes_[0]))
    b = Candidate(random_state=94, early_stopping=False).fit(x, y % 2)
    b.intercept_, b.levels_ = 0.0, []
    exact(b.predict(x), np.full(len(y), b.classes_[0]))
