"""Contract tests: absent compiled execution is SKIP, never native PASS."""
import copy
import importlib.util
from types import SimpleNamespace

import numpy as np
import pytest

from codadapt._core import addresses
from codadapt._inference import _BACKEND, inference_backend, predict_coded_memory_buckets
from codadapt._training import predict_coded_memory_buckets as reference


def fixture(seed=7, rows=32, table_size=32, strides=False, code_dtype=np.uint16):
    rng = np.random.RandomState(seed)
    levels, encoders, encoded = [], [], []
    for _ in range(2):
        z = rng.randint(0, 7, size=(rows, 4)).astype(np.uint16)
        main = rng.normal(size=(4, 7))
        support = [rng.randint(0, 2, 7).astype(bool) for _ in range(4)]
        groups = [np.array([0, 2], dtype=np.intp), np.array([1, 3], dtype=np.uint8)]
        codes = [[rng.randint(0, table_size, 7).astype(code_dtype) for _ in group] for group in groups]
        tables = [rng.normal(size=table_size) for _ in groups]
        if strides:
            z = z[::-1, ::-1]
            main = main[:, ::-1]
            support = [s[::-1] for s in support]
            codes = [[c[::-1] for c in group] for group in codes]
            tables = [v[::-1] for v in tables]
        levels.append(dict(main_features=np.arange(4), main_tables=list(main),
                           groups=groups, codes=codes, tables=tables))
        encoders.append(SimpleNamespace(support_=support))
        encoded.append(z)
    return levels, encoders, encoded, -0.125, table_size


def scalar_oracle(levels, encoders, encoded, intercept, table_size):
    result = np.full(len(encoded[0]), intercept, dtype=np.float64)
    for row in range(len(result)):
        for level, encoder, z in zip(levels, encoders, encoded):
            for feature, values in zip(level.get("main_features", range(len(level["main_tables"]))), level["main_tables"]):
                result[row] += values[z[row, feature]]
            for features, codes, values in zip(level["groups"], level["codes"], level["tables"]):
                total = sum(int(code[z[row, f]]) for f, code in zip(features, codes))
                signed = (total + 2**63) % 2**64 - 2**63
                index = signed % table_size
                supported = all(encoder.support_[f][z[row, f]] for f in features)
                result[row] += values[index] if supported else 0.0
    return result


@pytest.mark.parametrize("rows", [0, 1, 32, 2048])
@pytest.mark.parametrize("table_size", [1, 31, 32, 65536])
@pytest.mark.parametrize("strides", [False, True])
def test_python_dispatch_and_scalar_oracle(rows, table_size, strides):
    args = fixture(rows=rows, table_size=table_size, strides=strides)
    expected = reference(*args)
    before = copy.deepcopy(args)
    actual = predict_coded_memory_buckets(*args)
    assert actual.tobytes() == expected.tobytes() == scalar_oracle(*args).tobytes()
    for a, b in zip(args[2], before[2]):
        np.testing.assert_array_equal(a, b)


def test_backend_context_is_restored_after_failure():
    with pytest.raises(ValueError):
        with inference_backend("invalid"):
            pass
    assert _BACKEND.get() == "auto"
    with pytest.raises(RuntimeError, match="intentional"):
        with inference_backend("python"):
            raise RuntimeError("intentional")
    assert _BACKEND.get() == "auto"


def test_missing_native_never_silently_falls_back():
    if importlib.util.find_spec("codadapt._native_kernel") is not None:
        pytest.skip("Missing-module test only when module is absent")
    with pytest.raises(RuntimeError, match="not built"):
        with inference_backend("native"):
            pytest.fail("Unavailable backend accepted")
    assert _BACKEND.get() == "auto"


@pytest.fixture
def native():
    if importlib.util.find_spec("codadapt._native_kernel") is None:
        pytest.skip("Native extension not built: compiler required; G3 remains HOLD")
    from codadapt import _native_kernel
    return _native_kernel


