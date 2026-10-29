"""Safe automatic use only in the qualified profile; critical errors stay visible."""
from types import SimpleNamespace
import importlib.util
import platform
import sys
import pytest
import codadapt._inference as dispatch



def eligible_test_double(monkeypatch):
    # Test the enabled branch on every host, without enabling that profile in production.
    monkeypatch.setattr(dispatch,"sys",SimpleNamespace(platform="win32",implementation=SimpleNamespace(name="cpython"),version_info=(3,12,10)))
    monkeypatch.setattr(dispatch,"platform",SimpleNamespace(machine=lambda:"AMD64"))
    pins={"numpy":"2.5.4","pandas":"3.1.0","scipy":"1.18.1","scikit-learn":"1.9.1"}
    monkeypatch.setattr(dispatch,"version",lambda name:pins[name])

@pytest.fixture(autouse=True)
def clear_auto():
    dispatch._native_for_auto.cache_clear()
    yield
    dispatch._native_for_auto.cache_clear()


def test_qualified_installed_profile_uses_native():
    with dispatch.inference_backend("auto"):
        pins={"numpy":"2.5.4","pandas":"3.1.0","scipy":"1.18.1","scikit-learn":"1.9.1"}
        eligible=(sys.platform=="win32" and sys.implementation.name=="cpython"
            and sys.version_info[:3]==(3,12,10) and platform.machine().lower() in {"amd64","x86_64"}
            and all(dispatch.version(k)==v for k,v in pins.items())
            and importlib.util.find_spec("codadapt._native_kernel") is not None)
        assert dispatch._active_backend() == ("native" if eligible else "python")


def test_other_profile_prefers_python(monkeypatch):
    monkeypatch.setattr(dispatch,"version",lambda name:"unqualified")
    with dispatch.inference_backend("auto"):
        assert dispatch._active_backend()=="python"


def test_missing_module_falls_back_only_for_exact_missing_name(monkeypatch):
    eligible_test_double(monkeypatch)
    original = dispatch.import_module
    def missing(name):
        if name == "codadapt._native_kernel":
            raise ModuleNotFoundError("absent",name=name)
        return original(name)
    monkeypatch.setattr(dispatch,"import_module",missing)
    assert dispatch._native_for_auto() is None


@pytest.mark.parametrize("error",[ImportError("DLL App Control blocked"),ModuleNotFoundError("transitive",name="dependency")])
def test_critical_import_not_hidden(monkeypatch,error):
    eligible_test_double(monkeypatch)
    original = dispatch.import_module
    def fail(name):
        if name == "codadapt._native_kernel":
            raise error
        return original(name)
    monkeypatch.setattr(dispatch,"import_module",fail)
    with pytest.raises(type(error),match=str(error)):
        dispatch._native_for_auto()


def test_wrong_contract_is_not_fallback(monkeypatch):
    eligible_test_double(monkeypatch)
    original = dispatch.import_module
    monkeypatch.setattr(dispatch,"import_module",lambda name:SimpleNamespace(contract_version=-1) if name == "codadapt._native_kernel" else original(name))
    with pytest.raises(RuntimeError,match="contract"):
        dispatch._native_for_auto()


def test_python_override_and_context_restored():
    with dispatch.inference_backend("python"):
        assert dispatch._active_backend()=="python"
    assert dispatch._BACKEND.get()=="auto"


def test_runtime_version_matches_installed_distribution():
    from importlib.metadata import version
    for name in ("numpy", "pandas", "scipy", "scikit-learn"):
        assert dispatch.version(name) == version(name)
