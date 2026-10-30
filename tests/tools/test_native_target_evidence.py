"""Synthetic receipt rejection controls; these do not qualify any platform."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,zipfile
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('native_receipt',ROOT/'tools/verify_native_evidence.py');tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
@pytest.mark.parametrize('case',['valid','no_calls','wrong_system','tamper','traversal','failed_stage','missing_task','wrong_kernel','wrong_wheel','missing_wheel_audit','all_skipped'])
def test_receipt_controls(tmp_path,case):
    (tmp_path/'probe').mkdir();(tmp_path/'dist').mkdir()
    source={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for d in ('src/codadapt','native') for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    wheel=tmp_path/'dist/synthetic-only.whl';wheel.write_bytes(b'NOT A REAL WHEEL; RECEIPT CONTROL ONLY')
    digest=hashlib.sha256(wheel.read_bytes()).hexdigest()
    record=dict(status='PASS_EXECUTED_TARGET_CORE',backend='native',system='Windows' if case=='wrong_system' else 'Linux',context='ci',steps=[dict(label=n,returncode=1 if case=='failed_stage' and n=='smoke' else 0) for n in ('create_consumer','install','pip_check','wheel_audit','smoke','native_boundary_suite')],source_SHA256=source,artifacts={wheel.name:digest})
    probe=dict(status='PASS_ACTUAL_INSTALLED_BACKEND',native_calls=0 if case=='no_calls' else 1,backend='native',extension_name='_native_kernel.so',extension_SHA256='1'*64,cases=[dict(task=t,exact_arrays=1) for t in ('binary','multiclass','regression')])
    audit=dict(status='PASS_ACTUAL_HOST_WHEEL_TAGS_AND_PAYLOAD',system='Linux',native_binary_SHA256='0'*64 if case=='wrong_kernel' else '1'*64,wheel_SHA256='0'*64 if case=='wrong_wheel' else digest)
    if case!='missing_wheel_audit':(tmp_path/'WHEEL_AUDIT.json').write_text(json.dumps(audit))
    if case=='missing_task':probe['cases'].pop()
    (tmp_path/'RESULT.json').write_text(json.dumps(record));(tmp_path/'probe/RESULT.json').write_text(json.dumps(probe));(tmp_path/'junit.xml').write_text('<testsuites><testsuite><testcase name="SYNTHETIC_ONLY"/></testsuite></testsuites>')
    if case=='all_skipped':(tmp_path/'junit.xml').write_text('<testsuites><testsuite><testcase><skipped/></testcase></testsuite></testsuites>')
    manifest={p.relative_to(tmp_path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob('*') if p.is_file()}
    if case=='traversal':manifest['../escape']='0'*64
    (tmp_path/'RECEIPT_MANIFEST.json').write_text(json.dumps(dict(files=manifest)))
    if case=='tamper':(tmp_path/'junit.xml').write_text('changed')
    if case=='valid':assert tool.verify(tmp_path,'Linux','ci')['automatic_promotion'] is False
    else:
        with pytest.raises(ValueError):tool.verify(tmp_path,'Linux','ci')
@pytest.mark.parametrize('case',['pure','bad_hash'])
def test_prebuilt_native_wheel_rejected_before_install(tmp_path,case):
    wheel=tmp_path/'pure.whl'
    with zipfile.ZipFile(wheel,'w') as z:z.writestr('codadapt/__init__.py','# no extension')
    digest=hashlib.sha256(wheel.read_bytes()).hexdigest() if case=='pure' else '0'*64
    out=tmp_path/'consumer'
    r=subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/qualify_native_target.py'),'--output',str(out),'--runtime-requirements',str(ROOT/'requirements/portable-runtime.txt'),'--native-wheel',str(wheel),'--expected-wheel-sha256',digest,'--wheelhouse',str(tmp_path)],capture_output=True,timeout=15)
    assert r.returncode!=0 and not out.exists()
