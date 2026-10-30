"""Owner-operated real manylinux build, repair and exact final-wheel consumer test.

No service, image pull, account, Git or publication operation is performed here.
Run inside an authorized pinned PyPA manylinux container; untested until executed.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,platform,shutil,subprocess,sys,tarfile,time
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expected-python',required=True);p.add_argument('--image-digest',required=True)
    p.add_argument('--wheelhouse',type=Path);p.add_argument('--allow-public-index',action='store_true');a=p.parse_args()
    out=a.output.resolve()
    if out.exists() or out==ROOT or out.is_relative_to(ROOT):raise ValueError('New output outside read-only source required')
    out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('collector',ROOT/'tools/external_delivery.py')
    collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
    state=dict(status='HOLD',version='2.1.0',steps=[],manylinux_qualified=False,source_contract_changed=False,
               image_digest=a.image_digest,system=platform.system(),machine=platform.machine(),python=sys.version)
    env=dict(os.environ,NETRC=os.devnull,PIP_CONFIG_FILE=os.devnull,PYTHONDONTWRITEBYTECODE='1',
             PYTHONNOUSERSITE='1',PIP_CACHE_DIR=str(out/'pip-cache'))
    start=time.monotonic()
    def run(label,command,cwd=ROOT,extra=None,timeout=300):
        with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
            result=subprocess.run(command,cwd=cwd,env=dict(env,**(extra or {})),stdout=stdout,stderr=stderr,
                                  timeout=min(timeout,max(1,2400-(time.monotonic()-start))))
        state['steps'].append(dict(label=label,returncode=result.returncode));result.check_returncode()
    try:
        if platform.system()!='Linux' or platform.machine()!='x86_64':raise ValueError('Real Linux x86_64 required')
        if platform.libc_ver()!=('glibc','2.28') or os.environ.get('AUDITWHEEL_PLAT')!='manylinux_2_28_x86_64':
            raise ValueError('Actual PyPA manylinux_2_28 baseline required; do not merely change a label')
        if platform.python_version()!=a.expected_python:raise ValueError('Unexpected actual Python patch')
        if not a.image_digest.startswith('sha256:') or len(a.image_digest)!=71 or any(c not in '0123456789abcdef' for c in a.image_digest[7:]):raise ValueError('Pinned actual image digest required')
        if not a.wheelhouse and not a.allow_public_index:raise ValueError('Explicit authorized dependency source required')
        location=['--no-index','--find-links',str(a.wheelhouse.resolve()),'--only-binary=:all:'] if a.wheelhouse else ['--index-url','https://pypi.org/simple','--only-binary=:all:']
        build=out/'build_env';run('build_environment',[sys.executable,'-I','-B','-m','venv',str(build)])
        py=build/'bin/python'
        run('build_dependencies',[str(py),'-I','-B','-m','pip','--isolated','--disable-pip-version-check','--no-input','--keyring-provider','disabled','install',*location,'-r',str(ROOT/'requirements/build.txt'),'psutil==7.2.2','auditwheel==6.8.2'])
        run('tool_versions',[str(py),'-I','-B','-m','pip','freeze','--all'])
        source=out/'source';source.mkdir()
        for folder in ('src','native','tools','tests','docs','requirements','examples','benchmarks','qualification'):
            shutil.copytree(ROOT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyd','*.so'))
        for f in ROOT.iterdir():
            if f.is_file():shutil.copyfile(f,source/f.name)
        raw=out/'raw_dist';raw.mkdir()
        run('sdist',[str(py),'-I','-B','-m','build','--sdist','--no-isolation','--outdir',str(raw)],source,{'CODADAPT_BUILD_NATIVE':'0'})
        sdist,=raw.glob('*.tar.gz');restored=out/'restored';restored.mkdir()
        with tarfile.open(sdist) as tar:
            for m in tar:
                parts=Path(m.name).parts[1:]
                if not parts:continue
                target=(restored/Path(*parts)).resolve()
                if not target.is_relative_to(restored):raise ValueError('Source archive traversal')
                if m.isdir():target.mkdir(parents=True,exist_ok=True)
                elif m.isfile():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tar.extractfile(m).read())
                else:raise ValueError('Source links forbidden')
        run('native_build',[str(py),'-I','-B','-m','build','--wheel','--no-isolation','--outdir',str(raw)],restored,{'CODADAPT_BUILD_NATIVE':'1'})
        wheel,=raw.glob('*.whl');repaired=out/'repaired_dist';repaired.mkdir()
        run('audit_original',[str(py),'-I','-B','-m','auditwheel','show',str(wheel)])
        run('repair',[str(py),'-I','-B','-m','auditwheel','repair','--plat','manylinux_2_28_x86_64','--wheel-dir',str(repaired),str(wheel)])
        final,=repaired.glob('*.whl')
        if 'manylinux_2_28_x86_64' not in final.name:raise ValueError('Unexpected repaired wheel tag')
        run('audit_repaired',[str(py),'-I','-B','-m','auditwheel','show',str(final)])
        digest=hashlib.sha256(final.read_bytes()).hexdigest()
        common=['--wheelhouse',str(a.wheelhouse.resolve())] if a.wheelhouse else ['--allow-public-index']
        run('test_exact_repaired_wheel',[str(py),'-I','-B',str(ROOT/'tools/run_external.py'),'--context','ci',
            '--expected-python',a.expected_python,'--output',str(out/'qualification'),'--native-wheel',str(final),
            '--expected-wheel-sha256',digest,'--sdist',str(sdist),*common],timeout=1800)
        state.update(status='PASS_EXECUTED_BASELINE_SCOPE',manylinux_qualified='BASELINE_AUDIT_AND_ACTUAL_CONSUMER_ONLY',
                     repaired_wheel=final.name,repaired_SHA256=digest,
                     broader_runtime_qualification='Separate deployment/Kaggle execution of these exact repaired bytes required',automatic_promotion=False)
    except BaseException as error:state.update(status='HOLD_EXECUTION_FAILED_OR_UNAVAILABLE',error=repr(error))
    finally:
        state['seconds']=time.monotonic()-start;archive=collector.collect_results(out,state)
        print(json.dumps(dict(**state,return_zip=str(archive))))
    return 0 if state['status']=='PASS_EXECUTED_BASELINE_SCOPE' else 1
if __name__=='__main__':raise SystemExit(main())
