"""Explicit current-native fitted-state bridge; never trains or rebalances."""

import copy
import hashlib
import pickle
from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd

from . import _contract, backing_compiler, metadata_compiler
from . import portable_native_runtime as native
from . import validated_native_format as framing


def _clone(value, memo):
    if id(value) in memo:
        return memo[id(value)]
    if isinstance(value, Enum) and type(value).__name__ == "_BooleanKey":
        result = native._BooleanKey[value.name]
    elif type(value).__name__ == "_ResolutionView":
        result = object.__new__(native._ResolutionView)
        memo[id(value)] = result
        result.__dict__.update(_clone(vars(value), memo))
    elif isinstance(value, np.ndarray):
        result = value.copy(order="K")
        memo[id(value)] = result
        if result.dtype.hasobject:
            for index in np.ndindex(result.shape):
                result[index] = _clone(value[index], memo)
    elif isinstance(value, pd.Index):
        if any(isinstance(v, Enum) and type(v).__name__ == "_BooleanKey" for v in value):
            result = pd.Index([_clone(v, memo) for v in value], dtype=value.dtype, name=value.name)
        else:
            result = value.copy(deep=True)
    elif isinstance(value, dict):
        result = {}
        memo[id(value)] = result
        result.update((_clone(k, memo), _clone(v, memo)) for k, v in value.items())
    elif isinstance(value, list):
        result = []
        memo[id(value)] = result
        result.extend(_clone(v, memo) for v in value)
    elif isinstance(value, tuple):
        result = tuple(_clone(v, memo) for v in value)
    else:
        result = copy.deepcopy(value)
    memo[id(value)] = result
    return result


def _source(model):
    import codadapt
    from codadapt import CodAdaptClassifier, CodAdaptRegressor

    if type(model) not in (CodAdaptClassifier, CodAdaptRegressor):
        raise TypeError("Only exact qualified native estimator types can be exported")
    if not getattr(model, "_is_fitted_", False):
        raise ValueError("A fitted native estimator is required")
    if codadapt.__version__ != _contract.CONTRACT["native_version"]:
        raise ValueError("Unsupported native product version")
    package = Path(codadapt.__file__).resolve().parent
    actual = {
        "codadapt/" + f.relative_to(package).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(package.rglob("*.py"))
    }
    if actual != _contract.CONTRACT["native_sources"]:
        raise ValueError("Native source fingerprint is not this qualified private candidate")
    for name in ("fit", "predict", "predict_proba", "decision_function", "_decision"):
        if name in vars(model):
            raise ValueError("Instance method overrides are not exportable")
    return "classification" if type(model) is CodAdaptClassifier else "regression"


def export(model, path):
    family = _source(model)
    origin = _contract.producer()
    _contract.validate_producer(origin)
    before = pickle.dumps(model, protocol=5)
    is_multi = hasattr(model, "_ovr_artifact_")
    task = "multiclass" if is_multi else "binary" if family == "classification" else "regression"
    heads = (
        [(h.intercept, h.levels) for h in model._heads_]
        if is_multi
        else [(model.intercept_, model.levels_)]
    )
    size = model._heads_[0].table_size if is_multi else model.table_size
    classes = None if task == "regression" else model.classes_
    state = dict(encoder=vars(model.encoder_), heads=heads, classes=classes, table_size=size)
    state_hash = framing.state_digest(state)
    if is_multi:
        wire = model._ovr_artifact_.__getstate__()
        wire = wire[:-1] + ({},)
        payload = dict(
            schema=1, version=framing.VERSION, task=task, kind="multiclass_wire", wire=_clone(wire, {})
        )
    else:
        payload = _clone(
            dict(
                schema=1,
                version=framing.VERSION,
                task=task,
                kind="single",
                encoder=vars(model.encoder_),
                levels=model.levels_,
                intercept=model.intercept_,
                table_size=size,
                classes=classes,
            ),
            {},
        )
    blob = pickle.dumps(payload, protocol=5)
    metadata = dict(
        schema=framing.SCHEMA,
        source_version=framing.VERSION,
        task=task,
        payload_sha256=hashlib.sha256(blob).hexdigest(),
        state_sha256=state_hash,
        original_model_sha256=hashlib.sha256(before).hexdigest(),
        sections=[],
        producer=origin,
    )
    framing.validate_payload(blob, metadata)
    blob, metadata, sharing = metadata_compiler.compile_blob(blob, metadata, framing)
    blob, metadata, backing = backing_compiler.compile_blob(blob, metadata, framing)
    if pickle.dumps(model, protocol=5) != before:
        raise RuntimeError("Export must not mutate the native estimator")
    receipt = dict(
        artifact_sha256=None,
        artifact_bytes=None,
        task=task,
        predictive_state_sha256=state_hash,
        producer=origin,
        input_model_sha256=metadata["original_model_sha256"],
        sharing=sharing,
        backing=backing,
    )
    publication = framing.atomic_save(blob, metadata, path)
    receipt["artifact_sha256"] = publication["artifact_sha256"]
    receipt["artifact_bytes"] = publication["artifact_bytes"]
    return receipt
