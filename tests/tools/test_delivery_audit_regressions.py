"""Distribution/evidence regressions, without importing or claiming the ML engine."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('repository_check',ROOT/'tools/verify_repository.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)

@pytest.mark.parametrize('name',[
    'PRIVATE_CODEX/lab/pytest-cache/v/cache/nodeids','private_codex/CACHEDIR.TAG',
    'tests/__pycache__/test.pyc','.pytest_cache/README.md','results/log.txt',
    '.git/config','src/codadapt/hidden.pyc','../escape','/absolute','C:/absolute'])
def test_hashed_generated_material_is_still_rejected(name):
    with pytest.raises(ValueError):verifier.validate_public_path(name)

@pytest.mark.parametrize('name',['src/codadapt/_inference.py','tests/data/binary/DATA.npz','qualification/FINAL_MATRIX.json'])
def test_required_public_payload_is_allowed(name):
    verifier.validate_public_path(name)

def test_pure_wheel_with_two_native_modules_must_fail(tmp_path):
    # Regression: `(len(native)==1)==False` used to accept two extensions as pure.
    wheel=tmp_path/'codadapt-2.1.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel,'w') as z:
        z.writestr('codadapt/_native_kernel.a.pyd',b'not executed')
        z.writestr('codadapt/_native_kernel.b.pyd',b'not executed')
    result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/audit_native_wheel.py'),
        '--wheel',str(wheel),'--backend','pure','--output',str(tmp_path/'audit.json')],
        capture_output=True,text=True,timeout=15)
    assert result.returncode!=0
    assert 'Native/pure payload mismatch' in result.stderr
    assert not (tmp_path/'audit.json').exists()
