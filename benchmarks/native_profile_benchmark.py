"""No-fit explicit-backend benchmark on trusted engineering models only."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import pickle
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def worker(args):
    import importlib.metadata as md
    import numpy as np
    import psutil
    from codadapt import CodAdaptClassifier, CodAdaptRegressor
    from codadapt._inference import inference_backend, _active_backend

    def forbidden(*args, **kwargs):
        raise AssertionError("No new fit is authorized by this benchmark")
    CodAdaptClassifier.fit = forbidden
    CodAdaptRegressor.fit = forbidden
    rng = np.random.default_rng(1729)
    X = rng.normal(size=(750, 10))[600:]
    cases = []
    default = _active_backend()
    with inference_backend(args.backend):
        assert _active_backend() == args.backend
        for task in ("binary", "multiclass", "regression"):
            path = Path(args.models) / (task + ".pickle")
            model = pickle.loads(path.read_bytes())  # Trusted local probe only.
            before = pickle.dumps(model, protocol=5)
            for size in (1, 32, 2048, 65536):
                query = np.resize(X, (size, 10))
                model.predict(query)
                times = []
                for _ in range(5 if size == 65536 else 30):
                    start = time.perf_counter_ns()
                    model.predict(query)
                    times.append((time.perf_counter_ns() - start) / 1e6)
                outputs = {}
                for method in ("predict", "predict_proba", "decision_function"):
                    if hasattr(model, method):
                        value = getattr(model, method)(query)
                        outputs[method] = dict(dtype=str(value.dtype), shape=list(value.shape),
                            SHA256=hashlib.sha256(value.tobytes()).hexdigest())
                cases.append(dict(task=task, rows=size, samples_ms=times,
                    median_ms=float(np.median(times)), p95_ms=float(np.percentile(times, 95)),
                    rows_per_second=float(size / (np.median(times) / 1000)), outputs=outputs,
                    pickle_bytes=len(before), model_SHA256=sha(path)))
            assert before == pickle.dumps(model, protocol=5), "Inference mutated the model"
    memory = psutil.Process().memory_info()._asdict()
    result = dict(status="PASS_NO_FIT_WORKER", backend=args.backend, default_backend=default,
        python=sys.version, packages={name:md.version(name) for name in
            ("codadapt", "numpy", "pandas", "scipy", "scikit-learn")}, cases=cases,
        memory=memory, scientific_fits=0, all_fits=0)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")


def orchestrate(args):
    import statistics
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    all_records = []
    for pair in range(9):
        arms = ("python", "native") if pair % 2 == 0 else ("native", "python")
        records = {}
        for arm in arms:
            output = root / (str(pair) + "_" + arm + ".json")
            command = [args.python, "-I", "-B", str(Path(__file__).resolve()), "worker",
                       "--models", args.models, "--backend", arm, "--output", str(output)]
            with output.with_suffix(".stdout.txt").open("wb") as stdout, output.with_suffix(".stderr.txt").open("wb") as stderr:
                proc = subprocess.run(command, env=os.environ.copy(), stdout=stdout, stderr=stderr, timeout=45)
            proc.check_returncode()
            records[arm] = json.loads(output.read_text())
        for a, b in zip(records["python"]["cases"], records["native"]["cases"]):
            assert a["outputs"] == b["outputs"], (pair, a["task"], a["rows"])
            assert a["pickle_bytes"] == b["pickle_bytes"]
        all_records.append(records)
    cells = []
    for index in range(12):
        p = [r["python"]["cases"][index] for r in all_records]
        n = [r["native"]["cases"][index] for r in all_records]
        record = dict(task=p[0]["task"], rows=p[0]["rows"])
        for field in ("median_ms", "p95_ms", "rows_per_second"):
            record["python_" + field] = statistics.median(c[field] for c in p)
            record["native_" + field] = statistics.median(c[field] for c in n)
        record["median_ratio"] = record["native_median_ms"] / record["python_median_ms"]
        record["p95_ratio"] = record["native_p95_ms"] / record["python_p95_ms"]
        cells.append(record)
    peaks = {arm:[r[arm]["memory"]["peak_wset"] for r in all_records] for arm in ("python", "native")}
    peak_ratio = statistics.median(peaks["native"]) / statistics.median(peaks["python"])
    target = next(c for c in cells if c["task"] == "multiclass" and c["rows"] == 2048)
    all_latency = all(c["median_ratio"] <= 1.05 and c["p95_ratio"] <= 1.05 for c in cells)
    g3_small = all(c["median_ratio"] <= 1.05 and c["p95_ratio"] <= 1.05 for c in cells if c["rows"] in (1,32))
    result = dict(status="PASS_MEASUREMENT_COMPLETE", python=all_records[0]["python"]["python"],
        packages=all_records[0]["python"]["packages"], cells=cells, processes=18, paired_processes=9,
        process_peak_RSS_bytes=peaks, process_peak_RSS_median_ratio=peak_ratio,
        exact_output_comparisons=sum(len(c["outputs"]) for r in all_records for c in r["python"]["cases"]),
        state_immutable=True, all_fits=0,
        gates=dict(G3_MC2048_20pct=target["median_ratio"]<=.8, G3_small_median_p95=g3_small,
                   all_batches_no_latency_regression=all_latency, G3_RSS=peak_ratio<=1.05, payload_exact=True),
        performance_gate=bool(target["median_ratio"]<=.8 and all_latency and peak_ratio<=1.05),
        automatic_extension="NOT_PERFORMED_PRESERVE_EXISTING_PRODUCER_CONTRACT",
        source_contract_SHA256="940f9fd84198feb1f6d6fb1a515ca2028a5f7a9ca65c4f98c8713391f58f462b")
    (root / "RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode", choices=("worker", "run"))
    p.add_argument("--python")
    p.add_argument("--models", required=True)
    p.add_argument("--backend", choices=("python", "native"))
    p.add_argument("--output", required=True)
    args=p.parse_args()
    (worker if args.mode == "worker" else orchestrate)(args)
