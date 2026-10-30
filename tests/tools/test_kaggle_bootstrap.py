"""Execute notebook bootstrap only; never simulate a Kaggle kernel or ML test."""
from pathlib import Path,PurePosixPath
import hashlib,json,stat,zipfile
import pytest
ROOT=Path(__file__).resolve().parents[2]
@pytest.mark.parametrize('case',['valid','wrong_package_hash','wrong_member_hash'])
def test_actual_notebook_bootstrap(tmp_path,case):
    archive=tmp_path/'package.zip';payload=b'NOT EXECUTED'
    manifest=dict(files={'repository/payload.txt':dict(SHA256='0'*64 if case=='wrong_member_hash' else hashlib.sha256(payload).hexdigest())})
    with zipfile.ZipFile(archive,'w') as z:z.writestr('repository/payload.txt',payload);z.writestr('PACKAGE_MANIFEST.json',json.dumps(manifest))
    notebook=json.loads((ROOT/'examples/CODADAPT_210_KAGGLE_NATIVE_TEST.ipynb').read_text())
    scope=dict(Path=Path,PurePosixPath=PurePosixPath,hashlib=hashlib,json=json,stat=stat,zipfile=zipfile,PACKAGE=archive,
        WORK=tmp_path/'work',EXPECTED_PACKAGE_SHA256='0'*64 if case=='wrong_package_hash' else hashlib.sha256(archive.read_bytes()).hexdigest())
    code=''.join(notebook['cells'][2]['source'])
    if case=='valid':exec(compile(code,'bootstrap','exec'),scope);assert scope['BOOTSTRAP_OK'] is True
    else:
        with pytest.raises(RuntimeError):exec(compile(code,'bootstrap','exec'),scope)
        with zipfile.ZipFile(tmp_path/'work/CODADAPT_210_EXTERNAL_RESULTS.zip') as z:
            status=json.loads(z.read('BOOTSTRAP_STATUS.json'));assert status['source_executed'] is False and status['native_calls']==0
