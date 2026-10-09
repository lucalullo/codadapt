"""Dense float64 coefficient packing; immutable metadata pooling, no compression."""

import copy

import numpy as np

from .preprocessing import BucketEncoder, _ResolutionView


def minimal_index(a):
    if a.dtype.kind not in "iu" or (a.size and a.min() < 0):
        return a
    maximum = int(a.max()) if a.size else 0
    dtype = (
        np.uint8
        if maximum <= 255
        else np.uint16
        if maximum <= 65535
        else np.uint32
        if maximum <= 2**32 - 1
        else a.dtype
    )
    narrowed = a.astype(dtype)
    assert np.array_equal(narrowed.astype(a.dtype), a)
    return narrowed


class Pool:
    def __init__(self):
        self.parts, self.sizes, self.memo = {}, {}, {}

    def add(self, original, indices=True):
        a = minimal_index(original) if indices else original
        a = np.ascontiguousarray(a)
        signature = (a.dtype.str, a.shape, a.tobytes())
        if signature not in self.memo:
            dtype = a.dtype.str
            offset = self.sizes.get(dtype, 0)
            self.parts.setdefault(dtype, []).append(a.ravel().copy())
            self.sizes[dtype] = offset + a.size
            self.memo[signature] = ("a", dtype, offset, a.shape)
        return self.memo[signature]

    def buffers(self):
        return {dtype: np.concatenate(arrays) for dtype, arrays in self.parts.items()}


def encode(value, pool):
    if isinstance(value, np.ndarray) and value.dtype.kind != "O":
        return pool.add(value)
    if isinstance(value, dict):
        return ("d", tuple((k, encode(v, pool)) for k, v in value.items()))
    if isinstance(value, list):
        return ("l", tuple(encode(v, pool) for v in value))
    if isinstance(value, tuple):
        return ("t", tuple(encode(v, pool) for v in value))
    if isinstance(value, _ResolutionView):
        return ("v", encode(vars(value), pool))
    return ("p", copy.deepcopy(value))


def decode(value, buffers, memo):
    tag, *rest = value
    if tag == "a":
        dtype, offset, shape = rest
        key = (dtype, offset, tuple(shape))
        if key not in memo:
            length = int(np.prod(shape))
            a = buffers[dtype][offset : offset + length].reshape(shape)
            a.flags.writeable = False
            memo[key] = a
        return memo[key]
    if tag == "p":
        return rest[0]
    if tag == "d":
        return {k: decode(v, buffers, memo) for k, v in rest[0]}
    if tag in ("l", "t"):
        values = [decode(v, buffers, memo) for v in rest[0]]
        return values if tag == "l" else tuple(values)
    if tag == "v":
        result = object.__new__(_ResolutionView)
        result.__dict__.update(decode(rest[0], buffers, memo))
        return result
    raise ValueError("Unsupported artifact tag")


def pack(encoder, classes, heads, params):
    pool = Pool()
    enc = encode(vars(encoder), pool)
    values, records, cursor = [], [], 0
    sizes = {h.table_size for h in heads}
    if len(sizes) != 1:
        raise ValueError("Frozen native heads require a common table size")

    def coefficients(a):
        nonlocal cursor
        if a.dtype != np.float64 or a.ndim != 1:
            raise ValueError("Predictive coefficient dtype/shape must remain float64/1D")
        record = (cursor, len(a))
        cursor += len(a)
        values.append(a.copy())
        return record

    for head in heads:
        levels = []
        for level in head.levels:
            levels.append(
                (
                    level["n_bins"],
                    pool.add(level["main_features"]),
                    tuple(coefficients(a) for a in level["main_tables"]),
                    tuple(pool.add(a) for a in level["groups"]),
                    tuple(tuple(pool.add(a) for a in group) for group in level["codes"]),
                    tuple(coefficients(a) for a in level["tables"]),
                )
            )
        records.append((head.intercept, tuple(levels)))
    dense = np.concatenate(values) if values else np.empty(0, dtype=np.float64)
    return (
        1,
        enc,
        classes.copy(),
        pool.buffers(),
        dense,
        tuple(records),
        sizes.pop(),
        copy.deepcopy(params),
    )


def unpack(wire):
    version, enc, classes, buffers, values, records, table_size, params = wire
    if version != 1 or values.dtype != np.float64:
        raise ValueError("Unsupported artifact schema or coefficient dtype")
    for buffer in [values, *buffers.values()]:
        buffer.flags.writeable = False
    memo = {}
    encoder = object.__new__(BucketEncoder)
    encoder.__dict__.update(decode(enc, buffers, memo))

    def coefficients(ref):
        offset, length = ref
        a = values[offset : offset + length]
        a.flags.writeable = False
        return a

    result = []
    for intercept, levels in records:
        result.append(
            (
                intercept,
                [
                    dict(
                        n_bins=n,
                        main_features=decode(main, buffers, memo),
                        main_tables=[coefficients(a) for a in main_values],
                        groups=[decode(a, buffers, memo) for a in groups],
                        codes=[[decode(a, buffers, memo) for a in group] for group in codes],
                        tables=[coefficients(a) for a in tables],
                    )
                    for n, main, main_values, groups, codes, tables in levels
                ],
            )
        )
    return encoder, classes, result, table_size, params
