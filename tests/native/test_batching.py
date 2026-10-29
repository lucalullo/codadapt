"""G5 batching regression on frozen model states, without new model fits."""
from pathlib import Path
import os
import pickle
import numpy as np
import pytest
from codadapt import _batching

LAB=Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("task",["binary","multiclass","regression"])
@pytest.mark.parametrize("case",["ordinary","fortran","strided","nan","infinity","wrong_columns"])
def test_frozen_large_batched_equivalence(task,case,monkeypatch,runtime_fixtures):
    folder=runtime_fixtures/"fixtures/BASELINE"/task
    model=pickle.loads((folder/"model.pickle").read_bytes())
    before=pickle.dumps(model,protocol=5)
    with np.load(folder/"DATA.npz") as data:q=data["QUERY_X"]
    X=np.resize(q,(131073,q.shape[1]))
    if case=="fortran":X=np.asfortranarray(X)
    elif case=="strided":X=X[::-1]
    elif case=="nan":X[120000,0]=np.nan
    elif case=="infinity":X[120000,0]=np.inf;X[0,1]=-np.inf
    elif case=="wrong_columns":X=X[:,:-1]
    methods=["predict"]+(["predict_proba","decision_function"] if task!="regression" else [])
    if case in {"infinity","wrong_columns"}:methods=["predict"]
    for name in methods:
        results=[]
        for threshold in (10**12,131072):
            monkeypatch.setattr(_batching,"THRESHOLD",threshold)
            try:results.append((getattr(model,name)(X),None))
            except Exception as error:results.append((None,(type(error).__name__,str(error))))
        assert results[0][1]==results[1][1]
        if results[0][0] is not None:
            a,b=results[0][0],results[1][0]
            assert a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes()
    assert pickle.dumps(model,protocol=5)==before


def test_encoder_override_is_not_bypassed(monkeypatch,runtime_fixtures):
    folder=runtime_fixtures/"fixtures/BASELINE/binary"
    model=pickle.loads((folder/"model.pickle").read_bytes())
    calls=[]
    original=model.shared_encoder_.transform_levels
    def observed(X):
        calls.append(len(X));return original(X)
    monkeypatch.setattr(model.shared_encoder_,"transform_levels",observed)
    with np.load(folder/"DATA.npz") as data:q=data["QUERY_X"]
    model.predict(np.resize(q,(131073,q.shape[1])))
    assert calls==[131073]
