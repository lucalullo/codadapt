"""PRIVATE exact repeated numeric metadata owners; original loader/kernel unchanged.

Only duplicated contiguous 1D encoder arrays are interned. Coefficients and
object arrays are excluded. Each shared array reconstructs over immutable bytes
using NumPy itself; no new inference dependency or decompression is required.
This is trusted-pickle migration, not a safe-unpickling security boundary.
"""

import hashlib
import pickle

import numpy as np


class ImmutableNumeric:
    def __init__(self, a):
        self.raw = a.tobytes(order="C")
        self.dtype = a.dtype.str

    def __reduce__(self):
        return np.frombuffer, (self.raw, self.dtype)


def signature(value):
    if (
        type(value) is np.ndarray
        and value.ndim == 1
        and value.flags.c_contiguous
        and not value.dtype.hasobject
    ):
        return value.dtype.str, value.shape, value.strides, value.tobytes()
    return None


def children(value):
    if isinstance(value, dict):
        return value.values()
    if isinstance(value, (list, tuple)):
        return value
    if type(value).__name__ == "_ResolutionView":
        return [vars(value)]
    return []


def intern_encoder(encoder):
    groups, visited = {}, set()

    def census(value):
        if id(value) in visited:
            return
        visited.add(id(value))
        key = signature(value)
        if key is not None:
            groups.setdefault(key, []).append(value)
        else:
            for child in children(value):
                census(child)

    census(encoder)
    shared = {key: ImmutableNumeric(values[0]) for key, values in groups.items() if len(values) > 1}
    memo = {}

    def rewrite(value):
        if id(value) in memo:
            return memo[id(value)]
        key = signature(value)
        if key in shared:
            result = shared[key]
        elif isinstance(value, dict):
            result = {}
            memo[id(value)] = result
            result.update((k, rewrite(v)) for k, v in value.items())
        elif isinstance(value, list):
            result = []
            memo[id(value)] = result
            result.extend(rewrite(v) for v in value)
        elif isinstance(value, tuple):
            result = tuple(rewrite(v) for v in value)
        elif type(value).__name__ == "_ResolutionView":
            result = object.__new__(type(value))
            memo[id(value)] = result
            result.__dict__.update(rewrite(vars(value)))
        else:
            result = value
        memo[id(value)] = result
        return result

    return rewrite(encoder), dict(
        groups=len(shared),
        removed_array_objects=sum(len(v) - 1 for v in groups.values() if len(v) > 1),
    )


def compile_blob(blob, metadata, framing):
    framing.validate_payload(blob, metadata)
    payload = pickle.loads(blob)
    if payload["kind"] != "single":
        return (
            blob,
            dict(metadata),
            dict(groups=0, removed_array_objects=0, unchanged_multiclass=True),
        )
    payload["encoder"], audit = intern_encoder(payload["encoder"])
    if not audit["groups"]:
        return blob, dict(metadata), audit
    packed = pickle.dumps(payload, protocol=5)
    new_metadata = dict(metadata, payload_sha256=hashlib.sha256(packed).hexdigest())
    framing.validate_payload(packed, new_metadata)
    return packed, new_metadata, audit
