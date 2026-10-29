"""Runtime-local synthetic fixtures avoid cross-version pickle assumptions."""
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import pytest
from codadapt import CodAdaptClassifier,CodAdaptRegressor

@pytest.fixture(scope="session")
def runtime_fixtures(tmp_path_factory):
    root=tmp_path_factory.mktemp("engineering_fixtures")
    source=Path(__file__).resolve().parents[1]/"data"
    for task in ("binary","multiclass","regression"):
        target=root/"fixtures/BASELINE"/task;target.mkdir(parents=True)
        raw=(source/task/"DATA.npz").read_bytes();(target/"DATA.npz").write_bytes(raw)
        with np.load(source/task/"DATA.npz") as d:X,y,q=d["TRAIN_X"],d["TRAIN_y"],d["QUERY_X"]
        est=(CodAdaptRegressor if task=="regression" else CodAdaptClassifier)(random_state=42).fit(X,y)
        (target/"model.pickle").write_bytes(pickle.dumps(est,protocol=5))
        if task=="multiclass":
            frame=pd.DataFrame(X,columns=["c"+str(i) for i in range(X.shape[1])])
            query=pd.DataFrame(q,columns=frame.columns)
            model=CodAdaptClassifier(random_state=42).fit(frame,y)
            dest=root/"results/execution002_frame_prepare/baseline_multiclass";dest.mkdir(parents=True)
            (dest/"model.pickle").write_bytes(pickle.dumps(model,protocol=5))
            (dest/"query.pickle").write_bytes(pickle.dumps(query,protocol=5))
    return root
