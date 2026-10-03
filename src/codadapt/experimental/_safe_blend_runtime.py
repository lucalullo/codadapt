"""Frozen exact R77/post-R77 deployment;no inherited private import."""

import numpy as np
import pandas as pd


class SharedInputPreparation:
    def __init__(self, original):
        self.columns = original.columns
        self.vocab = original.vocab

    def transform(self, x):
        if not isinstance(x, pd.DataFrame):
            x = pd.DataFrame(x, columns=self.columns)
        assert tuple(x.columns) == self.columns
        if not self.vocab:
            # Original assigns the same per-column float64 values into a matrix.
            return x.to_numpy(dtype=np.float64)
        a = np.empty(x.shape, dtype=np.float64, order="F")
        for j, col in enumerate(self.columns):
            values = x[col]
            if j in self.vocab:
                values = values.map(self.vocab[j])
            a[:, j] = values.to_numpy(dtype=np.float64)
        return a


class BasePredictionState:
    """Only inference state; all original Base tables and ordered additions retained."""

    def __init__(self, original):
        enc = original.shared_encoder_
        self.schemas = []
        for s in enc.schemas_:
            if s["kind"] == "numeric":
                self.schemas.append(("numeric", s["thresholds"], s["missing_bucket"]))
            else:
                # The Base was trained on external-encoded real float64 categories.
                keys = np.array(sorted(s["vocabulary"]), dtype=np.float64)
                values = np.array([s["vocabulary"][v] for v in keys], dtype=np.uint16)
                observed = np.asarray(s["observed_categories"], dtype=np.float64)
                self.schemas.append(
                    (
                        "categorical",
                        keys,
                        values,
                        np.sort(observed) if s["n_rare_categories"] else np.empty(0),
                    )
                )
        self.mappings = enc.level_mappings_
        self.encoders = original.encoders_
        self.levels = original.levels_
        self.intercept = original.intercept_
        self.table_size = original.table_size

    def encode(self, a):
        if np.isinf(a).any():
            raise ValueError("Input contains infinity; original Base does not support it.")
        finest = np.empty(a.shape, dtype=np.uint16)
        for j, s in enumerate(self.schemas):
            v = a[:, j]
            missing = np.isnan(v)
            if s[0] == "numeric":
                b = np.searchsorted(s[1], v, side="right").astype(np.uint16)
                b[missing] = s[2]
            else:
                keys, values, observed = s[1:]
                b = np.full(len(v), 2, dtype=np.uint16)
                if len(keys):
                    ix = np.searchsorted(keys, v)
                    clipped = np.minimum(ix, len(keys) - 1)
                    matched = (ix < len(keys)) & (keys[clipped] == v)
                    b[matched] = values[clipped[matched]]
                if len(observed):
                    ix = np.searchsorted(observed, v)
                    matched = (ix < len(observed)) & (
                        observed[np.minimum(ix, len(observed) - 1)] == v
                    )
                    b[(b == 2) & matched] = 1
                b[missing] = 0
            finest[:, j] = b
        levels = []
        for maps in self.mappings:
            z = np.empty_like(finest)
            for j, mapping in enumerate(maps):
                z[:, j] = mapping[finest[:, j]]
            levels.append(z)
        return levels

    def lookup(self, levels):
        from codadapt._training import predict_coded_memory_buckets

        return predict_coded_memory_buckets(
            self.levels, self.encoders, levels, self.intercept, self.table_size
        )

    def predict(self, a):
        return self.lookup(self.encode(a))


class PackedCompiledState:
    def __init__(self, original):
        d = original.dictionary
        assert d.kind == "SBD"
        self.feature_count = d.features
        self.capacity = d.capacity
        self.kind = np.array(
            [{"missing": 0, "eq": 1, "le": 2}[p[0]] for p in d.primitives], dtype=np.uint8
        )
        self.feature = np.array([p[1] for p in d.primitives], dtype=np.uint16)
        self.cut = np.array([p[2] for p in d.primitives], dtype=np.float64)
        order = np.lexsort((self.kind, self.feature))
        self.group_indices = order.astype(np.uint16)
        pairs = np.column_stack((self.feature[order], self.kind[order]))
        starts = np.r_[0, np.flatnonzero(np.any(pairs[1:] != pairs[:-1], axis=1)) + 1]
        self.group_offsets = np.r_[starts, len(order)].astype(np.uint16)
        self.group_features = pairs[starts, 0].astype(np.uint16)
        self.group_kinds = pairs[starts, 1].astype(np.uint8)
        p = len(d.primitives)
        self.ids = np.full((4, len(d.terms)), p, dtype=np.uint16)
        self.signs = np.zeros_like(self.ids, dtype=bool)
        for k, (ids, signs) in enumerate(d.terms):
            self.ids[: len(ids), k] = ids
            self.signs[: len(ids), k] = signs
        self.coef = original.coef
        self.intercept = original.intercept

    def transform(self, x, out=None, layout="grouped"):
        n, p = len(x), len(self.kind)
        if out is None:
            out = np.empty((n, p + self.ids.shape[1]), dtype=np.float64, order="C")
        # Binary primitive values permit bool computation without rounding or approximation.
        primitive = np.ones((p + 1, n), dtype=bool)
        if layout == "grouped":
            previous = None
            for g, (j, kind) in enumerate(zip(self.group_features, self.group_kinds)):
                if j != previous:
                    v = x[:, j]
                    good = np.isfinite(v)
                    previous = j
                ids = self.group_indices[self.group_offsets[g] : self.group_offsets[g + 1]]
                if kind == 0:
                    primitive[ids] = ~good
                elif kind == 1:
                    primitive[ids] = v[None, :] == self.cut[ids, None]
                else:
                    primitive[ids] = good[None, :] & (v[None, :] <= self.cut[ids, None])
        elif layout == "feature":
            values = x.T[self.feature]
            good = np.isfinite(values)
            z = good & (values <= self.cut[:, None])
            eq, missing = self.kind == 1, self.kind == 0
            z[eq] = values[eq] == self.cut[eq, None]
            z[missing] = ~good[missing]
            primitive[:p] = z
        else:
            values = x[:, self.feature]
            good = np.isfinite(values)
            z = good & (values <= self.cut)
            eq, missing = self.kind == 1, self.kind == 0
            z[:, eq] = values[:, eq] == self.cut[eq]
            z[:, missing] = ~good[:, missing]
            primitive[:p] = z.T
        out[:, :p] = primitive[:p].T
        t = np.ones((self.ids.shape[1], n), dtype=bool)
        for ids, signs in zip(self.ids, self.signs):
            t &= primitive[ids] ^ signs[:, None]
        out[:, p:] = t.T
        return out

    def predict(self, a, layout="grouped"):
        prediction = np.empty(len(a), dtype=np.float64)
        width = len(self.coef)
        buf = np.empty((min(2048, len(a)), width), dtype=np.float64)
        for lo in range(0, len(a), 2048):
            block = a[lo : lo + 2048]
            chosen = "feature" if len(a) <= 32 else layout
            matrix = self.transform(block, out=buf[: len(block)], layout=chosen)
            prediction[lo : lo + 2048] = self.intercept + matrix @ self.coef
        return prediction


