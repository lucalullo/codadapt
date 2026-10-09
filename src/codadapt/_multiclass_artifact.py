"""Lossless shared native multiclass prediction and persistence."""

import numpy as np

from ._core import sigmoid
from ._multiclass_packing import pack, unpack
from ._training import predict_coded_memory_buckets


class CompactHead:
    __slots__ = ("shared_state", "intercept", "levels")

    def __init__(self, shared_state, intercept, levels):
        self.shared_state, self.intercept, self.levels = shared_state, intercept, levels

    @property
    def table_size(self):
        return self.shared_state.table_size

    def scores(self, z):
        s = self.shared_state
        return predict_coded_memory_buckets(
            self.levels, s.encoder.level_views_, z, self.intercept, s.table_size
        )


def probabilities(logits):
    p = sigmoid(logits)
    total = p.sum(axis=1, keepdims=True)
    if not np.isfinite(p).all() or np.any(total <= 0):
        raise FloatingPointError("Invalid OVR probability mass; no silent uniform repair")
    return p / total


class SharedState:
    __slots__ = ("encoder", "classes", "table_size", "params")

    def __init__(self, encoder, classes, table_size, params):
        self.encoder, self.classes, self.table_size, self.params = (
            encoder,
            classes,
            table_size,
            params,
        )


class Artifact:
    __slots__ = ("shared_state", "heads")

    @classmethod
    def create(cls, encoder, classes, heads, params):
        result = cls()
        result.__setstate__(pack(encoder, classes, heads, params))
        return result

    def decision_function(self, x):
        z = self.shared_state.encoder.transform_levels(x)
        return np.column_stack([h.scores(z) for h in self.heads])

    def predict_proba(self, x):
        return probabilities(self.decision_function(x))

    def predict(self, x):
        return self.shared_state.classes[self.predict_proba(x).argmax(1)]

    def __getstate__(self):
        s = self.shared_state
        return pack(s.encoder, s.classes, self.heads, s.params)

    def __setstate__(self, wire):
        encoder, classes, records, table_size, params = unpack(wire)
        self.shared_state = SharedState(encoder, classes, table_size, params)
        self.heads = tuple(
            CompactHead(self.shared_state, intercept, levels) for intercept, levels in records
        )
