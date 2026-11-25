"""Reproduce one fixed historical classification case; no tuning or publication."""
from pathlib import Path
from time import perf_counter, perf_counter_ns
import argparse
import hashlib
import importlib.metadata as md
import json
import pickle
import platform
import numpy as np
import pandas as pd
import psutil
from threadpoolctl import threadpool_limits
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.metrics import balanced_accuracy_score,accuracy_score,f1_score,recall_score,log_loss,confusion_matrix
from codadapt import CodAdaptClassifier

ROOT=Path(__file__).resolve().parent
ALGORITHMS=('CodAdapt','CodAdaptBalanced','DecisionTree','RandomForest','HGB','LightGBM')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True)
    parser.add_argument('--algorithm',choices=ALGORITHMS,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((ROOT/'data/MANIFEST.json').read_text())
    row=next(r for r in manifest['records'] if r['ID']==args.case)
    file=(ROOT/'data'/row['file']).resolve()
    assert file.is_relative_to(ROOT/'data')
    assert hashlib.sha256(file.read_bytes()).hexdigest()==row['SHA256']
    args.output.mkdir(parents=True,exist_ok=False)
    with np.load(file,allow_pickle=False) as data:
        columns=data['columns'].tolist()
        X=pd.DataFrame(data['TRAIN_X'],columns=columns);y=data['TRAIN_y']
        q=pd.DataFrame(data['EVAL_X'],columns=columns);target=data['EVAL_y']
    params=dict(random_state=row['seed'])
    if args.algorithm=='LightGBM':
        from lightgbm import LGBMClassifier
        cls=LGBMClassifier
        params.update(n_estimators=100,learning_rate=.1,num_leaves=31,n_jobs=1,deterministic=True,force_col_wise=True,verbosity=-1)
    else:cls={'CodAdapt':CodAdaptClassifier,'CodAdaptBalanced':CodAdaptClassifier,
        'DecisionTree':DecisionTreeClassifier,'RandomForest':RandomForestClassifier,'HGB':HistGradientBoostingClassifier}[args.algorithm]
    if args.algorithm=='CodAdaptBalanced':params['class_weight']='balanced'
    if args.algorithm=='RandomForest':params.update(n_estimators=100,n_jobs=1)
    if args.algorithm=='HGB':params['max_iter']=100
    model=cls(**params);proc=psutil.Process();before=proc.memory_info()._asdict()
    with threadpool_limits(limits=1):
        start=perf_counter();model.fit(X,y);fit=perf_counter()-start
        after=proc.memory_info()._asdict()
        pred=model.predict(q);prob=model.predict_proba(q)
        timing={}
        for n in (1,32,2048):
            batch=q.iloc[np.arange(n)%len(q)]
            for _ in range(3):model.predict_proba(batch)
            times=[]
            for _ in range(7):
                start=perf_counter_ns();model.predict_proba(batch);times.append(perf_counter_ns()-start)
            timing[str(n)]=dict(median_ns=float(np.median(times)),p95_ns=float(np.percentile(times,95)),samples_ns=times)
    blob=pickle.dumps(model,protocol=5);restored=pickle.loads(blob)
    assert np.array_equal(restored.predict(q),pred)
    assert restored.predict_proba(q).tobytes()==prob.tobytes()
    metrics=dict(balanced_accuracy=balanced_accuracy_score(target,pred),accuracy=accuracy_score(target,pred),
        macro_f1=f1_score(target,pred,average='macro'),recall=recall_score(target,pred,labels=model.classes_,average=None).tolist(),
        logloss=log_loss(target,prob,labels=model.classes_),confusion=confusion_matrix(target,pred,labels=model.classes_).tolist())
    result=dict(case=args.case,algorithm=args.algorithm,seed=row['seed'],parameters=params,metrics=metrics,
        fit_seconds=fit,inference=timing,model_bytes=len(blob),memory_before_fit=before,memory_after_fit=after,
        system=platform.platform(),machine=platform.machine(),source_SHA256=row['SHA256'],
        versions={n:md.version(n) for n in ('codadapt','numpy','pandas','scipy','scikit-learn','psutil')},
        independent_new_confirmation=False,tuning_budget=0,threads=1)
    (args.output/'RESULT.json').write_text(json.dumps(result,indent=2))
    np.savez_compressed(args.output/'PREDICTIONS.npz',prediction=pred,probability=prob)
    print(json.dumps(metrics))

if __name__=='__main__':main()
