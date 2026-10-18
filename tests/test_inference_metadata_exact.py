"""Regression controls for exact inference and immutable metadata ownership."""

import pickle
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
import pytest

from codadapt import CodAdaptClassifier, CodAdaptRegressor
from codadapt._core import addresses
from codadapt.preprocessing import BucketEncoder, _BooleanKey, _pool_categorical_strings


def test_address_generators_and_readonly_int64_operands():
    z = np.array([[0, 1], [2, 0], [1, 2]], dtype=np.uint16)
    codes = [np.array([2**40, -17, 83], dtype=np.int64), np.array([6, 9, 12])]
    originals = [code.tobytes() for code in codes]
    for code in codes:
        code.flags.writeable = False
    for size in [31, 256]:
        expected = np.array(
            [(int(codes[0][a]) + int(codes[1][b])) % size for a, b in z], dtype=np.uint16
        )
        np.testing.assert_array_equal(addresses(z, [0, 1], codes, size), expected)
        np.testing.assert_array_equal(addresses(z, iter([0, 1]), iter(codes), size), expected)
    assert [code.tobytes() for code in codes] == originals


@pytest.mark.parametrize("dtype", [np.float16, np.float32, np.float64, np.uint64])
def test_numeric_array_codes_match_dataframe_with_readonly_strided_input(dtype):
    x = np.arange(384).reshape(128, 3).astype(dtype)
    if np.issubdtype(dtype, np.floating):
        x[::13, 0] = np.nan
        x[1, 1] = -0.0
    array_encoder = BucketEncoder(n_bins=16, random_state=8)
    frame_encoder = BucketEncoder(n_bins=16, random_state=8)
    array_encoder.fit_transform_levels(x, [4, 8, 16])
    frame_encoder.fit_transform_levels(pd.DataFrame(x), [4, 8, 16])
    probe = x[::-3]
    probe.flags.writeable = False
    original = probe.tobytes()
    actual = array_encoder.transform_levels(probe)
    expected = frame_encoder.transform_levels(pd.DataFrame(probe))
    for left, right in zip(actual, expected):
        assert left.dtype == right.dtype and left.tobytes() == right.tobytes()
    assert probe.tobytes() == original


def test_metadata_pool_preserves_boolean_numeric_and_string_subclass_keys():
    class SpecialString(str):
        pass

    a = "shared_word"
    b = (a + "x")[:-1]
    special = SpecialString(a)
    schemas = []
    for word in [a, b, special]:
        values = [_BooleanKey.TRUE, 1, _BooleanKey.FALSE, 0, word, "True"]
        schemas.append(
            {
                "kind": "categorical",
                "vocabulary": {value: i + 3 for i, value in enumerate(values)},
                "observed_categories": pd.Index(values, dtype=object),
            }
        )
    before = [(list(s["vocabulary"].items()), s["observed_categories"].tolist()) for s in schemas]
    _pool_categorical_strings(SimpleNamespace(schemas_=schemas))
    assert before == [
        (list(s["vocabulary"].items()), s["observed_categories"].tolist()) for s in schemas
    ]
    assert schemas[0]["observed_categories"][4] is schemas[1]["observed_categories"][4]
    assert schemas[2]["observed_categories"][4] is special
    assert len(schemas[0]["vocabulary"]) == 6


def test_metadata_pool_large_owner_guard_is_noop():
    a = "shared_word"
    b = (a + "x")[:-1]
    schemas = [
        {
            "kind": "categorical",
            "vocabulary": {a: 3},
            "observed_categories": pd.Index(range(16385)),
        },
        {
            "kind": "categorical",
            "vocabulary": {b: 3},
            "observed_categories": pd.Index(range(16384)),
        },
    ]
    original = [schema["vocabulary"] for schema in schemas]
    _pool_categorical_strings(SimpleNamespace(schemas_=schemas))
    assert all(schema["vocabulary"] is old for schema, old in zip(schemas, original))


@pytest.mark.parametrize("task", ["binary", "multiclass", "regression"])
@pytest.mark.parametrize("format_name", ["pickle", "joblib"])
def test_persistence_restores_shared_immutable_category_spellings(tmp_path, task, format_name):
    rng = np.random.default_rng(19)
    n = 192
    x = pd.DataFrame(
        {
            "cat_a": [f"state_{i % 8}" for i in range(n)],
            "cat_b": [f"state_{i % 8}" for i in range(n)],
            "value": rng.normal(size=n),
        }
    )
    if task == "regression":
        model = CodAdaptRegressor(random_state=3).fit(x, x.value.to_numpy())
    else:
        model = CodAdaptClassifier(random_state=3).fit(
            x, np.arange(n) % (3 if task == "multiclass" else 2)
        )
    expected = model.predict(x.iloc[:17])
    path = tmp_path / ("model." + format_name)
    if format_name == "pickle":
        path.write_bytes(pickle.dumps(model))
        restored = pickle.loads(path.read_bytes())
    else:
        joblib.dump(model, path)
        restored = joblib.load(path)
    np.testing.assert_array_equal(restored.predict(x.iloc[:17]), expected)
    first, second = restored.encoder_.schemas_[:2]
    left = {v: v for v in first["observed_categories"]}
    right = {v: v for v in second["observed_categories"]}
    assert left.keys() == right.keys()
    assert all(left[v] is right[v] for v in left)
