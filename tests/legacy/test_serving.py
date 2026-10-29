"""Integration contracts for fitted-only serving; no predictive tuning."""

import hashlib
import json
import os
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.pipeline import Pipeline

from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor
from codadapt.serving import export_model, load_model


def test_public_imports_are_deferred_and_serving_needs_no_training_imports():
    import codadapt

    root = str(Path(codadapt.__file__).parent.parent)
    script = """
import importlib.abc,sys
sys.path.insert(0,ROOT)
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'numpy','pandas','scipy','sklearn','codadapt_serving_private'}:
            raise ImportError('unexpected eager dependency: '+fullname)
sys.meta_path.insert(0,Block())
import codadapt
from codadapt.serving import export_model,load_model
assert callable(export_model) and callable(load_model)
assert 'CodAdaptClassifier' in dir(codadapt)
assert not any(n in sys.modules for n in ('numpy','pandas','scipy','sklearn'))
try:
    codadapt.nonexistent_attribute
except AttributeError:
    pass
else:
    raise AssertionError('unknown attributes must reject')
""".replace("ROOT", repr(root))
    done = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script], capture_output=True, text=True, timeout=60
    )
    assert done.returncode == 0, done.stdout + done.stderr


def test_native_alias_and_clone_contract():
    assert CodAdapt is CodAdaptClassifier
    for model in (
        CodAdaptClassifier(),
        CodAdaptClassifier(class_weight="balanced"),
        CodAdaptRegressor(),
    ):
        assert clone(model).get_params() == model.get_params()


@pytest.fixture(
    scope="module",
    params=[
        "binary_none",
        "binary_balanced",
        "multiclass_none",
        "multiclass_balanced",
        "regression",
    ],
)
def fitted(request):
    rng = np.random.RandomState(42)
    n = 120
    x = pd.DataFrame(
        {
            "number": rng.normal(size=n),
            "other": rng.normal(size=n),
            "category": np.resize(["red", "green", "blue"], n),
            "flag": np.arange(n) % 2 == 0,
        }
    )
    weight = np.linspace(0.25, 2.5, n)
    weight[[0, 15]] = 0
    options = dict(random_state=42, n_tables=2, table_size=32, early_stopping=False)
    if request.param == "regression":
        y = x.number.to_numpy() + x.other.to_numpy() ** 2
        model = CodAdaptRegressor(**options)
    else:
        if request.param.startswith("binary"):
            y = np.where(np.arange(n) < 90, "major", "minor")
        else:
            y = np.repeat(["galaxy", "quasar", "star"], [80, 32, 8])
        model = CodAdaptClassifier(
            class_weight="balanced" if request.param.endswith("balanced") else None, **options
        )
    model.fit(x, y, sample_weight=weight)
    return model, x


def test_roundtrip_predictions_state_and_native_pipeline(fitted, tmp_path):
    model, x = fitted
    before = pickle.dumps(model, protocol=5)
    file = tmp_path / "model.cda"
    receipt = export_model(model, file)
    assert pickle.dumps(model, protocol=5) == before
    assert receipt["artifact_sha256"] == hashlib.sha256(file.read_bytes()).hexdigest()
    assert receipt["artifact_bytes"] == file.stat().st_size
    loaded = load_model(file, trusted=True, expected_sha256=receipt["artifact_sha256"])
    for n in (1, 32, len(x)):
        for method in ("predict", "decision_function", "predict_proba"):
            if method != "predict" and not isinstance(model, CodAdaptClassifier):
                continue
            actual, expected = (
                getattr(loaded, method)(x.iloc[:n]),
                getattr(model, method)(x.iloc[:n]),
            )
            assert actual.dtype == expected.dtype and actual.shape == expected.shape
            np.testing.assert_array_equal(actual, expected)
            if not actual.dtype.hasobject:
                assert actual.tobytes() == expected.tobytes()
    np.testing.assert_array_equal(Pipeline([("model", model)]).predict(x), model.predict(x))
    assert pickle.dumps(model, protocol=5) == before


def test_explicit_trust_receipt_and_corruption_guards(fitted, tmp_path):
    model, _ = fitted
    file = tmp_path / "model.cda"
    receipt = export_model(model, file)
    with pytest.raises(ValueError, match="trusted=True"):
        load_model(file)
    with pytest.raises(ValueError, match="expected_checksum"):
        load_model(file, trusted=True, expected_sha256="0" * 64)
    raw = bytearray(file.read_bytes())
    raw[-1] ^= 1
    file.write_bytes(raw)
    with pytest.raises(ValueError, match="checksum"):
        load_model(file, trusted=True)
    with pytest.raises(ValueError, match="size_limit"):
        load_model(file, trusted=True, max_bytes=1)
    assert receipt["artifact_sha256"] != hashlib.sha256(file.read_bytes()).hexdigest()


