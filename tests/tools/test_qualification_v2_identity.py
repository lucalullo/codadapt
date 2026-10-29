"""Version2 receipts bind test/build inputs; synthetic receipts do not qualify platforms."""
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
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

@pytest.mark.parametrize('case',['valid','modified_inputs','missing_preflight','duplicate_stage','false_perf_pass'])
def test_v2_receipt(tmp_path,case):
    folder=tmp_path/'receipt';(folder/'probe').mkdir(parents=True);(folder/'dist').mkdir()
    (folder/'junit.xml').write_text('<testsuites><testsuite><testcase name="SYNTHETIC_ONLY"/></testsuite></testsuites>')
    (folder/'probe/RESULT.json').write_text(json.dumps(dict(status='PASS_FINITE_ENGINEERING_PROBE',native_batch2048_10pct_guard=False)))
    for name in ('fake.whl','fake.tar.gz'):(folder/'dist'/name).write_bytes(b'SYNTHETIC')
    steps=[dict(label=name,returncode=0) for name in ('create_build_env','build_dependencies','dependency_preflight','build',
        'create_consumer','install_consumer','dependency_check','engineering_probe','suite')]
    if case=='missing_preflight':steps=[row for row in steps if row['label']!='dependency_preflight']
    if case=='duplicate_stage':steps.append(steps[0])
    record=dict(schema=2,status='PASS_EXECUTED_PROFILE',backend='native',functional_qualification='PASS',
        performance_gate='PASS_FINITE' if case=='false_perf_pass' else 'HOLD',automatic_platform_promotion=False,
        system='TEST_ONLY',machine='TEST_ONLY',python='TEST_ONLY',steps=steps,
        source_SHA256=identity_module.source_identity(ROOT),
        qualification_inputs_SHA256=identity_module.qualification_inputs(ROOT),
        runner_SHA256=sha(ROOT/'tools/qualify_platform.py'),
        artifacts_SHA256={p.relative_to(folder).as_posix():sha(p) for p in (folder/'dist').iterdir()})
    if case=='modified_inputs':record['qualification_inputs_SHA256']['MANIFEST.in']='0'*64
    (folder/'RESULT.json').write_text(json.dumps(record))
    (folder/'RECEIPT_MANIFEST.json').write_text(json.dumps(dict(schema=2,files={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()})))
    outcome=subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/verify_qualification_receipt.py'),str(folder)],capture_output=True,text=True,timeout=15)
    if case=='valid':
        assert outcome.returncode==0,outcome.stderr
        assert json.loads(outcome.stdout)['automatic_platform_promotion'] is False
    else:assert outcome.returncode!=0
