"""Single-target regression with adaptive lookup tables."""

from sklearn.base import RegressorMixin

from ._base import _BaseCodAdapt


class CodAdaptRegressor(RegressorMixin, _BaseCodAdapt):
    """Single-target regressor, including integer-valued regression targets."""

    _task = "regression"

    def predict(self, X):
        """Return real-valued target estimates."""
        return self._decision(X)
