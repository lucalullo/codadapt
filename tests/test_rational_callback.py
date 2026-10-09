"""Exact fit-local diagnostic reuse; no change to the Rational recipe."""

import pickle
from types import SimpleNamespace

import joblib
import numpy as np
import pytest

import codadapt.experimental._rational as module
from codadapt.experimental import SafeBlendRegressor
from codadapt.experimental._rational import Rational


@pytest.mark.parametrize("seed", [0, 7, 42])
def test_accepted_objective_reuse_and_legacy_trace(monkeypatch, seed):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(180, 4))
    y = x[:, 0] / (1 + x[:, 1] ** 2) + rng.normal(size=len(x)) * 0.1
    calls = []
    objective, minimize = Rational.objective, module.minimize

    def counted(*args):
        calls.append(args[0].copy())
        return objective(*args)

    monkeypatch.setattr(Rational, "objective", staticmethod(counted))
    current = Rational(seed=seed).fit(x, y)
    optimized_calls = len(calls)
    calls.clear()

    def legacy(fun, theta, **kwargs):
        callback = kwargs["callback"]
        args = kwargs["args"]
        assert kwargs["options"] == {"maxiter": 100, "ftol": 1e-9}
        assert kwargs["method"] == "L-BFGS-B" and kwargs["jac"] is True

        def recompute(v):
            # The original callback evaluated this full objective/gradient solely
            # for its scalar. Check it against the cached accepted-iterate value.
            old_loss = float(counted(v, *args)[0])
            callback(v)
            assert old_loss == reference.trace[-1]

        kwargs["callback"] = recompute
        return minimize(fun, theta, **kwargs)

    monkeypatch.setattr(module, "minimize", legacy)
    reference = Rational(seed=seed)
    reference.fit(x, y)
    assert len(calls) == optimized_calls + len(current.trace)
    assert current.maxiter == reference.maxiter == 100
    assert current.theta.tobytes() == reference.theta.tobytes()
    assert np.asarray(current.trace).tobytes() == np.asarray(reference.trace).tobytes()
    assert current.predict(x).tobytes() == reference.predict(x).tobytes()
    assert vars(current).keys() == vars(reference).keys()
    assert not any("cache" in name or "gradient" in name for name in vars(current))


def test_cache_rejects_stale_or_missing_objective(monkeypatch):
    x = np.arange(40.0).reshape(-1, 1)

    def stale(fun, theta, **kwargs):
        callback = kwargs["callback"]
        with pytest.raises(RuntimeError, match="accepted iterate"):
            callback(theta)
        fun(theta, *kwargs["args"])
        changed = theta.copy()
        changed[0] += 1
        with pytest.raises(RuntimeError, match="accepted iterate"):
            callback(changed)
        callback(theta)
        return SimpleNamespace(x=theta, success=True, message="test fixture")

    monkeypatch.setattr(module, "minimize", stale)
    # Separate closures for another instance and a later fit; no persisted cache.
    a = Rational().fit(x, np.sin(x[:, 0]))
    Rational().fit(x, np.cos(x[:, 0]))
    a.fit(x, np.sin(x[:, 0]))


def test_solver_callback_disabled_preserves_coefficients(monkeypatch):
    # There is no public diagnostics switch. Exercise the solver's callback=None
    # contract without adding one to the estimator API.
    x = np.arange(160.0).reshape(-1, 2)
    y = np.sin(x[:, 0] / 20)
    current = Rational().fit(x, y)
    minimize = module.minimize

    def no_diagnostics(*args, **kwargs):
        kwargs["callback"] = None
        return minimize(*args, **kwargs)

    monkeypatch.setattr(module, "minimize", no_diagnostics)
    silent = Rational().fit(x, y)
    assert silent.trace == []
    assert silent.theta.tobytes() == current.theta.tobytes()
    assert silent.predict(x).tobytes() == current.predict(x).tobytes()


@pytest.mark.parametrize("verbosity", [0, 1])
@pytest.mark.parametrize("branch", ["BASE", "BLEND"])
def test_safe_branch_determinism_and_persistence(tmp_path, monkeypatch, branch, verbosity):
    rng = np.random.default_rng(17)
    x = rng.normal(size=(120, 2)) if branch == "BLEND" else np.zeros((40, 2))
    y = x[:, 0] ** 2 + 0.1 * rng.normal(size=len(x)) if branch == "BLEND" else np.full(40, 3.5)
    if branch == "BLEND":
        # Controlled selection fixture only; actual both-branch fits are replayed
        # in the integration audit. Rational optimization is real and unchanged.
        import pandas as pd
        from sklearn.model_selection import train_test_split

        from codadapt import CodAdaptRegressor

        train, val = train_test_split(np.arange(len(x)), test_size=0.25, random_state=142)
        base = CodAdaptRegressor(random_state=42).fit(
            pd.DataFrame(x[train]), y[train], eval_set=(pd.DataFrame(x[val]), y[val])
        )
        b = base.predict(pd.DataFrame(x[val]))
        perfect = b + (y[val] - b) / 0.3
        predict = Rational.predict

        def probe(self, frame):
            return perfect.copy() if len(frame) == len(val) else predict(self, frame)

        monkeypatch.setattr(Rational, "predict", probe)
    a = SafeBlendRegressor(random_state=42, verbosity=verbosity).fit(x, y)
    b = SafeBlendRegressor(random_state=42, verbosity=verbosity).fit(x, y)
    assert a.branch_ == b.branch_ == branch
    assert a.predict(x).tobytes() == b.predict(x).tobytes()
    assert a.fit_diagnostics_ == b.fit_diagnostics_
    path = tmp_path / "model.joblib"
    joblib.dump(a, path)
    for restored in (pickle.loads(pickle.dumps(a)), joblib.load(path)):
        assert restored.predict(x).tobytes() == a.predict(x).tobytes()
        if restored.rational_ is not None:
            assert not any("cache" in name for name in vars(restored.rational_))
