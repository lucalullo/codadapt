"""Read-only evidence consistency check. Never authenticate or promote a host."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def verify(folder,expected_system,expected_context):
    folder=Path(folder).resolve();manifest=json.loads((folder/'RECEIPT_MANIFEST.json').read_text())
    for name,digest in manifest['files'].items():
        parts=name.split('/')
        if ':' in name or '\\' in name or PurePosixPath(name).is_absolute() or any(p in ('','.','..') for p in parts):raise ValueError('Unsafe evidence path')
        p=folder/name
        if p.is_symlink() or not p.resolve().is_relative_to(folder) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Evidence integrity mismatch')
    for name in ('RESULT.json','probe/RESULT.json','junit.xml','WHEEL_AUDIT.json'):
        if name not in manifest['files']:raise ValueError('Unbound required evidence')
    record=json.loads((folder/'RESULT.json').read_text());probe=json.loads((folder/'probe/RESULT.json').read_text())
    if record['status']!='PASS_EXECUTED_TARGET_CORE' or record['backend']!='native' or record['system']!=expected_system or record['context']!=expected_context:raise ValueError('Wrong qualification status or actual target')
    if any(row['returncode'] for row in record['steps']):raise ValueError('Failed stage')
    if not {'create_consumer','install','pip_check','wheel_audit','smoke','native_boundary_suite'}.issubset({r['label'] for r in record['steps']}):raise ValueError('Missing executed stage')
    if probe['status']!='PASS_ACTUAL_INSTALLED_BACKEND' or probe['native_calls']<=0 or probe['backend']!='native':raise ValueError('No executed native backend')
    if not probe['extension_name'].endswith('.pyd' if expected_system=='Windows' else '.so'):raise ValueError('Wrong extension type')
    audit=json.loads((folder/'WHEEL_AUDIT.json').read_text())
    if (audit['status']!='PASS_ACTUAL_HOST_WHEEL_TAGS_AND_PAYLOAD'
            or audit['system']!=expected_system
            or audit.get('native_binary_SHA256')!=probe.get('extension_SHA256')
            or not audit.get('native_binary_SHA256')):
        raise ValueError('Installed kernel differs from audited wheel')
    wheels=[(name,digest) for name,digest in record['artifacts'].items() if name.endswith('.whl')]
    if len(wheels)!=1 or wheels[0][1]!=audit.get('wheel_SHA256'):
        raise ValueError('Wheel artifact differs from audit')
    if {r['task'] for r in probe['cases']}!={'binary','multiclass','regression'} or any(r['exact_arrays']<=0 for r in probe['cases']):raise ValueError('Incomplete equivalence workload')
    cases=list(ET.parse(folder/'junit.xml').iter('testcase'))
    if not cases or any(c.find('error') is not None or c.find('failure') is not None for c in cases) or all(c.find('skipped') is not None for c in cases):raise ValueError('Failed or empty suite')
    actual={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for d in ('src/codadapt','native') for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if record['source_SHA256']!=actual:raise ValueError('Different source')
    for name,digest in record['artifacts'].items():
        if manifest['files'].get('dist/'+name)!=digest:raise ValueError('Unbound artifact')
    return dict(integrity='PASS',target_system=expected_system,target_context=expected_context,native_calls=probe['native_calls'],suite=dict(passed=sum(not list(c) for c in cases),skipped=sum(c.find('skipped') is not None for c in cases),total=len(cases)),automatic_promotion=False,authenticity='Requires owner verification of host/job provenance; a synthetic receipt cannot prove actual host execution')
def main():
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--system',required=True,choices=['Windows','Linux','Darwin']);p.add_argument('--context',required=True,choices=['local','ci','kaggle']);a=p.parse_args();print(json.dumps(verify(a.folder,a.system,a.context)))
if __name__=='__main__':main()
