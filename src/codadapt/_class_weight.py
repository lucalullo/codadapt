"""Internal class factors computed from effective positive-weight TRAIN rows."""

import numbers

import numpy as np


def validate_class_weight(value):
    if value is None or (isinstance(value, str) and value == "balanced"):
        return
    if isinstance(value, dict):
        for factor in value.values():
            invalid_type = (
                isinstance(factor, (bool, np.bool_))
                or not isinstance(factor, numbers.Real)
            )
            try:
                valid = not invalid_type and np.isfinite(float(factor)) and factor > 0
            except (OverflowError, TypeError, ValueError):
                valid = False
            if not valid:
                raise ValueError("class_weight dictionary factors must be finite and positive.")
        return
    raise ValueError("class_weight must be None, 'balanced', or a dictionary of positive factors.")


def training_class_weights(y, weight, class_weight):
    """Return a new vector; callers have already removed zero-weight rows/split VALID.

    Balanced masses use the original multiclass labels, never individual OVR labels.
    Division precedes multiplication to avoid overflow of an explicit inverse factor.
    """
    if class_weight is None:
        return weight
    classes, inverse = np.unique(y, return_inverse=True)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            if isinstance(class_weight, str):
                mass = np.bincount(inverse, weights=weight, minlength=len(classes))
                target_mass = float(weight.sum()) / len(classes)
                result = (weight / mass[inverse]) * target_mass
            else:
                if any(label not in classes for label in class_weight):
                    raise ValueError("class_weight contains a class absent from effective TRAIN.")
                factors = np.array(
                    [class_weight.get(label, 1.0) for label in classes], dtype=np.float64
                )
                result = weight * factors[inverse]
            total = result.sum()
    except FloatingPointError as error:
        raise ValueError("class_weight cannot be represented safely; rescale sample_weight.") from error
    if not np.isfinite(result).all() or (result <= 0).any() or not np.isfinite(total):
        raise ValueError("class_weight must produce finite positive weights; rescale sample_weight.")
    return result
