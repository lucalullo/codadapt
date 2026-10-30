"""Preregistered small synthetic reference panel; no tuning or candidate promotion."""
from pathlib import Path
import argparse,cProfile,hashlib,importlib.metadata as md,json,pickle,platform,pstats,sys,time,warnings
import numpy as np
import psutil
from sklearn.datasets import make_classification,make_regression
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score,accuracy_score,f1_score,recall_score,log_loss,mean_absolute_error,mean_squared_error

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    import codadapt,lightgbm
    # NumPy inputs are intentionally unnamed in both fit and prediction. Only
    # this known wrapper warning is excluded from latency; all others remain.
    warnings.filterwarnings('ignore',message='X does not have valid feature names, but LGBM.* was fitted with feature names',category=UserWarning)
    from codadapt import CodAdaptClassifier,CodAdaptRegressor
    from codadapt._inference import inference_backend,_load_native
    cases=[];profiles=[]
    for task in ('binary','multiclass','regression'):
        X,y=make_regression(n_samples=3000,n_features=10,n_informative=6,noise=10,random_state=919) if task=='regression' else make_classification(n_samples=3000,n_features=10,n_informative=6,n_redundant=2,n_classes=2 if task=='binary' else 3,n_clusters_per_class=1,random_state=919)
        datahash=hashlib.sha256(X.tobytes()+y.tobytes()).hexdigest()
        for seed in (101,202,303):
            indices=np.arange(len(y));tr,te=train_test_split(indices,test_size=.3,random_state=seed,stratify=None if task=='regression' else y)
            for algorithm in ('codadapt','lightgbm'):
                model=(CodAdaptRegressor(random_state=seed) if task=='regression' else CodAdaptClassifier(random_state=seed)) if algorithm=='codadapt' else (lightgbm.LGBMRegressor if task=='regression' else lightgbm.LGBMClassifier)(n_estimators=100,n_jobs=1,verbosity=-1,random_state=seed)
                t=time.perf_counter();model.fit(X[tr],y[tr]);fit=time.perf_counter()-t
                before=pickle.dumps(model,protocol=5);(a.output/(task+'_'+str(seed)+'_'+algorithm+'.pickle')).write_bytes(before);arms=[];expected={}
                for engine in (('python','native') if algorithm=='codadapt' else ('lightgbm',)):
                    ctx=inference_backend(engine) if algorithm=='codadapt' else __import__('contextlib').nullcontext()
                    with ctx:
                        pred=model.predict(X[te]);prob=model.predict_proba(X[te]) if task!='regression' else None
                        if engine=='python':expected=dict(predict=pred,proba=prob)
                        if engine=='native':
                            assert pred.tobytes()==expected['predict'].tobytes()
                            if prob is not None:assert prob.tobytes()==expected['proba'].tobytes()
                        metrics=dict(MAE=mean_absolute_error(y[te],pred),RMSE=float(np.sqrt(mean_squared_error(y[te],pred)))) if task=='regression' else dict(balanced_accuracy=balanced_accuracy_score(y[te],pred),accuracy=accuracy_score(y[te],pred),macro_F1=f1_score(y[te],pred,average='macro'),recall=recall_score(y[te],pred,average=None).tolist(),logloss=log_loss(y[te],prob))
                        timing=[]
                        for n in (1,32,1000,2048,65536):
                            query=np.resize(X[te],(n,10))
                            for method in (('predict',) if task=='regression' else ('predict','predict_proba')):
                                fn=getattr(model,method);fn(query);samples=[]
                                for _ in range(7):t=time.perf_counter_ns();fn(query);samples.append((time.perf_counter_ns()-t)/1e6)
                                timing.append(dict(rows=n,method=method,samples_ms=samples,median_ms=float(np.median(samples)),p95_ms=float(np.percentile(samples,95))))
                        arms.append(dict(backend=engine,metrics=metrics,timing=timing))
                assert pickle.dumps(model,protocol=5)==before
                cases.append(dict(task=task,seed=seed,algorithm=algorithm,data_SHA256=datahash,train_indices_SHA256=hashlib.sha256(tr.tobytes()).hexdigest(),test_indices_SHA256=hashlib.sha256(te.tobytes()).hexdigest(),fit_seconds=fit,pickle_bytes=len(before),params=model.get_params(),arms=arms,memory=psutil.Process().memory_info()._asdict()))
                (a.output/'PARTIAL.json').write_text(json.dumps(cases,indent=2))
                if algorithm=='codadapt' and seed==101:
                    profile=cProfile.Profile();profile.enable();model.fit(X[tr],y[tr]);profile.disable()
                    top=sorted(pstats.Stats(profile).stats.items(),key=lambda r:r[1][3],reverse=True)[:25]
                    profiles.append(dict(task=task,rows=len(tr),functions=[dict(file=Path(k[0]).name,line=k[1],name=k[2],calls=v[1],self_seconds=v[2],cumulative_seconds=v[3]) for k,v in top]))
    result=dict(status='PASS_REFERENCE_ENGINEERING_PANEL',system=platform.platform(),python=sys.version,packages={n:md.version(n) for n in ('codadapt','lightgbm','numpy','pandas','scipy','scikit-learn')},codadapt_source_SHA256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(codadapt.__file__).parent.glob('*.py')},kernel_SHA256=hashlib.sha256(Path(_load_native().__file__).read_bytes()).hexdigest(),cases=cases,profiles=profiles,benchmark_fits=18,additional_profile_fits=3,
        memory_scope='Cumulative process memory after each arm; not isolated per-model peak; use outer owned-tree peak separately',scope='Actual executing runtime recorded above; finite synthetic3splitpanel,not universal superiority or automatic promotion',candidate_qualified=False)
    (a.output/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('cases','profiles','codadapt_source_SHA256')}))
if __name__=='__main__':main()
