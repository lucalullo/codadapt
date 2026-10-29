"""Opt-in fitted-only model export and serving.

Serving models provide prediction methods,not the estimator training API.
Artifacts use pickle and require explicit authorization as trusted input.
"""

__all__ = ["export_model", "load_model"]


def export_model(model, path):
    """Export a fitted native estimator without fitting or rebalancing it.

    Return the hash/size receipt for the exact publication made by this call.
    """
    from .exporter import export

    return export(model, path)


def load_model(path, *, trusted=False, expected_sha256=None, max_bytes=None):
    """Load an explicitly trusted image after format/profile/integrity checks.

    expected_sha256 binds an externally trusted publication receipt. It is not
    an authenticity signature and does not make hostile pickle input safe.
    """
    if trusted is not True:
        raise ValueError("Explicit trusted=True is required for authorized pickle artifacts")
    from . import numeric_frame_runtime as runtime
    from . import validated_native_format as framing

    parts, metadata = framing.read_validated(
        path, expected_sha256=expected_sha256, max_bytes=max_bytes
    )
    result = runtime.ServingModel(framing.construct(parts))
    result.metadata = metadata
    return result
