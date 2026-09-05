"""CodAdapt: experimental adaptive integer addressing for tabular data."""

from ._version import __version__
from .classifier import CodAdaptClassifier
from .regressor import CodAdaptRegressor

CodAdapt = CodAdaptClassifier
__all__ = ["CodAdapt", "CodAdaptClassifier", "CodAdaptRegressor", "__version__"]
