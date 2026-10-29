"""CodAdapt native estimators; optional fitted-model serving imports on demand."""

from ._version import __version__

__all__ = ["CodAdapt", "CodAdaptClassifier", "CodAdaptRegressor", "__version__"]


def __getattr__(name):
    if name in {"CodAdapt", "CodAdaptClassifier"}:
        from .classifier import CodAdaptClassifier

        globals().update(CodAdapt=CodAdaptClassifier, CodAdaptClassifier=CodAdaptClassifier)
    elif name == "CodAdaptRegressor":
        from .regressor import CodAdaptRegressor

        globals()[name] = CodAdaptRegressor
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return globals()[name]


def __dir__():
    return sorted(set(globals()) | set(__all__))
