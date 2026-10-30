"""Actual archive checks and failed-child collection; not platform qualification."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,zipfile
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'tools/external_delivery.py');delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
@pytest.mark.parametrize('case',['valid','hash','traversal','absolute','backslash','duplicate','symlink'])
def test_archive_preflight(tmp_path,case):
    archive=tmp_path/'input.zip'
    with zipfile.ZipFile(archive,'w') as z:
        name={'traversal':'../bad','absolute':'/bad','backslash':'repo\\bad'}.get(case,'repository/good.py')
        if case=='symlink':
            info=zipfile.ZipInfo(name);info.external_attr=(0o120777<<16);z.writestr(info,'/outside')
        else:z.writestr(name,'VALUE=1')
        if case=='duplicate':z.writestr('REPOSITORY/GOOD.py','case alias')
    if case=='backslash':
        # ZipInfo normalizes host path separators on Windows. Patch both raw
        # filename headers to test an archive actually containing a backslash.
        archive.write_bytes(archive.read_bytes().replace(b'repo/bad',b'repo\\bad'))
    digest='0'*64 if case=='hash' else hashlib.sha256(archive.read_bytes()).hexdigest();out=tmp_path/'unpacked'
    if case=='valid':assert (delivery.safe_extract(archive,out,digest)/'repository/good.py').is_file()
    else:
        with pytest.raises(ValueError):delivery.safe_extract(archive,out,digest)
        assert not out.exists()
def test_failed_process_results_are_returned(tmp_path):
    # A real local child fails, and its failure remains in the returned archive.
    log=tmp_path/'stage.stderr'
    with log.open('wb') as stderr:r=subprocess.run([sys.executable,'-I','-B','-c','raise RuntimeError("CONTROLLED_FAILURE")'],stderr=stderr,timeout=10)
    assert r.returncode!=0
    (tmp_path/'consumer').mkdir();(tmp_path/'consumer/private-cache').write_text('excluded runtime')
    archive=delivery.collect_results(tmp_path,dict(status='HOLD_EXECUTION_FAILED_OR_BLOCKED',returncode=r.returncode))
    with zipfile.ZipFile(archive) as z:
        assert 'CONTROLLED_FAILURE' in z.read('stage.stderr').decode()
        assert json.loads(z.read('FINAL_STATUS.json'))['status'].startswith('HOLD')
        assert not any(n.startswith('consumer/') for n in z.namelist())
def test_external_preflight_failure_still_produces_results(tmp_path):
    out=tmp_path/'run'
    r=subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/run_external.py'),'--context','local','--expected-python','0.0.0','--output',str(out),'--wheelhouse',str(tmp_path)],capture_output=True,timeout=15)
    assert r.returncode==1
    with zipfile.ZipFile(out/'CODADAPT_210_EXTERNAL_RESULTS.zip') as z:
        state=json.loads(z.read('FINAL_STATUS.json'))
        assert state['status']=='HOLD_EXECUTION_FAILED_OR_BLOCKED'
        assert state['steps']==[]
        assert 'Actual Python differs' in state['error']
