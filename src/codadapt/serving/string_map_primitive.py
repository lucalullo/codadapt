"""Private pure NumPy mapping primitive; no trainer or persistence dependency."""

import numpy as np


def map_nonrare_strings(values, missing, schema, original):
    n = len(values)
    if not 0 < n <= 32 or schema["n_rare_categories"]:
        return original(values, missing, schema)
    vocabulary = schema["vocabulary"]
    # Bound validation work by the native default category limit. Larger user
    # vocabularies keep their original path; no thresholds are fitted/scanned.
    if type(vocabulary) is not dict or len(vocabulary) > 128:
        return original(values, missing, schema)
    if any(
        type(k) is not str or type(v) is not int or not 0 <= v <= 65535
        for k, v in vocabulary.items()
    ):
        return original(values, missing, schema)
    if type(missing) is not np.ndarray or missing.shape != (n,) or missing.dtype != bool:
        return original(values, missing, schema)
    raw = values.to_numpy(copy=False)
    if any(not missing[i] and type(key) is not str for i, key in enumerate(raw)):
        return original(values, missing, schema)
    unknown, empty = schema["unknown_bucket"], schema["missing_bucket"]
    if (
        type(unknown) is not int
        or type(empty) is not int
        or not 0 <= unknown <= 65535
        or not 0 <= empty <= 65535
    ):
        return original(values, missing, schema)
    result = np.empty(n, dtype=np.uint16)
    for i, key in enumerate(raw):
        result[i] = empty if missing[i] else vocabulary.get(key, unknown)
    return result
