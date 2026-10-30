"""Execute setup configuration, not a compiler: no Linux qualification implied."""
from pathlib import Path
import runpy,sys
import pytest
import setuptools
ROOT=Path(__file__).resolve().parents[2]
@pytest.mark.parametrize('platform,flag,expected',[
    ('linux',None,True),('linux','0',False),('linux','1',True),
    ('win32',None,False),('win32','1',True),('win32','0',False),
    ('darwin',None,False),('darwin','1',True),('darwin','0',False)])
def test_distribution_configuration(monkeypatch,platform,flag,expected):
    # Import helper before platform substitution to avoid emulating CPython ABI.
    import pybind11.setup_helpers
    captured={};monkeypatch.setattr(setuptools,'setup',lambda **kw:captured.update(kw))
    monkeypatch.setattr(sys,'platform',platform)
    if flag is None:monkeypatch.delenv('CODADAPT_BUILD_NATIVE',raising=False)
    else:monkeypatch.setenv('CODADAPT_BUILD_NATIVE',flag)
    runpy.run_path(str(ROOT/'setup.py'))
    exts=captured['ext_modules'];assert bool(exts) is expected
    if expected:
        assert exts[0].name=='codadapt._native_kernel'
        assert exts[0].sources==['native/memory_read.cpp']
        assert ('/fp:strict' if platform=='win32' else '-ffp-contract=off') in exts[0].extra_compile_args
        assert captured['cmdclass']['build_ext'] is pybind11.setup_helpers.build_ext
@pytest.mark.parametrize('flag',['auto','true','2',''])
def test_invalid_flag_fails_before_build(monkeypatch,flag):
    monkeypatch.setenv('CODADAPT_BUILD_NATIVE',flag)
    with pytest.raises(ValueError,match='must be 0 or 1'):runpy.run_path(str(ROOT/'setup.py'))
