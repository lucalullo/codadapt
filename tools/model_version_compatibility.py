"""No-fit compatibility replay of trusted, already fitted engineering artifacts.

Run prepare-old under the preserved old installed wheel, then check-new under
the new installed wheel with the same Python minor and NumPy/pandas versions.
The input is trusted local engineering state, never an unknown pickle sender.
This diagnostic does not relax the serving producer contract or migrate images.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata as md
import json
import pickle
import platform
import sys

TASKS=('binary','multiclass','regression')
ROWS=(1,32,2048)


def sha(path):
    with path.open('rb') as stream:
        digest=hashlib.sha256()
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        return digest.hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,indent=2),encoding='utf-8')


def runtime():
    import codadapt
    import numpy as np
    import pandas as pd
    from codadapt import CodAdaptClassifier,CodAdaptRegressor
    from codadapt.serving import export_model,load_model
    from codadapt._inference import inference_backend
    # Loading must never implicitly fit or use labels to alter the model.
    def forbidden(*args,**kwargs):raise AssertionError('Compatibility loading must never fit')
    CodAdaptClassifier.fit=forbidden
    CodAdaptRegressor.fit=forbidden
    assert Path(codadapt.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()),'Installed package required; no source injection'
    identity=dict(codadapt=codadapt.__version__,python=list(sys.version_info[:3]),
        numpy=np.__version__,pandas=pd.__version__,system=platform.system(),machine=platform.machine(),
        sklearn=md.version('scikit-learn'),joblib=md.version('joblib'))
    return np,export_model,load_model,inference_backend,identity


def query(np,rows):
    rng=np.random.default_rng(1729)
    X=rng.normal(size=(750,10))
    return np.resize(X[600:],(rows,X.shape[1]))


def outputs(model,np,expected=None):
    result={}
    methods=('predict','predict_proba','decision_function') if expected is None else tuple(sorted({key.rsplit('_',1)[0] for key in expected}))
    for rows in ROWS:
        X=query(np,rows)
        for name in methods:
            if hasattr(model,name):result[f'{name}_{rows}']=getattr(model,name)(X)
    for value in result.values():
        assert not value.dtype.hasobject and np.isfinite(value).all()
    return result


def compare(actual,expected,np):
    assert set(actual)==set(expected),(sorted(actual),sorted(expected))
    for key,value in actual.items():
        other=expected[key]
        assert value.dtype==other.dtype and value.shape==other.shape,key
        assert value.tobytes()==other.tobytes(),key
    return len(actual)


def prepare_old(args,out):
    np,export_model,load_model,inference_backend,identity=runtime()
    assert identity['codadapt']==args.expected_old_version
    import joblib
    folder=args.artifacts.resolve()
    receipt=json.loads((folder/'RESULT.json').read_text(encoding='utf-8'))
    assert receipt['status']=='PASS_FINITE_ENGINEERING_PROBE'
    assert receipt['packages']['codadapt']==identity['codadapt']
    record=dict(status='INCOMPLETE',identity=identity,task_records=[],fit_calls=0,
        scientific_fits=0,source='Previously qualified synthetic engineering probe only')
    for task in TASKS:
        file=folder/(task+'.pickle')
        model=pickle.loads(file.read_bytes())
        with inference_backend('python'):
            expected=outputs(model,np)
            compare(outputs(joblib.load(folder/(task+'.joblib')),np),expected,np)
        np.savez_compressed(out/(task+'_expected.npz'),**expected)
        original_image=folder/(task+'.codadapt')
        served=load_model(original_image,trusted=True,expected_sha256=sha(original_image))
        compare(outputs(served,np,expected),expected,np)
        record['task_records'].append(dict(task=task,
            pickle=str(file),pickle_SHA256=sha(file),
            joblib=str(folder/(task+'.joblib')),joblib_SHA256=sha(folder/(task+'.joblib')),
            old_image=str(original_image),old_image_SHA256=sha(original_image),
            expected=task+'_expected.npz',expected_SHA256=sha(out/(task+'_expected.npz')),
            old_pickle_joblib_and_serving='PASS',expected_arrays=len(expected)))
        write(out/'REFERENCE.json',record)
    record['status']='PASS_OLD_INSTALLED_RUNTIME_REFERENCE_NO_FIT'
    write(out/'REFERENCE.json',record)
    return record


def check_new(args,out):
    np,export_model,load_model,inference_backend,identity=runtime()
    assert identity['codadapt']==args.expected_new_version
    import joblib
    reference=args.reference.resolve()
    old=json.loads((reference/'REFERENCE.json').read_text(encoding='utf-8'))
    assert old['status']=='PASS_OLD_INSTALLED_RUNTIME_REFERENCE_NO_FIT'
    assert identity['python'][:2]==old['identity']['python'][:2], 'Use matching Python minor to isolate version change'
    assert all(identity[k]==old['identity'][k] for k in ('numpy','pandas','sklearn','joblib','system','machine')), 'Use the same dependency profile; otherwise this contrast is confounded'
    record=dict(status='INCOMPLETE',before=old['identity'],after=identity,cases=[],
        fit_calls=0,scientific_fits=0,cross_contract_migration_added=False)
    for row in old['task_records']:
        task=row['task']
        expected_file=reference/row['expected'];assert sha(expected_file)==row['expected_SHA256']
        with np.load(expected_file,allow_pickle=False) as arrays:
            expected={key:arrays[key] for key in arrays.files}
        count=0
        for kind in ('pickle','joblib'):
            file=Path(row[kind]);assert sha(file)==row[kind+'_SHA256']
            model=pickle.loads(file.read_bytes()) if kind=='pickle' else joblib.load(file)
            with inference_backend('python'):count+=compare(outputs(model,np),expected,np)
            if args.require_native:
                with inference_backend('native'):count+=compare(outputs(model,np),expected,np)
            # New version writes/loads its own new-contract image, never overwrites old.
            image=out/(task+'_'+kind+'.codadapt')
            receipt=export_model(model.named_steps['model'],image)
            served=load_model(image,trusted=True,expected_sha256=receipt['artifact_sha256'])
            compare(outputs(served,np,expected),expected,np)
            count+=len(expected)
        old_image=Path(row['old_image']);assert sha(old_image)==row['old_image_SHA256']
        try:
            load_model(old_image,trusted=True,expected_sha256=row['old_image_SHA256'])
        except ValueError as error:
            assert 'contract_sha256' in str(error), 'Rejection must isolate source contract, not unrelated profile drift'
            rejection=dict(type=type(error).__name__,message=str(error),expected=True)
        else:raise AssertionError('Old producer image unexpectedly accepted; migration was not authorized')
        record['cases'].append(dict(task=task,exact_arrays=count,
            old_pickle_joblib_readable='PASS_FINITE_MATCHING_PROFILE',
            new_export_load_roundtrip='PASS',old_serving_image_rejection=rejection,
            old_serving_images_need_preserved_old_runtime=True))
        write(out/'RESULT.json',record)
    record['status']='PASS_VERSION_COMPATIBILITY_REPLAY_FINITE_NO_FIT'
    record['scope']='Three fixed synthetic models, same dependency/Python-minor profile; not universal pickle or cross-platform compatibility'
    write(out/'RESULT.json',record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    old=commands.add_parser('prepare-old')
    old.add_argument('--artifacts',required=True,type=Path)
    old.add_argument('--expected-old-version',default='2.0.0.dev0+lab.g6r1')
    new=commands.add_parser('check-new')
    new.add_argument('--reference',required=True,type=Path)
    new.add_argument('--expected-new-version',default='2.1.0')
    new.add_argument('--require-native',action='store_true')
    for child in (old,new):
        child.add_argument('--output',required=True,type=Path)
        child.add_argument('--trusted-local-artifacts',action='store_true',required=True)
    args=parser.parse_args()
    out=args.output.resolve()
    source=(args.artifacts if args.command=='prepare-old' else args.reference).resolve()
    if out.exists() or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('Output must be new and non-overlapping')
    out.mkdir(parents=True,exist_ok=False)
    try:
        result=prepare_old(args,out) if args.command=='prepare-old' else check_new(args,out)
    except BaseException as error:
        write(out/'FAILED.json',dict(status='FAIL_OR_BLOCKED',error=repr(error),fit_calls=0))
        raise
    print(json.dumps({k:v for k,v in result.items() if k not in ('task_records','cases')},indent=2))


if __name__=='__main__':main()
