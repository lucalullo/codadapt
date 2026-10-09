"""Native binary and shared-OVR multiclass classification."""

from time import perf_counter

import numpy as np
from sklearn.base import ClassifierMixin
from sklearn.utils.validation import check_is_fitted

from ._base import _BaseCodAdapt
from ._core import sigmoid
from ._multiclass import fit_heads, is_multiclass, prepare
from ._multiclass_artifact import Artifact


class CodAdaptClassifier(ClassifierMixin, _BaseCodAdapt):
    """Single-label classifier; probabilities follow the order in ``classes_``.

    Two positive-weight classes retain the native binary path. More classes use
    shared encoding and target-specific native OVR heads, with normalized sigmoid
    probabilities rather than a softmax link.
    """

    _task = "classification"

    def fit(self, X, y, sample_weight=None, eval_set=None):
        """Fit binary or multiclass targets with the same constructor parameters."""
        if not is_multiclass(y, sample_weight):
            return super().fit(X, y, sample_weight=sample_weight, eval_set=eval_set)
        tick = perf_counter()
        for key in list(vars(self)):
            if key.endswith("_"):
                delattr(self, key)
        data = prepare(self, X, y, sample_weight, eval_set)
        encoder, heads, preprocessing_s = fit_heads(self, data)
        self._ovr_artifact_ = Artifact.create(
            encoder,
            data.classes,
            heads,
            dict(random_state=self.random_state, categorical_features=self.categorical_features),
        )
        self._restore_aliases()
        self.estimated_memory_bytes_ = data.estimated_bytes
        self.timings_ = {"preprocessing": preprocessing_s, "fit_total": perf_counter() - tick}
        self._is_fitted_ = True
        if self.verbosity:
            print(
                f"CodAdapt multiclass fitted {self.n_classes_} unchanged native heads; fit={self.timings_['fit_total']:.3f}s"
            )
        return self

    def _restore_aliases(self):
        artifact = self._ovr_artifact_
        state = artifact.shared_state
        self.classes_, self.n_classes_ = state.classes, len(state.classes)
        self.n_features_in_ = state.encoder.n_features_in_
        self.encoder_ = self.shared_encoder_ = state.encoder
        self.encoders_ = state.encoder.level_views_
        if hasattr(state.encoder, "feature_names_in_"):
            self.feature_names_in_ = state.encoder.feature_names_in_
        self._heads_ = artifact.heads
        self.n_iter_ = max(len(h.levels) for h in artifact.heads)
        self.best_iteration_ = self.n_iter_
        self.lookup_count_per_sample_ = sum(
            len(level["main_tables"]) + len(level["tables"])
            for head in artifact.heads
            for level in head.levels
        )

    def decision_function(self, X):
        """Return binary scores (n,) or multiclass OVR scores (n, K)."""
        if hasattr(self, "_ovr_artifact_"):
            check_is_fitted(self)
            return self._ovr_artifact_.decision_function(X)
        return self._decision(X)

    def predict_proba(self, X):
        """Return class-ordered probabilities, shape (n_samples, n_classes)."""
        if hasattr(self, "_ovr_artifact_"):
            check_is_fitted(self)
            return self._ovr_artifact_.predict_proba(X)
        positive = sigmoid(self._decision(X))
        return np.column_stack((1.0 - positive, positive))

    def predict(self, X):
        """Return original labels; multiclass ties select the first class."""
        if hasattr(self, "_ovr_artifact_"):
            check_is_fitted(self)
            return self._ovr_artifact_.predict(X)
        score = self._decision(X)
        return self.classes_[(score > 0.0).astype(np.intp)]

    def __sklearn_tags__(self):
        tags = super().__sklearn_tags__()
        tags.classifier_tags.multi_class = True
        return tags

    def _more_tags(self):
        return {**super()._more_tags(), "binary_only": False}

    def __getstate__(self):
        state = super().__getstate__().copy()
        if "_ovr_artifact_" in state:
            for key in (
                "classes_",
                "encoder_",
                "shared_encoder_",
                "encoders_",
                "feature_names_in_",
                "_heads_",
            ):
                state.pop(key, None)
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        if "_ovr_artifact_" in state:
            self._restore_aliases()
