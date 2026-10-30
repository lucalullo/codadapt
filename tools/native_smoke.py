"""Actual installed-extension calls, exact outputs, persistence and bounded profiling."""
from pathlib import Path
import argparse,cProfile,hashlib,json,pickle,platform,pstats,sys,time
import numpy as np
import psutil
from codadapt import CodAdaptClassifier,CodAdaptRegressor
from codadapt._inference import inference_backend,_load_native,_active_backend
from codadapt.serving import export_model,load_model

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--backend',choices=['native','python'],required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    import codadapt
    assert Path(codadapt.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),'Installed consumer required'
    module=_load_native() if args.backend=='native' else None
    calls=[0]
    if module:
        original=module.predict_head
        def counted(*a,**k):calls[0]+=1;return original(*a,**k)
        module.predict_head=counted
    rng=np.random.default_rng(1729);X=rng.normal(size=(750,10));signal=X[:,0]+.4*X[:,1]-.25*X[:,2]
    rows=[];profiler=cProfile.Profile();profiler.enable()
    try:
        for task,y in [('binary',(signal>0).astype(int)),('multiclass',np.digitize(signal,[-.6,.6])),('regression',signal)]:
            model=CodAdaptRegressor(random_state=42) if task=='regression' else CodAdaptClassifier(random_state=42,class_weight='balanced')
            start=time.perf_counter();model.fit(X[:600],y[:600]);fit=time.perf_counter()-start
            state=pickle.dumps(model,protocol=5);(args.output/(task+'.pickle')).write_bytes(state);checks=0;timings=[]
            for n in (1,32,1000,2048,65536):
                query=np.resize(X[600:],(n,10));baseline={}
                for engine in ('python',args.backend):
                    with inference_backend(engine):
                        samples=[]
                        for i in range(5):
                            start=time.perf_counter_ns();model.predict(query);samples.append((time.perf_counter_ns()-start)/1e6)
                        for method in ('predict','predict_proba','decision_function'):
                            if not hasattr(model,method):continue
                            value=getattr(model,method)(query)
                            if engine=='python':baseline[method]=value
                            else:
                                expected=baseline[method];assert value.dtype==expected.dtype and value.shape==expected.shape and value.tobytes()==expected.tobytes();checks+=1
                        timings.append(dict(rows=n,backend=engine,median_ms=float(np.median(samples)),p95_ms=float(np.percentile(samples,95))))
            assert pickle.dumps(model,protocol=5)==state
            image=args.output/(task+'.codadapt');receipt=export_model(model,image)
            restored=load_model(image,trusted=True,expected_sha256=receipt['artifact_sha256'])
            # Auto on Linux would otherwise compare Python with Python here.
            with inference_backend(args.backend):
                expected=model.predict(X[600:])
                assert np.array_equal(restored.predict(X[600:]),expected)
                assert np.array_equal(pickle.loads(state).predict(X[600:]),expected)
            rows.append(dict(task=task,fit_seconds=fit,exact_arrays=checks,timing=timings,pickle_bytes=len(state),artifact_bytes=image.stat().st_size))
    finally:
        profiler.disable()
        if module:module.predict_head=original
    stats=pstats.Stats(profiler);top=sorted(stats.stats.items(),key=lambda row:row[1][3],reverse=True)[:30]
    profile=[dict(file=Path(key[0]).name,line=key[1],function=key[2],calls=value[1],self_seconds=value[2],cumulative_seconds=value[3]) for key,value in top]
    assert calls[0]>0 if module else calls[0]==0
    import importlib.metadata as md
    result=dict(packages={n:md.version(n) for n in ('codadapt','numpy','pandas','scipy','scikit-learn','pybind11')},status='PASS_ACTUAL_INSTALLED_BACKEND',platform=platform.platform(),python=sys.version,backend=args.backend,default_backend=_active_backend(),
        native_calls=calls[0],extension_name=Path(module.__file__).name if module else None,
        extension_SHA256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() if module else None,
        cases=rows,profile=profile,process_memory=psutil.Process().memory_info()._asdict(),engineering_fits=3,scientific_fits=0,
        timing_scope='cProfile enabled; diagnostic timings only, not a speed-promotion benchmark',memory_scope='Whole process after work; not peak unless OS supplies peak_wset')
    (args.output/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('cases','profile')}))
if __name__=='__main__':main()
