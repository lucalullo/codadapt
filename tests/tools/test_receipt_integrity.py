"""Synthetic evidence tests; these fixtures never certify a runtime platform."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
identity_spec=importlib.util.spec_from_file_location('codadapt_qualification_identity',ROOT/'tools/qualification_identity.py')
identity_module=importlib.util.module_from_spec(identity_spec);identity_spec.loader.exec_module(identity_module)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def fixture(tmp_path):
    folder=tmp_path/'receipt';folder.mkdir()
    (folder/'probe').mkdir();(folder/'dist').mkdir()
    (folder/'probe/RESULT.json').write_text(json.dumps({'status':'PASS_FINITE_ENGINEERING_PROBE'}))
    (folder/'junit.xml').write_text('<testsuites><testsuite><testcase name="synthetic_fixture"/></testsuite></testsuites>')
    for name in ('fixture.whl','fixture.tar.gz'):(folder/'dist'/name).write_bytes(b'SYNTHETIC TEST ONLY')
    record=dict(status='PASS_EXECUTED_PROFILE',system='TEST_FIXTURE',machine='TEST_FIXTURE',python='TEST_FIXTURE',
        source_SHA256=identity_module.source_identity(ROOT),
        runner_SHA256=sha(ROOT/'tools/qualify_platform.py'),
        artifacts_SHA256={p.relative_to(folder).as_posix():sha(p) for p in (folder/'dist').iterdir()},
        steps=[dict(label=name,returncode=0) for name in ('create_build_env','build_dependencies','build',
            'create_consumer','install_consumer','dependency_check','engineering_probe','suite')])
    return folder,record

def seal(folder,record):
    (folder/'RESULT.json').write_text(json.dumps(record))
    manifest=dict(schema=1,files={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*')
        if p.is_file() and p.name!='RECEIPT_MANIFEST.json'})
    (folder/'RECEIPT_MANIFEST.json').write_text(json.dumps(manifest))
    return manifest

def invoke(folder):
    return subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/verify_qualification_receipt.py'),str(folder)],
        capture_output=True,text=True,timeout=20)

@pytest.mark.parametrize('case',['valid','windows_paths','modified_log','traversal','absolute_windows',
    'missing_source','missing_runner','failed_suite','missing_probe','missing_step','artifact_unbound','duplicate_identity'])
def test_receipt_contract(tmp_path,case):
    folder,record=fixture(tmp_path)
    if case=='missing_source':record['source_SHA256'].pop(next(iter(record['source_SHA256'])))
    if case=='missing_runner':record['runner_SHA256']='0'*64
    if case=='missing_step':record['steps'].pop()
    if case=='artifact_unbound':record['artifacts_SHA256']['dist/unbound.whl']='0'*64
    if case=='failed_suite':(folder/'junit.xml').write_text('<testsuites><testsuite><testcase><failure/></testcase></testsuite></testsuites>')
    if case=='windows_paths':record['source_SHA256']={k.replace('/','\\'):v for k,v in record['source_SHA256'].items()}
    manifest=seal(folder,record)
    if case=='modified_log':(folder/'junit.xml').write_text('tampered')
    if case=='traversal':manifest['files']['../outside']='0'*64
    if case=='absolute_windows':manifest['files']['Z:/outside']='0'*64
    if case=='missing_probe':manifest['files'].pop('probe/RESULT.json')
    if case=='duplicate_identity':manifest['files']['probe\\RESULT.json']=manifest['files']['probe/RESULT.json']
    if case=='windows_paths':manifest['files']={k.replace('/','\\'):v for k,v in manifest['files'].items()}
    (folder/'RECEIPT_MANIFEST.json').write_text(json.dumps(manifest))
    outcome=invoke(folder)
    if case in ('valid','windows_paths'):
        assert outcome.returncode==0,outcome.stderr
        result=json.loads(outcome.stdout)
        assert result['automatic_platform_promotion'] is False
        assert result['external_authenticity_attested'] is False
    else:assert outcome.returncode!=0
