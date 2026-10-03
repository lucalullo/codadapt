"""Opt-in experimental exports; the default CodAdapt estimators are unchanged."""

from ._compiler import CompilationError, compile_ebm
from ._model import CompiledEBMClassifier, CompiledEBMRegressor

__all__ = [
    "CompilationError",
    "CompiledEBMClassifier",
    "CompiledEBMRegressor",
    "SafeBlendRegressor",
    "compile_ebm",
]


def __getattr__(name):
    if name == "SafeBlendRegressor":
        from ._safe_blend import SafeBlendRegressor

        return SafeBlendRegressor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
