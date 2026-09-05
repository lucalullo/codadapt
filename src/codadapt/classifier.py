"""Binary classification with adaptive lookup tables."""

import numpy as np
from sklearn.base import ClassifierMixin

from ._base import _BaseCodAdapt
from ._core import sigmoid


class CodAdaptClassifier(ClassifierMixin, _BaseCodAdapt):
    """Binary classifier; probabilities follow the order in ``classes_``."""

    _task = "classification"

    def decision_function(self, X):
        """Return uncalibrated binary decision scores."""
        return self._decision(X)

    def predict_proba(self, X):
        """Return probabilities for the two original class labels."""
        positive = sigmoid(self._decision(X))
        return np.column_stack((1.0 - positive, positive))

    def predict(self, X):
        """Return original labels, using a probability threshold of 0.5."""
        score = self._decision(X)
        return self.classes_[(score > 0.0).astype(np.intp)]

    def __sklearn_tags__(self):
        tags = super().__sklearn_tags__()
        tags.classifier_tags.multi_class = False
        return tags

    def _more_tags(self):
        return {**super()._more_tags(), "binary_only": True}
