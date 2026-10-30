"""One owner-operated actual-host build/test/benchmark run and one returned ZIP."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,platform,sys,time
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--context',choices=['ci','kaggle','local'],required=True)
    p.add_argument('--expected-python');p.add_argument('--allow-public-index',action='store_true');p.add_argument('--wheelhouse',type=Path)
    p.add_argument('--native-wheel',type=Path);p.add_argument('--expected-wheel-sha256');p.add_argument('--sdist',type=Path)
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or out==ROOT or out.is_relative_to(ROOT/'src') or out.is_relative_to(ROOT/'tools') or out.is_relative_to(ROOT/'tests'):raise ValueError('New independent output required')
    out.mkdir(parents=True);collector=load('external_delivery');state=dict(status='HOLD',system=platform.system(),machine=platform.machine(),python=sys.version,context=a.context,steps=[],publication_approved=False)
    start=time.monotonic();env=dict(os.environ,NETRC=os.devnull,PIP_CONFIG_FILE=os.devnull,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    try:
        if a.expected_python:
            expected=tuple(int(n) for n in a.expected_python.split('.'))
            if sys.version_info[:len(expected)]!=expected:raise ValueError('Actual Python differs from requested target')
        if a.context=='kaggle' and (platform.system()!='Linux' or not Path('/kaggle/working').is_dir()):raise ValueError('Real Kaggle Linux required')
        owned=load('qualification_process')
        def run(label,command):
            remaining=1800-(time.monotonic()-start)
            with (out/(label+'.stdout')).open('wb') as stdout,(out/(label+'.stderr')).open('wb') as stderr:
                result=owned.run_owned(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=remaining,max_rss=1536*1024**2)
            state['steps'].append(dict(label=label,**result))
            if result['returncode']:raise RuntimeError(label+' failed; see retained logs')
        requirements=ROOT/'requirements'/('external-current.txt' if sys.version_info[:2]>=(3,12) else 'external-legacy.txt')
        common=['--context',a.context,'--runtime-requirements',str(requirements),'--full-suite']
        if a.wheelhouse:common+=['--wheelhouse',str(a.wheelhouse.resolve())]
        elif a.allow_public_index:common+=['--allow-public-index']
        else:raise ValueError('Explicit wheelhouse or public index permission required')
        native=[sys.executable,'-I','-B',str(ROOT/'tools/qualify_native_target.py'),'--output',str(out/'native'),'--run-benchmark',*common]
        if a.native_wheel:
            native+=['--native-wheel',str(a.native_wheel.resolve()),'--expected-wheel-sha256',a.expected_wheel_sha256 or '']
            if not a.sdist:raise ValueError('Wheel-only full qualification needs the paired source archive')
            native+=['--companion-sdist',str(a.sdist.resolve())]
        run('native_pipeline',native)
        run('verify_native_receipt',[sys.executable,'-I','-B',str(ROOT/'tools/verify_native_evidence.py'),str(out/'native'),'--system',platform.system(),'--context',a.context])
        consumer=out/'native/consumer'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        for task in ('binary','multiclass','regression'):
            for backend in ('python','native','lightgbm'):
                algorithm='lightgbm' if backend=='lightgbm' else 'codadapt'
                model=out/'native/benchmark'/(task+'_101_'+algorithm+'.pickle')
                run('load_'+task+'_'+backend,[str(consumer),'-I','-B',str(ROOT/'tools/import_load_probe.py'),'--model',str(model),'--backend',backend,'--output',str(out/('load_'+task+'_'+backend+'.json'))])
        for task in ('binary','multiclass','regression'):
            reference=json.loads((out/('load_'+task+'_python.json')).read_text())
            native_result=json.loads((out/('load_'+task+'_native.json')).read_text())
            if any(reference[k]!=native_result[k] for k in ('model_SHA256','prediction_SHA256')):raise ValueError('Isolated-load prediction mismatch: '+task)
        run('pure_pipeline',[sys.executable,'-I','-B',str(ROOT/'tools/qualify_native_target.py'),'--backend','pure','--output',str(out/'pure'),*common])
        state.update(status='PASS_EXECUTED_EXTERNAL_SCOPE',scope='Actual host, exact pins, full default suite, synthetic paired panel, explicit native, pure fallback; no automatic dispatch or release promotion')
    except BaseException as error:
        state.update(status='HOLD_EXECUTION_FAILED_OR_BLOCKED',error=repr(error))
    finally:
        state['seconds']=time.monotonic()-start;archive=collector.collect_results(out,state);print(json.dumps(dict(**state,return_zip=str(archive))))
    return 0 if state['status']=='PASS_EXECUTED_EXTERNAL_SCOPE' else 1
if __name__=='__main__':raise SystemExit(main())
