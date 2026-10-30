"""Fresh-process import/load/memory observations on trusted generated models."""
from pathlib import Path
import argparse,hashlib,json,pickle,sys,time
def main():
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--backend',choices=['python','native','lightgbm'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    start=time.perf_counter()
    if a.backend=='lightgbm':import lightgbm
    else:
        from codadapt import CodAdaptClassifier,CodAdaptRegressor
        from codadapt._inference import inference_backend,_load_native
        if a.backend=='native':_load_native()
    import_seconds=time.perf_counter()-start
    import numpy as np,psutil
    raw=a.model.read_bytes();start=time.perf_counter();model=pickle.loads(raw);load_seconds=time.perf_counter()-start
    query=np.random.default_rng(1729).normal(size=(2048,10))
    from contextlib import nullcontext
    with (nullcontext() if a.backend=='lightgbm' else inference_backend(a.backend)):value=model.predict(query)
    memory=psutil.Process().memory_info()._asdict();peak=memory.get('peak_wset')
    if peak is None:
        import resource
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    result=dict(backend=a.backend,import_seconds=import_seconds,load_seconds=load_seconds,peak_process_RSS_bytes=peak,memory=memory,model_bytes=len(raw),model_SHA256=hashlib.sha256(raw).hexdigest(),prediction_SHA256=hashlib.sha256(value.tobytes()).hexdigest(),scope='Fresh process including imports/model/query; not isolated model heap. Trusted locally generated pickle only.')
    a.output.write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
