"""Regression checks for the restricted cross-version snapshot reader."""
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from codadapt._serialization import restore


def test_unlisted_global_still_rejected():
    from pathlib import PurePosixPath
    with pytest.raises(ValueError, match="Unexpected archived model type"):
        restore(pickle.dumps(PurePosixPath("unlisted"), protocol=5))


@pytest.mark.skipif(pd.__version__ != "2.2.3", reason="Migration is specific to pandas 2.2.3")
@pytest.mark.parametrize("missing", [False, True])
def test_pandas3_string_index_migration_is_lossless_or_refused(missing):
    from pandas._libs.arrays import __pyx_unpickle_NDArrayBacked as reconstruct_array
    from pandas.core.indexes.base import _new_Index

    class ArchivedDtype:
        def __reduce__(self):
            return pd.StringDtype, ("python", float("nan"))

    class ArchivedArray:
        def __reduce__(self):
            values = np.array(["a", np.nan if missing else "b"], dtype=object)
            return (reconstruct_array, (pd.arrays.StringArray, 82904607, None), (ArchivedDtype(), values))

    class ArchivedIndex:
        def __reduce__(self):
            return _new_Index, (pd.Index, {"data": ArchivedArray(), "name": "features"})

    wire = pickle.dumps(ArchivedIndex(), protocol=5)
    if missing:
        with pytest.raises(ValueError, match="nonmissing"):
            restore(wire)
    else:
        assert restore(wire).equals(pd.Index(["a", "b"], name="features"))
        assert restore(wire).name == "features"
    with pytest.raises(ValueError):
        restore(pickle.dumps(ArchivedArray(), protocol=5))


def test_serving_source_manifest_matches_actual_code():
    import codadapt
    root = Path(codadapt.__file__).resolve().parent
    c = json.loads((root / "serving/source_contract.json").read_text())
    files = {"codadapt/" + p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*.py")}
    assert files == c["native_sources"]
    assert hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == c["native_source_sha256"]
