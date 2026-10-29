"""PRIVATE exporter-only physical backing rewrite. No inference module required."""

import hashlib
import pickle

import numpy as np


class ImmutableOneDimensional:
    def __init__(self, array):
        self.raw = array.tobytes(order="C")
        self.dtype = array.dtype.str

    def __reduce__(self):
        # NumPy itself reconstructs exactly one ndarray over immutable bytes;
        # no reshape/base-array/memoryview object chain and no custom decoder.
        return np.frombuffer, (self.raw, self.dtype)


def eligible(value):
    return (
        type(value) is np.ndarray
        and value.ndim == 1
        and value.flags.c_contiguous
        and not value.dtype.hasobject
    )


def compile_blob(blob, metadata, framing):
    framing.validate_payload(blob, metadata)
    payload = pickle.loads(blob)
    if payload["kind"] != "single":
        return blob, dict(metadata), dict(changed=False, multiclass_unchanged=True, target_arrays=0)
    target_ids = set()
    seen = set()

    def census(x):
        if id(x) in seen:
            return
        seen.add(id(x))
        if eligible(x):
            target_ids.add(id(x))
        elif isinstance(x, dict):
            for v in x.values():
                census(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                census(v)

    census(payload["levels"])
    if not target_ids:
        return blob, dict(metadata), dict(changed=False, target_arrays=0)
    memo = {}
    preserved = 0

    def rewrite(x):
        nonlocal preserved
        if id(x) in memo:
            return memo[id(x)]
        # Preserve C3's already-qualified one-array/bytes metadata layout while
        # repickling. This branch adds no new metadata sharing or content pool.
        old_short = eligible(x) and type(x.base) is bytes
        if id(x) in target_ids or old_short:
            y = ImmutableOneDimensional(x)
            preserved += int(old_short and id(x) not in target_ids)
        elif isinstance(x, dict):
            y = {}
            memo[id(x)] = y
            y.update((k, rewrite(v)) for k, v in x.items())
        elif isinstance(x, list):
            y = []
            memo[id(x)] = y
            y.extend(rewrite(v) for v in x)
        elif isinstance(x, tuple):
            y = tuple(rewrite(v) for v in x)
        elif type(x).__name__ == "_ResolutionView":
            y = object.__new__(type(x))
            memo[id(x)] = y
            y.__dict__.update(rewrite(vars(x)))
        else:
            y = x
        memo[id(x)] = y
        return y

    packed = pickle.dumps(rewrite(payload), protocol=5)
    new_meta = dict(metadata, payload_sha256=hashlib.sha256(packed).hexdigest())
    framing.validate_payload(packed, new_meta)
    assert new_meta["state_sha256"] == metadata["state_sha256"]
    return (
        packed,
        new_meta,
        dict(
            changed=True,
            target_arrays=len(target_ids),
            qualified_metadata_arrays_preserved=preserved,
            coefficients_changed=False,
            content_deduplication=False,
            precision_change=False,
        ),
    )