@pytest.mark.native
@pytest.mark.parametrize("rows", [0, 1, 32, 2048])
@pytest.mark.parametrize("table_size", [1, 31, 32, 65536])
@pytest.mark.parametrize("strides", [False, True])
def test_native_exact(native, rows, table_size, strides):
    args = fixture(rows=rows, table_size=table_size, strides=strides)
    before = copy.deepcopy(args)
    with inference_backend("native"):
        actual = predict_coded_memory_buckets(*args)
    assert actual.dtype == np.float64
    assert actual.tobytes() == scalar_oracle(*args).tobytes()
    for a, b in zip(args[2], before[2]):
        np.testing.assert_array_equal(a, b)


@pytest.mark.native
@pytest.mark.parametrize("dtype", [np.uint8, np.int8, np.uint16, np.int16, np.uint32, np.int32, np.uint64, np.int64])
def test_code_dtypes_and_wrapping(native, dtype):
    args = fixture(table_size=31, code_dtype=dtype)
    if dtype == np.int64:
        for level in args[0]:
            for codes in level["codes"]:
                codes[0][:] = np.iinfo(np.int64).max
                codes[1][:] = 17
    if dtype == np.uint64:
        for level in args[0]:
            for codes in level["codes"]:
                codes[0][:] = np.iinfo(np.uint64).max
    with inference_backend("native"):
        result = predict_coded_memory_buckets(*args)
    assert result.tobytes() == scalar_oracle(*args).tobytes()


@pytest.mark.native
@pytest.mark.parametrize("mutation,error", [
    ("bad_bucket", IndexError), ("bad_feature", IndexError),
    ("z_dtype", TypeError), ("table_dtype", TypeError),
    ("short_codes", ValueError), ("short_levels", ValueError),
    ("bad_table_size", ValueError), ("byteswap", TypeError),
])
def test_native_rejects_invalid_inputs(native, mutation, error):
    levels, encoders, z, intercept, size = fixture()
    if mutation == "bad_bucket": z[0][0, 0] = 65535
    if mutation == "bad_feature": levels[0]["groups"][0][0] = 99
    if mutation == "z_dtype": z[0] = z[0].astype(np.int64)
    if mutation == "table_dtype": levels[0]["tables"][0] = levels[0]["tables"][0].astype(np.float32)
    if mutation == "short_codes": levels[0]["codes"][0].pop()
    if mutation == "short_levels": z.pop()
    if mutation == "bad_table_size": size = 0
    if mutation == "byteswap": z[0] = z[0].astype(">u2")
    with pytest.raises(error):
        native.predict_head(levels, [e.support_ for e in encoders], z, intercept, size)


@pytest.mark.native
def test_empty_groups_and_default_main_features(native):
    args = fixture()
    for level in args[0]:
        level.pop("main_features")
        level["groups"] = [np.array([], dtype=np.intp)]
        level["codes"] = [[]]
        level["tables"] = [level["tables"][0]]
    with inference_backend("native"):
        assert predict_coded_memory_buckets(*args).tobytes() == reference(*args).tobytes()


def test_independent_overflow_oracle_matches_reference():
    z = np.array([[0], [1]], dtype=np.uint16)
    code = np.array([np.iinfo(np.int64).max, np.iinfo(np.int64).min])
    second = np.array([17, -17], dtype=np.int64)
    expected = np.array([((int(a)+int(b)+2**63) % 2**64-2**63) % 31 for a, b in zip(code, second)], dtype=np.uint16)
    np.testing.assert_array_equal(addresses(z, [0, 0], [code, second], 31), expected)


@pytest.mark.native
@pytest.mark.parametrize("retained_levels", [0, 1])
def test_early_stop_prefix_and_intercept_only(native, retained_levels):
    levels, encoders, z, intercept, size = fixture()
    levels = levels[:retained_levels]
    with inference_backend("native"):
        actual = predict_coded_memory_buckets(levels, encoders, z, intercept, size)
    expected = reference(levels, encoders, z, intercept, size)
    assert actual.tobytes() == expected.tobytes()
