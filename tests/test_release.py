"""Zero-fit executable release checks on three existing synthetic snapshots."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from codadapt import CodAdaptClassifier,CodAdaptRegressor,__version__
FIX=Path(__file__).resolve().parent/"fixtures"
def fixture(task):
    path=FIX/(task+".pkl")
    expected=(FIX/(task+".sha256")).read_text().strip()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
    data=json.loads((FIX/(task+".json")).read_text())
    cls=CodAdaptRegressor if task=="regression" else CodAdaptClassifier
    return cls.load(path,expected_sha256=expected),pd.DataFrame(data["rows"],columns=data["columns"])
def same(a,b):
    assert len(a)==len(b)
    for x,y in zip(a,b):
        assert x.dtype==y.dtype and x.shape==y.shape
        if x.dtype.kind=="O":assert x.tolist()==y.tolist()
        else:assert x.tobytes()==y.tobytes()
@pytest.mark.parametrize("task",["binary","multiclass","regression"])
def test_api_and_roundtrip(task,tmp_path):
    assert __version__=="2.2.0"
    m,x=fixture(task)
    combined=m.predict_all(x)
    native=(m.predict(x),) if task=="regression" else (m.decision_function(x),m.predict_proba(x),m.predict(x))
    same(combined,native)
    assert clone(m).get_params()==m.get_params()
    for compress in (False,True):
        p=tmp_path/(task+str(compress)+".cda")
        n=m.save(p,compress=compress);assert n==p.stat().st_size
        same(type(m).load(p).predict_all(x),combined)
        with pytest.raises(FileExistsError):m.save(p)
        with pytest.raises(ValueError):type(m).load(p,expected_sha256="0"*64)
@pytest.mark.parametrize("task",["binary","multiclass","regression"])
def test_snapshot_binding(task):
    m,x=fixture(task);bound=m.prepare_inference(x);ids=np.array([0,3,3,1])
    same(bound.predict_rows(ids),m.predict_all(x.iloc[ids]))
    saved=bound.predict_rows(ids)
    x.iloc[0,0]=123456.0
    same(bound.predict_rows(ids),saved)
    assert not bound._codes.flags.writeable
    with pytest.raises(ValueError):bound.predict_rows(np.array([-1]))
    with pytest.raises(ValueError):bound.predict_rows(np.array([0.5]))
@pytest.mark.parametrize("cls",[CodAdaptClassifier,CodAdaptRegressor])
def test_unfitted_and_clone(cls):
    from sklearn.exceptions import NotFittedError
    model=cls(random_state=42)
    assert clone(model).get_params()==model.get_params()
    with pytest.raises(NotFittedError):model.predict_all(np.zeros((2,3)))
    with pytest.raises(NotFittedError):model.prepare_inference(np.zeros((2,3)))


@pytest.mark.parametrize("task",["binary","multiclass","regression"])
def test_retained_serving(task,tmp_path):
    from codadapt.serving import export_model,load_model
    m,x=fixture(task);p=tmp_path/(task+".image")
    receipt=export_model(m,p)
    with pytest.raises(ValueError):load_model(p)
    served=load_model(p,trusted=True,expected_sha256=receipt["artifact_sha256"])
    native=(m.predict(x),) if task=="regression" else (m.decision_function(x),m.predict_proba(x),m.predict(x))
    got=(served.predict(x),) if task=="regression" else (served.decision_function(x),served.predict_proba(x),served.predict(x))
    same(native,got)
@pytest.mark.parametrize("kind",["BooleanKey","RandomState","RangeIndex","DatetimeIndex","MultiIndex","CategoricalIndex","TimedeltaIndex","PeriodIndex"])
def test_native_state_codecs(kind):
    import pickle
    from codadapt._serialization import restore
    from codadapt.preprocessing import _BooleanKey
    values={"BooleanKey":_BooleanKey.TRUE,"RandomState":np.random.RandomState(42),
      "RangeIndex":pd.RangeIndex(3),"DatetimeIndex":pd.date_range("2024-01-01",periods=3),
      "MultiIndex":pd.MultiIndex.from_tuples([("a",1),("b",2),("c",3)]),
      "CategoricalIndex":pd.CategoricalIndex(["a","b","c"]),
      "TimedeltaIndex":pd.timedelta_range("0 days",periods=3),
      "PeriodIndex":pd.period_range("2024-01",periods=3,freq="M")}
    obj=values[kind];new=restore(pickle.dumps(obj,protocol=5))
    if isinstance(obj,pd.Index):assert type(obj) is type(new) and obj.equals(new)
    elif isinstance(obj,np.random.RandomState):assert np.array_equal(obj.get_state()[1],new.get_state()[1])
    else:assert obj is new
