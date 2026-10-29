"""E4 prototype: identical encoded-memory reads with bounded temporary arrays."""
import numpy as np
from codadapt.preprocessing import BucketEncoder

_METHODS = {name: getattr(BucketEncoder, name) for name in (
    "_validate_input", "transform", "transform_levels", "_transform_numeric", "_numeric_values")}
THRESHOLD = 131072
BLOCK_ROWS = 16384


def eligible(encoder, X):
    return (type(X) is np.ndarray and X.ndim == 2 and len(X) >= THRESHOLD
        and type(encoder) is BucketEncoder and not encoder._fit_dataframe_
        and all(s["kind"] == "numeric" for s in encoder.schemas_)
        and not any(name in vars(encoder) for name in _METHODS)
        and all(getattr(BucketEncoder,name) is fn for name,fn in _METHODS.items()))


def decision(encoder, X, reader):
    if not eligible(encoder, X):
        return reader(encoder.transform_levels(X))
    # Preserve full-input resource/schema checks and first-infinity column order.
    X = encoder._validate_input(X)
    if X.shape[1] != encoder.n_features_in_:
        return reader(encoder.transform_levels(X))
    for j in range(X.shape[1]):
        values = np.array(X[:,j],dtype=np.float64,copy=True)
        if np.isinf(values).any():
            raise ValueError(f"Input contains infinity in feature {j!r}; infinities are not supported.")
    del values
    first = reader(encoder.transform_levels(X[:BLOCK_ROWS]))
    output = np.empty((len(X),)+first.shape[1:],dtype=first.dtype)
    output[:len(first)] = first
    for start in range(BLOCK_ROWS,len(X),BLOCK_ROWS):
        stop = min(start+BLOCK_ROWS,len(X))
        output[start:stop] = reader(encoder.transform_levels(X[start:stop]))
    return output
