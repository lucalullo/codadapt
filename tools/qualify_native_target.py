"""Credential-free local native/pure build and actual clean-consumer qualification.

Invoke with a target CPython interpreter containing pip; pass an authorized
compiler environment on Windows. No services, accounts or OS policy are changed.
"""
from pathlib import Path
import argparse,hashlib,json,os,platform,shutil,subprocess,sys,tarfile,zipfile

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    p.add_argument('--runtime-requirements',required=True,type=Path)
    p.add_argument('--wheelhouse',type=Path);p.add_argument('--allow-public-index',action='store_true')
    p.add_argument('--pip-bootstrap',type=Path,help='Authorized interpreter with pip, if target has none')
    p.add_argument('--native-wheel',type=Path,help='Install a target-native wheel without invoking a compiler')
    p.add_argument('--expected-wheel-sha256',help='Required trusted SHA256 for wheel-only qualification')
    p.add_argument('--context',choices=['local','ci','kaggle'],default='local')
    p.add_argument('--run-benchmark',action='store_true',help='Requires LightGBM in explicit runtime requirements')
    p.add_argument('--full-suite',action='store_true')
    p.add_argument('--companion-sdist',type=Path)
    p.add_argument('--backend',choices=['native','pure'],default='native');a=p.parse_args()
    if a.native_wheel:
        if a.backend!='native' or not a.expected_wheel_sha256 or hashlib.sha256(a.native_wheel.read_bytes()).hexdigest()!=a.expected_wheel_sha256:raise ValueError('Native wheel identity mismatch')
        with zipfile.ZipFile(a.native_wheel) as z:
            suffix='.pyd' if os.name=='nt' else '.so'
            if not any(n.startswith('codadapt/_native_kernel') and n.endswith(suffix) for n in z.namelist()):raise ValueError('Actual target extension required; pure wheel is insufficient')
    out=a.output.resolve()
    if a.context=='kaggle' and (platform.system()!='Linux' or not Path('/kaggle/working').is_dir()):raise ValueError('Actual Kaggle Linux runtime required')
    if out.exists() or out==ROOT or any(out.is_relative_to(ROOT/d) for d in ('src','native','tools','tests','requirements','docs')):raise ValueError('New non-product output required')
    if not a.wheelhouse and not a.allow_public_index:raise ValueError('Explicit offline wheelhouse or public-index authorization required')
    out.mkdir(parents=True);record=dict(status='INCOMPLETE',system=platform.system(),machine=platform.machine(),python=sys.version,backend=a.backend,context=a.context,steps=[])
    record['runner_provenance']={k:os.environ.get(k) for k in ('GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','RUNNER_OS','RUNNER_ARCH') if os.environ.get(k)}
    import importlib.util
    spec=importlib.util.spec_from_file_location('codadapt_build_environment',ROOT/'tools/build_environment.py')
    build_environment=importlib.util.module_from_spec(spec);spec.loader.exec_module(build_environment)
    env=build_environment.forward_environment(os.environ)
    temp=out/'tmp';temp.mkdir();env.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp),PIP_CONFIG_FILE=os.devnull,NETRC=os.devnull,PIP_CACHE_DIR=str(out/'pip-cache'),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    location=['--no-index','--find-links',str(a.wheelhouse.resolve()),'--only-binary=:all:'] if a.wheelhouse else ['--index-url','https://pypi.org/simple','--only-binary=:all:']
    def run(label,cmd,cwd=ROOT,extra=None):
        with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
            r=subprocess.run(cmd,cwd=cwd,env=dict(env,**(extra or {})),stdout=stdout,stderr=stderr,timeout=300)
        record['steps'].append(dict(label=label,returncode=r.returncode));(out/'RESULT.json').write_text(json.dumps(record,indent=2));r.check_returncode()
    def python(folder):return folder/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    def pip(target):return [str(a.pip_bootstrap.resolve()) if a.pip_bootstrap else sys.executable,'-I','-B','-m','pip','--isolated','--disable-pip-version-check','--no-input','--keyring-provider','disabled','--python',str(target)]
    try:
        build=out/'build_env';consumer=out/'consumer'
        run('create_consumer',[sys.executable,'-I','-B','-m','venv','--without-pip',str(consumer)])
        if a.native_wheel:
            (out/'dist').mkdir();wheel=out/'dist'/a.native_wheel.name;shutil.copyfile(a.native_wheel,wheel)
            record['build_mode']='PREBUILT_NATIVE_WHEEL_NO_COMPILER'
            if a.companion_sdist:shutil.copyfile(a.companion_sdist,out/'dist'/a.companion_sdist.name)
        else:
            run('create_build',[sys.executable,'-I','-B','-m','venv','--without-pip',str(build)])
            run('build_dependencies',pip(python(build))+['install','--no-compile',*location,'-r',str(ROOT/'requirements/build.txt')])
            source=out/'source';source.mkdir()
            for folder in ('src','native','tools','tests','docs','requirements','examples','benchmarks','qualification'):
                shutil.copytree(ROOT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyd','*.so'))
            for file in ROOT.iterdir():
                if file.is_file():shutil.copyfile(file,source/file.name)
            run('sdist',[str(python(build)),'-I','-B','-m','build','--sdist','--no-isolation','--outdir',str(out/'dist')],source,{'CODADAPT_BUILD_NATIVE':'0'})
            archive,=(out/'dist').glob('*.tar.gz');restored=out/'restored';restored.mkdir()
            with tarfile.open(archive) as tar:
                for m in tar:
                    parts=Path(m.name).parts[1:]
                    if not parts:continue
                    dest=(restored/Path(*parts)).resolve();assert dest.is_relative_to(restored)
                    if m.isdir():dest.mkdir(parents=True,exist_ok=True)
                    elif m.isfile():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(tar.extractfile(m).read())
                    else:raise ValueError('Archive links forbidden')
            default_linux = a.backend=='native' and platform.system()=='Linux'
            record['build_mode']='STANDARD_LINUX_NATIVE_DEFAULT' if default_linux else 'EXPLICIT_NATIVE_OR_PURE'
            run('wheel_from_sdist',[str(python(build)),'-I','-B','-m','build','--wheel','--no-isolation','--outdir',str(out/'dist')],restored,{} if default_linux else {'CODADAPT_BUILD_NATIVE':'1' if a.backend=='native' else '0'})
            wheel,=(out/'dist').glob('*.whl')
        run('install',pip(python(consumer))+['install','--no-compile',*location,'-r',str(a.runtime_requirements.resolve()),'-r',str(ROOT/'requirements/external-tests.txt'),'pytest==9.1.1','psutil==7.2.2',str(wheel)])
        run('pip_check',pip(python(consumer))+['check'])
        run('wheel_audit',[str(python(consumer)),'-I','-B',str(ROOT/'tools/audit_native_wheel.py'),'--wheel',str(wheel),'--output',str(out/'WHEEL_AUDIT.json'),'--backend',a.backend])
        run('smoke',[str(python(consumer)),'-I','-B',str(ROOT/'tools/native_smoke.py'),'--output',str(out/'probe'),'--backend','native' if a.backend=='native' else 'python'])
        record['test_scope']='full_default_suite' if a.full_suite else 'native_boundary_only'
        run('native_boundary_suite',[str(python(consumer)),'-I','-B','-m','pytest','-q',* ([] if a.full_suite else ['tests/native']),'-o','cache_dir='+str(out/'pytest-cache'),'--basetemp='+str(out/'pytest-tmp'),'--junitxml='+str(out/'junit.xml')],extra={'CODADAPT_TEST_DIST':str(out/'dist')})
        if a.run_benchmark:
            if a.backend!='native':raise ValueError('Paired benchmark requires actual native consumer')
            run('lightgbm_preflight',[str(python(consumer)),'-I','-B','-c','import lightgbm; print(lightgbm.__version__)'])
            run('competitive_benchmark',[str(python(consumer)),'-I','-B',str(ROOT/'tools/competitive_reference.py'),'--output',str(out/'benchmark')])
        record.update(status='PASS_EXECUTED_TARGET_CORE',scope='Native boundary and3synthetic tasks; not full legacy/optional/platform or performance promotion',artifacts={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (out/'dist').iterdir()})
    except BaseException as error:record.update(status='FAIL_OR_BLOCKED',error=repr(error));raise
    finally:
        record['source_SHA256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src/codadapt','native') for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        record['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'dist').glob('*') if p.is_file()}
        (out/'RESULT.json').write_text(json.dumps(record,indent=2))
        bound={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and (p.parent==out or p.parent==out/'probe' or p.parent==out/'dist' or p.parent==out/'benchmark') and p.name!='RECEIPT_MANIFEST.json'}
        (out/'RECEIPT_MANIFEST.json').write_text(json.dumps(dict(files=bound,scope='Integrity only; owner must authenticate evidence and host'),indent=2));print(json.dumps(record))
if __name__=='__main__':main()
