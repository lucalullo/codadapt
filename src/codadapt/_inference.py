"""Private inference boundary: no training dispatch, no serialized native state."""
from contextlib import contextmanager
from contextvars import ContextVar
from importlib import import_module
from functools import lru_cache
import platform
import sys

from ._training import predict_coded_memory_buckets as python_predict

_BACKEND = ContextVar("codadapt_private_inference_backend", default="auto")


def version(distribution):
    # These dependencies are already imported by the estimator. Avoid scanning
    # dist-info directories on the first prediction merely to select a backend.
    module = "sklearn" if distribution == "scikit-learn" else distribution
    return import_module(module).__version__


@contextmanager
def inference_backend(name):
    """Private experiment selector; does not alter estimator parameters or state."""
    if name not in {"auto", "python", "native"}:
        raise ValueError("Expected auto, python or native backend")
    if name == "native":
        _load_native()  # Fail before a run, never quietly label Python as native.
    token = _BACKEND.set(name)
    try:
        yield
    finally:
        _BACKEND.reset(token)


def _load_native():
    try:
        module = import_module("codadapt._native_kernel")
    except ModuleNotFoundError as error:
        if error.name != "codadapt._native_kernel":
            raise
        raise RuntimeError("CodAdapt native extension is not built in this laboratory") from error
    if module.contract_version != 1:
        raise RuntimeError("Unsupported CodAdapt native kernel contract")
    return module


@lru_cache(maxsize=1)
def _native_for_auto():
    """Only the tested local profile opts in automatically; absence is expected."""
    if not (sys.platform == "win32" and sys.implementation.name == "cpython"
            and sys.version_info[:3] == (3, 12, 10)
            and platform.machine().lower() in {"amd64", "x86_64"}):
        return None
    pins = {"numpy": "2.5.4", "pandas": "3.1.0", "scipy": "1.18.1", "scikit-learn": "1.9.1"}
    if any(version(name) != required for name, required in pins.items()):
        return None
    try:
        module = import_module("codadapt._native_kernel")
    except ModuleNotFoundError as error:
        if error.name == "codadapt._native_kernel":
            return None
        raise
    # DLL/App Control/ABI errors are not caught or turned into fallback.
    if module.contract_version != 1:
        raise RuntimeError("Unsupported CodAdapt native kernel contract")
    return module


def _active_backend():
    selected = _BACKEND.get()
    if selected == "auto":
        return "native" if _native_for_auto() is not None else "python"
    return selected


def predict_coded_memory_buckets(levels, encoders, z_levels, intercept, table_size):
    if _active_backend() == "python":
        return python_predict(levels, encoders, z_levels, intercept, table_size)
    return _load_native().predict_head(levels, [e.support_ for e in encoders],
                                      z_levels, intercept, table_size)