def test_foreign_minor_rejects_before_unpickling_with_specific_error(fitted, tmp_path, monkeypatch):
    from codadapt.serving import validated_native_format as framing

    model, _ = fitted
    file = tmp_path / "model.cda"
    export_model(model, file)
    raw = file.read_bytes()
    fields = list(framing.HEADER.unpack(raw[: framing.HEADER.size]))
    mlen = fields[4]
    meta_raw = raw[framing.HEADER.size : framing.HEADER.size + mlen]
    metadata = json.loads(meta_raw)
    # Equal-width minor digits keep the section length/offsets unchanged.
    minor = metadata["producer"]["python"][1]
    metadata["producer"]["python"][1] = 14 if minor != 14 else 13
    changed = json.dumps(
        metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    assert len(changed) == mlen
    payload = raw[framing.HEADER.size + mlen :]
    fields[-1] = hashlib.sha256(changed + payload).digest()
    file.write_bytes(framing.HEADER.pack(*fields) + changed + payload)
    called = []

    def reject_unpickler(*args, **kwargs):
        called.append(True)
        raise AssertionError("unpickling must not precede producer compatibility")

    monkeypatch.setattr(framing.pickle, "Unpickler", reject_unpickler)
    with pytest.raises(ValueError, match="COMPATIBILITY.*metadata.producer.*Cross-Python-minor"):
        load_model(file, trusted=True)
    assert not called


def test_private_envelope_three_is_not_implicitly_migrated(fitted, tmp_path, monkeypatch):
    from codadapt.serving import validated_native_format as framing

    model, _ = fitted
    file = tmp_path / "model.cda"
    export_model(model, file)
    raw = file.read_bytes()
    file.write_bytes(b"CDNIMG3\x00" + raw[8:])

    def reject_unpickler(*args, **kwargs):
        raise AssertionError("old envelopes must reject before unpickling")

    monkeypatch.setattr(framing.pickle, "Unpickler", reject_unpickler)
    with pytest.raises(ValueError, match="header.magic"):
        load_model(file, trusted=True)


def test_other_dependency_profile_rejects_before_unpickling(fitted, tmp_path, monkeypatch):
    from codadapt.serving import validated_native_format as framing

    model, _ = fitted
    file = tmp_path / "model.cda"
    export_model(model, file)
    raw = file.read_bytes()
    fields = list(framing.HEADER.unpack(raw[: framing.HEADER.size]))
    metadata = json.loads(raw[framing.HEADER.size : framing.HEADER.size + fields[4]])
    payload = raw[framing.HEADER.size + fields[4] :]
    profile = (metadata["producer"]["numpy"], metadata["producer"]["pandas"])
    other = ("1.26.4", "2.2.3") if profile == ("2.5.4", "3.1.0") else ("2.5.4", "3.1.0")
    metadata["producer"]["numpy"], metadata["producer"]["pandas"] = other
    # Construct a checksum-consistent foreign-profile file without asking the
    # production encoder to authorize incompatible metadata.
    for _ in range(10):
        encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
        metadata["sections"][0]["length"] = len(encoded)
        metadata["sections"][1]["offset"] = framing.HEADER.size + len(encoded)
        updated = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
        if len(updated) == len(encoded):
            break
    else:
        raise AssertionError("metadata framing did not stabilize")
    fields[4] = len(updated)
    fields[-1] = hashlib.sha256(updated + payload).digest()
    file.write_bytes(framing.HEADER.pack(*fields) + updated + payload)

    def forbidden(*args, **kwargs):
        raise AssertionError("a known but different dependency profile must reject before pickle")

    monkeypatch.setattr(framing.pickle, "Unpickler", forbidden)
    with pytest.raises(ValueError, match="COMPATIBILITY.*producer.*compatibility: numpy"):
        load_model(file, trusted=True)


def test_wheel_contains_exact_serving_contract_and_sources():
    import zipfile
    from email import message_from_bytes

    import codadapt

    dist = Path(os.environ["CODADAPT_TEST_DIST"])
    wheel = next(dist.glob(f"codadapt-{codadapt.__version__}-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        contract = json.loads(archive.read("codadapt/serving/source_contract.json"))
        for name, digest in contract["native_sources"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        meta = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        requirements = message_from_bytes(archive.read(meta)).get_all("Requires-Dist")
        assert any(r.startswith("scikit-learn") for r in requirements)
        assert any(r.startswith("scipy") for r in requirements)
