"""G6: views are transient; custom behavior and validation cannot be bypassed."""
from pathlib import Path
import os
import pickle
import numpy as np
import pandas as pd
import pytest
import codadapt.preprocessing as prep

if not hasattr(prep, "_FRAME_METHODS"):
    pytest.skip("Candidate G6-specific checks; the frozen G5 suite remains separate", allow_module_level=True)

LAB = Path(__file__).resolve().parents[2]


@pytest.fixture
def frozen(runtime_fixtures):
    folder = runtime_fixtures / "results/execution002_frame_prepare/baseline_multiclass"
    return pickle.loads((folder / "model.pickle").read_bytes()), pickle.loads(
        (folder / "query.pickle").read_bytes())


def encoder(model):
    return model.shared_encoder_


@pytest.mark.parametrize("case", ["ordinary", "reverse", "reorder", "float32", "nullable",
                                 "nan", "subclass", "readonly", "mixed"])
def test_exact_fallback_equivalence(frozen, monkeypatch, case):
    model, frame = frozen
    enc = encoder(model)
    if case == "reverse": frame = frame.iloc[::-1]
    elif case == "reorder": frame = frame[frame.columns[::-1]]
    elif case == "float32": frame = frame.astype("float32")
    elif case == "nullable": frame = frame.astype("Float64")
    elif case == "nan": frame.iloc[0, 0] = np.nan
    elif case == "subclass":
        class CustomFrame(pd.DataFrame):
            pass
        frame = CustomFrame(frame)
    elif case == "readonly": frame._mgr.blocks[0].values.flags.writeable = False
    elif case == "mixed": frame.iloc[:, 0] = frame.iloc[:, 0].astype("float32")
    before = frame.copy(deep=True)
    result = enc.transform_levels(frame)
    monkeypatch.setattr(enc, "_numeric_values", enc._numeric_values)
    expected = enc.transform_levels(frame)
    assert len(result) == len(expected)
    for actual, wanted in zip(result, expected):
        assert actual.dtype == wanted.dtype and actual.shape == wanted.shape
        assert actual.tobytes() == wanted.tobytes()
    pd.testing.assert_frame_equal(frame, before)


def test_input_view_used_but_never_retained(frozen):
    model, frame = frozen
    enc = encoder(model)
    before = pickle.dumps(model, protocol=5)
    columns = prep._ordinary_frame_columns(frame, enc)
    if columns is None:
        assert (np.__version__,pd.__version__) != ("2.5.4","3.1.0")
        result=enc.transform(frame)
        assert pickle.dumps(model,protocol=5)==before
        assert not np.shares_memory(result,frame.to_numpy())
        return
    assert np.shares_memory(columns, frame._mgr.blocks[0].values)
    result = enc.transform(frame)
    assert not np.shares_memory(result, columns)
    assert pickle.dumps(model, protocol=5) == before


def test_mutating_custom_helper_uses_independent_column(frozen, monkeypatch):
    model, frame = frozen
    enc = encoder(model)
    before = frame.copy(deep=True)
    original = enc._transform_numeric
    calls = []
    def mutate(values, schema):
        assert values.flags.writeable
        calls.append(len(values))
        values[:] = 0.0
        return original(values, schema)
    monkeypatch.setattr(enc, "_transform_numeric", mutate)
    assert prep._ordinary_frame_columns(frame, enc) is None
    enc.transform(frame)
    assert len(calls) == frame.shape[1]
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("name", list(prep._FRAME_METHODS))
def test_class_override_rejects_fastpath(frozen, monkeypatch, name):
    model, frame = frozen
    original = getattr(prep.BucketEncoder, name)
    def wrapper(*args, **kwargs):
        return original(*args, **kwargs)
    monkeypatch.setattr(prep.BucketEncoder, name, wrapper)
    assert prep._ordinary_frame_columns(frame, encoder(model)) is None


@pytest.mark.parametrize("version", ["2.2.0", "future"])
def test_unqualified_pandas_has_correct_fallback(frozen, monkeypatch, version):
    model, frame = frozen
    enc = encoder(model)
    expected = enc.transform(frame)
    monkeypatch.setattr(pd, "__version__", version)
    assert prep._ordinary_frame_columns(frame, enc) is None
    actual = enc.transform(frame)
    assert actual.tobytes() == expected.tobytes()


@pytest.mark.parametrize("case", ["infinity", "wrong_columns", "duplicate_columns", "empty"])
def test_same_error_before_any_fast_access(frozen, monkeypatch, case):
    model, frame = frozen
    enc = encoder(model)
    if case == "infinity": frame.iloc[-1, 0] = np.inf; frame.iloc[0, 1] = -np.inf
    elif case == "wrong_columns": frame = frame.iloc[:, :-1]
    elif case == "duplicate_columns": frame.columns = ["same"] * frame.shape[1]
    else: frame = frame.iloc[:0]
    errors = []
    for fallback in (False, True):
        if fallback: monkeypatch.setattr(enc, "_numeric_values", enc._numeric_values)
        with pytest.raises((ValueError, TypeError)) as error: enc.transform(frame)
        errors.append((type(error.value), str(error.value)))
    assert errors[0] == errors[1]
