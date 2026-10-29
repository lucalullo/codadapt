"""Bounded real-host qualification. This command never publishes packages."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('codadapt_qualification_process',ROOT/'tools/qualification_process.py')
process_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(process_module)

identity_spec=importlib.util.spec_from_file_location('codadapt_qualification_identity',ROOT/'tools/qualification_identity.py')
identity_module=importlib.util.module_from_spec(identity_spec);identity_spec.loader.exec_module(identity_module)

def qualification_inputs(root=ROOT):
    return identity_module.qualification_inputs(root)

def stage_build_inputs(source,root=ROOT):
    """Copy bound root files and two public benchmarks, never research datasets."""
    for relative in (*identity_module.ROOT_BUILD_INPUTS,*identity_module.BENCHMARK_BUILD_INPUTS):
        destination=source/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/relative,destination)

def profile(version):
    if version[:2]==(3,10):return 'windows310.txt','historically_qualified_exact_pins_on_Windows31022'
    if version[:2]==(3,11):return 'windows310.txt','compatible_dependency_candidate_NOT_TESTED_on_Python311'
    if version[:2] in ((3,12),(3,14)):return 'windows312.txt','historically_tested_pins_only_exact_patch_OS_qualification'
    return 'windows312.txt','dependency_availability_and_execution_NOT_TESTED'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--backend',choices=['native','pure'],default='native')
    parser.add_argument('--wheelhouse',type=Path)
    parser.add_argument('--output-root',type=Path,default=ROOT/'qualification_runs')
    args=parser.parse_args()
    if not args.run_id or not all(c.isascii() and (c.isalnum() or c in '-_') for c in args.run_id):
        raise ValueError('run-id must be a simple new ASCII name')
    output_root=args.output_root.resolve()
    if output_root==ROOT or any(output_root.is_relative_to(ROOT/d) for d in ('src','native','tests','dist','tools','requirements','benchmarks')):
        raise ValueError('Output must not overlap product or qualification inputs')
    out=output_root/args.run_id;out.mkdir(parents=True,exist_ok=False)
    env={k:os.environ[k] for k in ('PATH','SystemRoot','WINDIR','COMSPEC','PATHEXT','ProgramFiles','ProgramFiles(x86)',
        'ProgramW6432','SystemDrive','PROCESSOR_ARCHITECTURE','PROCESSOR_ARCHITEW6432','PROCESSOR_IDENTIFIER','NUMBER_OF_PROCESSORS',
        'INCLUDE','LIB','LIBPATH','SDKROOT','MACOSX_DEPLOYMENT_TARGET','VCTOOLSINSTALLDIR','VCTOOLSVERSION',
        'WINDOWSSDKDIR','WINDOWSSDKVERSION','WINDOWSLIBPATH','UCRTVERSION','UNIVERSALCRTSDKDIR',
        'VISUALSTUDIOVERSION','VCINSTALLDIR','VSINSTALLDIR') if k in os.environ}
    if os.name=='nt' and env.get('INCLUDE') and env.get('LIB') and shutil.which('cl.exe',path=env.get('PATH')):
        env['DISTUTILS_USE_SDK']='1'
    temp=out/'tmp';temp.mkdir()
    env.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp),PIP_CACHE_DIR=str(out/'pip-cache'),
        PIP_CONFIG_FILE=os.devnull,PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',
        OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    result=dict(schema=2,UTC=datetime.now(timezone.utc).isoformat(),system=platform.system(),machine=platform.machine(),
        python=sys.version,backend=args.backend,status='INCOMPLETE',steps=[],
        source_SHA256=identity_module.source_identity(ROOT),
        qualification_inputs_SHA256=qualification_inputs(),
        runner_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        budgets=dict(command_seconds=300,total_seconds=1800,sampled_owned_tree_RSS_bytes=1536*1024**2),
        automatic_platform_promotion=False)
    begin=time.monotonic()
    def run(label,command,cwd=ROOT,extra=None):
        if any(s['label']==label for s in result['steps']):raise ValueError('Duplicate qualification stage')
        settings=dict(env);settings.update(extra or {})
        remaining=1800-(time.monotonic()-begin)
        if remaining<=0:raise RuntimeError('Total qualification time budget exhausted')
        with (out/(label+'.stdout.txt')).open('wb') as stdout,(out/(label+'.stderr.txt')).open('wb') as stderr:
            receipt=process_module.run_owned(command,cwd=cwd,env=settings,stdout=stdout,stderr=stderr,
                timeout=min(300,remaining),max_rss=1536*1024**2)
        result['steps'].append(dict(label=label,**receipt))
        (out/'RESULT.json').write_text(json.dumps(result,indent=2))
        if receipt['returncode']:raise RuntimeError(label+' failed; inspect logs. Do not bypass OS protections.')
    def executable(folder):return folder/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    def pip(exe):return [str(exe),'-I','-B','-m','pip','--isolated','--disable-pip-version-check','--no-input','--keyring-provider','disabled']
    if args.wheelhouse:
        warehouse=args.wheelhouse.resolve()
        if not warehouse.is_dir():raise ValueError('wheelhouse must already exist')
        location=['--no-index','--find-links',str(warehouse)]
    else:location=['--index-url','https://pypi.org/simple','--only-binary=:all:']
    try:
        if sys.implementation.name!='cpython' or not (3,10)<=sys.version_info[:2]<(3,16):
            raise RuntimeError('This matrix targets CPython3.10 through3.15')
        filename,qualification=profile(sys.version_info)
        pins=ROOT/'requirements'/filename
        result['dependency_profile']=dict(file=pins.relative_to(ROOT).as_posix(),qualification=qualification,
            SHA256=hashlib.sha256(pins.read_bytes()).hexdigest())
        build=out/'build_env'
        run('create_build_env',[sys.executable,'-I','-B','-m','venv',str(build)])
        bp=executable(build)
        run('build_dependencies',pip(bp)+['install','--no-compile',*location,'-r',str(ROOT/'requirements/build.txt')])
        # Resolve actual target wheels now; metadata permissiveness is not availability.
        run('dependency_preflight',pip(bp)+['install','--dry-run','--ignore-installed','--no-compile',*location,
            '--report',str(out/'dependency-preflight.json'),'-r',str(pins),'-r',str(ROOT/'requirements/qualification.txt')])
        source=out/'source';source.mkdir()
        for name in ('src','native','docs','tests','tools','requirements','examples'):
            shutil.copytree(ROOT/name,source/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyd','*.so'))
        stage_build_inputs(source)
        dist=out/'dist'
        run('build',[str(bp),'-I','-B','-m','build','--wheel','--sdist','--no-isolation','--outdir',str(dist)],source,
            {'CODADAPT_BUILD_NATIVE':'1' if args.backend=='native' else '0'})
        wheels=list(dist.glob('*.whl'))
        if len(wheels)!=1:raise RuntimeError('Expected one freshly built wheel')
        consumer=out/'consumer'
        run('create_consumer',[sys.executable,'-I','-B','-m','venv',str(consumer)])
        cp=executable(consumer)
        run('install_consumer',pip(cp)+['install','--no-compile',*location,'--report',str(out/'install-report.json'),
            '-r',str(pins),'-r',str(ROOT/'requirements/qualification.txt'),str(wheels[0])])
        run('dependency_check',pip(cp)+['check'])
        run('engineering_probe',[str(cp),'-I','-B',str(ROOT/'tools/engineering_probe.py'),
            '--output',str(out/'probe'),'--native','required' if args.backend=='native' else 'absent'])
        run('suite',[str(cp),'-I','-B','-m','pytest','-q','-o','cache_dir='+str(out/'pytest-cache'),
            '--basetemp='+str(out/'pytest-tmp'),'--junitxml='+str(out/'junit.xml')],extra={'CODADAPT_TEST_DIST':str(dist)})
        probe=json.loads((out/'probe/RESULT.json').read_text())
        result['status']='PASS_EXECUTED_PROFILE'
        result['functional_qualification']='PASS'
        result['performance_gate']='PASS_FINITE' if probe['native_batch2048_10pct_guard'] is True else 'HOLD' if args.backend=='native' else 'NOT_APPLICABLE_PURE'
        result['scope']='Functional execution only on the actual host/pins. Review performance, memory, skips and platform gates before promotion.'
    except BaseException as error:
        result['status']='FAIL_OR_BLOCKED';result['error']=repr(error)
        raise
    finally:
        result['total_seconds']=time.monotonic()-begin
        result['artifacts_SHA256']={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'dist').glob('*') if p.is_file()}
        (out/'RESULT.json').write_text(json.dumps(result,indent=2))
        files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file() and p.name!='RECEIPT_MANIFEST.json'}
        files.update(result['artifacts_SHA256'])
        for p in (out/'probe').glob('*.json'):files[p.relative_to(out).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
        (out/'RECEIPT_MANIFEST.json').write_text(json.dumps(dict(schema=2,files=files),indent=2))
        print(json.dumps(dict(status=result['status'],performance_gate=result.get('performance_gate','NOT_REACHED'),receipt=str(out/'RECEIPT_MANIFEST.json'))))

if __name__=='__main__':main()
