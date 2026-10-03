"""Minimal teacher-free branch-dependent inference state."""

from ._safe_blend_runtime import (
    BasePredictionState,
    PackedCompiledState,
    SharedInputPreparation,
    compiler_predict,
)

ALPHA = 0.27388247139831357


class SafeBlendArtifact:
    def __init__(self, base, compiler, encoding, branch):
        if branch not in ("BASE", "BLEND"):
            raise ValueError("Unknown frozen safety branch.")
        self.branch = branch
        self.shared_preprocessing = SharedInputPreparation(encoding)
        self.base = BasePredictionState(base)
        if branch == "BLEND":
            self.compiled = PackedCompiledState(compiler)

    def predict(self, x):
        a = self.shared_preprocessing.transform(x)
        b = self.base.predict(a)
        if self.branch == "BASE":
            return b
        c = compiler_predict(self.compiled, a)
        c -= b
        c *= ALPHA
        b += c
        return b