class Buffers:
    def __init__(self, state, rows, storage="bool", matrix=True):
        p, t = len(state.kind), state.ids.shape[1]
        self.primitive = np.ones((p + 1, rows), dtype=np.uint8 if storage == "uint8" else bool)
        if matrix:
            self.matrix = np.empty((rows, p + t), dtype=np.float64)
        self.binary = np.empty((rows, p + t), dtype=bool) if storage == "staged_bool" else None
        self.terms = np.empty((t, rows), dtype=np.uint8 if storage == "uint8" else bool)
        self.scratch = np.empty_like(self.terms)
        self.good = np.empty(rows, dtype=bool)
        self.rank = np.empty(rows, dtype=np.intp)
        self.storage = storage

    @property
    def bytes(self):
        return sum(
            a.nbytes
            for a in [
                self.primitive,
                getattr(self, "matrix", None),
                self.binary,
                self.terms,
                self.scratch,
                self.good,
                self.rank,
            ]
            if a is not None
        )


def evaluate_primitives(state, x, buffer, method="grouped"):
    n = len(x)
    out = buffer.primitive[:, :n]
    previous = None
    for g, (j, kind) in enumerate(zip(state.group_features, state.group_kinds)):
        if j != previous:
            v = x[:, j]
            np.isfinite(v, out=buffer.good[:n])
            good = buffer.good[:n]
            previous = j
        ids = state.group_indices[state.group_offsets[g] : state.group_offsets[g + 1]]
        if kind == 0:
            out[ids] = ~good
        elif kind == 1:
            out[ids] = v[None, :] == state.cut[ids, None]
        elif method == "ranks":
            cuts = state.cut[ids]
            # Freeze preserves ascending numeric cuts; left gives v<=cut including exact cut.
            assert np.all(cuts[1:] >= cuts[:-1])
            ranks = np.searchsorted(cuts, v, side="left")
            out[ids] = good[None, :] & (ranks[None, :] <= np.arange(len(ids))[:, None])
        else:
            out[ids] = good[None, :] & (v[None, :] <= state.cut[ids, None])
    return out


def evaluate_conjunctions(state, primitive, buffer):
    n = primitive.shape[1]
    if buffer.storage == "bitpacked":
        # Packed across rows, not functions: AND/XOR are exact. Tail discarded on unpack.
        packed = np.packbits(primitive, axis=1, bitorder="little")
        t = np.full((state.ids.shape[1], packed.shape[1]), 255, dtype=np.uint8)
        for ids, signs in zip(state.ids, state.signs):
            t &= packed[ids] ^ np.where(signs[:, None], 255, 0).astype(np.uint8)
        return np.unpackbits(t, axis=1, count=n, bitorder="little")
    t = buffer.terms[:, :n]
    scratch = buffer.scratch[:, :n]
    t.fill(1)
    for ids, signs in zip(state.ids, state.signs):
        np.take(primitive, ids, axis=0, out=scratch, mode="clip")
        np.bitwise_xor(scratch, signs[:, None], out=scratch)
        np.bitwise_and(t, scratch, out=t)
    return t


def compiler_predict(state, a, rows=2048, storage="bool", method="grouped"):
    if len(a) <= 32:
        return state.predict(a)
    output = np.empty(len(a), dtype=np.float64)
    buffer = Buffers(state, min(rows, len(a)), storage)
    for lo in range(0, len(a), rows):
        block = a[lo : lo + rows]
        primitive = evaluate_primitives(state, block, buffer, method)
        terms = evaluate_conjunctions(state, primitive, buffer)
        mat = buffer.matrix[: len(block)]
        if buffer.binary is not None:
            binary = buffer.binary[: len(block)]
            binary[:, : len(state.kind)] = primitive[:-1].T
            binary[:, len(state.kind) :] = terms.T
            np.copyto(mat, binary)
        else:
            mat[:, : len(state.kind)] = primitive[:-1].T
            mat[:, len(state.kind) :] = terms.T
        output[lo : lo + rows] = state.intercept + mat @ state.coef
    return output
