"""Validate evidence integrity without executing external commands or model payloads."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse
import hashlib
import importlib.util
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
identity_spec=importlib.util.spec_from_file_location('codadapt_qualification_identity',ROOT/'tools/qualification_identity.py')
identity_module=importlib.util.module_from_spec(identity_spec);identity_spec.loader.exec_module(identity_module)

def relative_name(value):
    """Accept portable relative paths, never drives, ADS, traversal or aliases."""
    if not isinstance(value,str) or not value or ':' in value:
        raise ValueError('Invalid evidence path')
    name=value.replace('\\','/')
    if PurePosixPath(name).is_absolute() or PureWindowsPath(value).drive:
        raise ValueError('Absolute evidence path')
    if any(part in ('','.','..') for part in name.split('/')):
        raise ValueError('Non-canonical evidence path')
    return name

def normalized(mapping):
    output={}
    for key,value in mapping.items():
        name=relative_name(key)
        if name in output:raise ValueError('Duplicate evidence identity')
        output[name]=value
    return output

def contained_file(folder,rel):
    candidate=folder/relative_name(rel)
    path=candidate.resolve()
    if not path.is_relative_to(folder) or any(p.is_symlink() for p in (candidate,*candidate.parents) if p!=folder and p.is_relative_to(folder)):
        raise ValueError('Invalid evidence path')
    return path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('receipt_directory',type=Path)
    args=parser.parse_args();folder=args.receipt_directory.resolve()
    manifest=json.loads((folder/'RECEIPT_MANIFEST.json').read_text())
    if manifest.get('schema') not in (1,2):raise ValueError('Unknown schema')
    bound=normalized(manifest['files'])
    if 'RESULT.json' not in bound:raise ValueError('Unbound result file')
    for rel,digest in bound.items():
        path=contained_file(folder,rel)
        with path.open('rb') as stream:
            h=hashlib.sha256()
            for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
        if h.hexdigest()!=digest:raise ValueError('Evidence digest mismatch: '+rel)
    record=json.loads((folder/'RESULT.json').read_text())
    expected_sources=identity_module.source_identity(ROOT)
    supplied_sources=normalized(record['source_SHA256'])
    if supplied_sources!=expected_sources:raise ValueError('Incomplete or different product source identity')
    for rel,digest in supplied_sources.items():
        path=(ROOT/rel).resolve()
        if not path.is_relative_to(ROOT) or not rel.startswith(('src/','native/','src\\','native\\')):
            raise ValueError('Invalid source identity')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Different product source: '+rel)
    expected=hashlib.sha256((ROOT/'tools/qualify_platform.py').read_bytes()).hexdigest()
    if record['runner_SHA256']!=expected:raise ValueError('Different qualification runner')
    if manifest['schema']==2:
        if record.get('schema')!=2:raise ValueError('Contradictory receipt schema')
        expected_inputs=identity_module.qualification_inputs(ROOT)
        if normalized(record['qualification_inputs_SHA256'])!=expected_inputs:
            raise ValueError('Different or incomplete qualification inputs')
        if record.get('automatic_platform_promotion') is not False:
            raise ValueError('A receipt cannot promote itself')
    artifacts=normalized(record['artifacts_SHA256'])
    if any(bound.get(rel)!=digest for rel,digest in artifacts.items()):
        raise ValueError('Unbound or contradictory artifact identity')
    counts=None
    if (folder/'junit.xml').exists():
        xml=ET.parse(folder/'junit.xml');counts={'tests':0,'failures':0,'errors':0,'skipped':0}
        for case in xml.iter('testcase'):
            counts['tests']+=1
            for tag in ('failure','error','skipped'):
                if case.find(tag) is not None:counts[{'failure':'failures','error':'errors','skipped':'skipped'}[tag]]+=1
    if record['status']=='PASS_EXECUTED_PROFILE':
        if not {'junit.xml','probe/RESULT.json'}.issubset(bound):raise ValueError('Incomplete passing evidence')
        if counts is None or counts['tests']==0 or counts['failures'] or counts['errors']:
            raise ValueError('Passing status contradicts test results')
        probe=json.loads((folder/'probe/RESULT.json').read_text())
        if probe['status']!='PASS_FINITE_ENGINEERING_PROBE':raise ValueError('Probe did not pass')
        if any(s['returncode'] for s in record['steps']):raise ValueError('A required step failed')
        required={'create_build_env','build_dependencies','build','create_consumer',
                  'install_consumer','dependency_check','engineering_probe','suite'}
        if manifest['schema']==2:
            required.add('dependency_preflight')
            expected_gate='PASS_FINITE' if probe.get('native_batch2048_10pct_guard') is True else 'HOLD' if record['backend']=='native' else 'NOT_APPLICABLE_PURE'
            if record.get('functional_qualification')!='PASS' or record.get('performance_gate')!=expected_gate:
                raise ValueError('Functional/performance gate contradicts probe')
        if {s['label'] for s in record['steps']}!=required:
            raise ValueError('Missing or unrecognized qualification step')
        if len(record['steps'])!=len(required):raise ValueError('Duplicate qualification step')
        if not any(p.endswith('.whl') for p in artifacts) or not any(p.endswith('.tar.gz') for p in artifacts):
            raise ValueError('Missing distribution artifacts')
    print(json.dumps(dict(integrity='PASS',reported_status=record['status'],system=record['system'],
        machine=record['machine'],python=record['python'],suite=counts,
        automatic_platform_promotion=False,external_authenticity_attested=False),indent=2))

if __name__=='__main__':main()
