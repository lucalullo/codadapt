"""PRIVATE 01+02 serving; immutable metadata replacement is compile-time only."""

import copy

import pandas as pd

from . import portable_native_runtime as native
from . import validated_native_format as framing
from .string_map_primitive import map_nonrare_strings


def mapping(values, missing, schema):
    return map_nonrare_strings(values, missing, schema, native.BucketEncoder._transform_categorical)


class EncoderView(native.BucketEncoder):
    _transform_categorical = staticmethod(mapping)


class ServingModel:
    """Fitted-only trusted image, with the unchanged Component02 local view."""

    def __init__(self, image):
        self.image = image

    def _view(self, x):
        if (
            type(x) is not pd.DataFrame
            or not 0 < len(x) <= 32
            or not len(self.image.encoder.categorical_features_)
        ):
            return self.image
        encoder = object.__new__(EncoderView)
        encoder.__dict__.update(vars(self.image.encoder))
        image = copy.copy(self.image)
        image.encoder = encoder
        return image

    def decision_function(self, x):
        return self._view(x).decision_function(x)

    def predict_proba(self, x):
        return self._view(x).predict_proba(x)

    def predict(self, x):
        return self._view(x).predict(x)


def load(path):
    return ServingModel(framing.load(path))
