"""Finite, reproducible engineering workload; no scientific source or holdout."""
from pathlib import Path
from time import perf_counter_ns
import argparse
import hashlib
import importlib.metadata as md
import importlib.util
import json
import pickle
import platform
import sys
import joblib
import numpy as np
import psutil
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from codadapt import CodAdaptClassifier, CodAdaptRegressor
from codadapt._inference import inference_backend, _active_backend
from codadapt.serving import export_model, load_model


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--native',choices=['required','absent'],required=True)
    args=parser.parse_args()
    out=Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=False)
    native_available=importlib.util.find_spec('codadapt._native_kernel') is not None
    assert native_available == (args.native=='required')
    if native_available:
        with inference_backend('native'): assert _active_backend()=='native'
    else:
        try:
            with inference_backend('native'): pass
        except RuntimeError as e:
            assert 'not built' in str(e)
        else: raise AssertionError('Explicit native must not silently fall back')
    rng=np.random.default_rng(1729)
    X=rng.normal(size=(750,10))
    signal=X[:,0]+.4*X[:,1]-.25*X[:,2]+.1*np.sin(X[:,3])
    targets={'binary':(signal>0).astype(int), 'multiclass':np.digitize(signal,[-.6,.6]), 'regression':signal}
    weight=np.linspace(.5,1.5,600);weight[:6]=0
    cases=[]
    for task,y in targets.items():
        fits=[];first=None
        for repeat in range(5):
            est=CodAdaptRegressor(random_state=42) if task=='regression' else CodAdaptClassifier(random_state=42,class_weight='balanced')
            model=Pipeline([('model',clone(est))])
            start=perf_counter_ns();model.fit(X[:600],y[:600],model__sample_weight=weight)
            fits.append((perf_counter_ns()-start)/1e6)
            pred=model.predict(X[600:])
            prob=model.predict_proba(X[600:]) if task!='regression' else None
            if first is None: first=(pred.copy(),None if prob is None else prob.copy())
            else:
                assert np.array_equal(first[0],pred)
                if prob is not None: assert np.array_equal(first[1],prob)
        est=model.named_steps['model']
        raw=pickle.dumps(model,protocol=5)
        (out/(task+'.pickle')).write_bytes(raw)
        restored=pickle.loads(raw)
        assert np.array_equal(pred,restored.predict(X[600:]))
        joblib.dump(model,out/(task+'.joblib'))
        assert np.array_equal(pred,joblib.load(out/(task+'.joblib')).predict(X[600:]))
        receipt=export_model(est,out/(task+'.codadapt'))
        loaded=load_model(out/(task+'.codadapt'),trusted=True,expected_sha256=receipt['artifact_sha256'])
        assert np.array_equal(pred,loaded.predict(X[600:]))
        if prob is not None: assert np.array_equal(prob,loaded.predict_proba(X[600:]))
        timings={};equalities=0
        for rows in (1,32,2048):
            query=np.resize(X[600:],(rows,X.shape[1]))
            outputs={};times={}
            for backend in (('python','native') if native_available else ('python',)):
                with inference_backend(backend):
                    model.predict(query)
                    samples=[]
                    for _ in range(5):
                        start=perf_counter_ns();output=model.predict(query)
                        samples.append((perf_counter_ns()-start)/1e6)
                    outputs[backend]=output.copy()
                    if task!='regression': outputs[backend+'_proba']=model.predict_proba(query)
                    times[backend]=dict(samples_ms=samples,median_ms=float(np.median(samples)),p95_ms=float(np.percentile(samples,95)))
            if native_available:
                assert outputs['python'].dtype==outputs['native'].dtype
                assert outputs['python'].tobytes()==outputs['native'].tobytes();equalities+=1
                if task!='regression':
                    assert outputs['python_proba'].tobytes()==outputs['native_proba'].tobytes();equalities+=1
                times['native_to_python_median_ratio']=times['native']['median_ms']/times['python']['median_ms']
            timings[str(rows)]=times
        assert raw==pickle.dumps(model,protocol=5),'inference changed model state'
        cases.append(dict(task=task,training_ms=fits,training_median_ms=float(np.median(fits)),
            inference=timings,exact_engine_output_arrays=equalities,deterministic_fit_prediction_repeats=5,
            pickle_bytes=len(raw),joblib_bytes=(out/(task+'.joblib')).stat().st_size,
            artifact_bytes=(out/(task+'.codadapt')).stat().st_size,
            prediction_SHA256=hashlib.sha256(pred.tobytes()).hexdigest(),
            persistence_pickle_joblib_export='PASS',API_clone_pipeline_weights_zeros='PASS'))
    memory=psutil.Process().memory_info()._asdict()
    result=dict(status='PASS_FINITE_ENGINEERING_PROBE',python=sys.version,system=platform.system(),
        machine=platform.machine(),prefix=sys.prefix,default_backend=_active_backend(),
        native_module_present=native_available,packages={d.metadata['Name']:d.version for d in md.distributions()},
        cases=cases,process_memory=memory,memory_scope='whole process after import/training/persistence/inference; not model-only RAM',
        engineering_fits=15,scientific_fits=0,
        native_batch2048_10pct_guard=all(c['inference']['2048']['native_to_python_median_ratio']<=1.10 for c in cases) if native_available else None)
    (out/'RESULT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in {'cases','packages'}}))

if __name__=='__main__':main()
