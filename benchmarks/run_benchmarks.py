"""Lightweight public sanity benchmark for CodAdapt 0.1.0.

This runner is intentionally small and self-contained. It is not the frozen internal
release benchmark described in BENCHMARKS.md.
"""

from __future__ import annotations

import argparse
import csv
import pickle
import time
from pathlib import Path

import numpy as np
from sklearn.datasets import load_breast_cancer, load_diabetes, make_classification, make_regression
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, roc_auc_score
from sklearn.model_selection import train_test_split

from codadapt import CodAdapt, CodAdaptRegressor


def datasets(quick: bool):
    items = [
        ("breast_cancer", "classification", *load_breast_cancer(return_X_y=True)),
        ("diabetes", "regression", *load_diabetes(return_X_y=True)),
    ]
    if not quick:
        Xc, yc = make_classification(
            n_samples=4000,
            n_features=24,
            n_informative=8,
            n_redundant=4,
            class_sep=1.0,
            random_state=123,
        )
        Xr, yr = make_regression(
            n_samples=4000,
            n_features=20,
            n_informative=8,
            noise=15.0,
            random_state=456,
        )
        items.extend(
            [
                ("synthetic_classification", "classification", Xc, yc),
                ("synthetic_regression", "regression", Xr, yr),
            ]
        )
    return items


def models(task: str, seed: int):
    if task == "classification":
        result = {
            "codadapt": CodAdapt(random_state=seed, verbosity=0),
            "hist_gb": HistGradientBoostingClassifier(random_state=seed),
        }
        try:
            from lightgbm import LGBMClassifier

            result["lightgbm"] = LGBMClassifier(
                n_estimators=100, random_state=seed, n_jobs=1, verbosity=-1
            )
        except ImportError:
            pass
        return result

    result = {
        "codadapt": CodAdaptRegressor(random_state=seed, verbosity=0),
        "hist_gb": HistGradientBoostingRegressor(random_state=seed),
    }
    try:
        from lightgbm import LGBMRegressor

        result["lightgbm"] = LGBMRegressor(
            n_estimators=100, random_state=seed, n_jobs=1, verbosity=-1
        )
    except ImportError:
        pass
    return result


def timed_prediction(model, X, task: str, repeats: int = 5):
    predict = model.predict_proba if task == "classification" else model.predict
    predict(X[: min(32, len(X))])
    samples = []
    output = None
    for _ in range(repeats):
        started = time.perf_counter()
        output = predict(X)
        samples.append(time.perf_counter() - started)
    return output, float(np.median(samples))


def evaluate(name: str, task: str, X, y, seed: int):
    stratify = y if task == "classification" else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=stratify
    )
    rows = []
    for model_name, model in models(task, seed).items():
        started = time.perf_counter()
        model.fit(X_train, y_train)
        fit_seconds = time.perf_counter() - started
        prediction, predict_seconds = timed_prediction(model, X_test, task)
        if task == "classification":
            positive = prediction[:, 1]
            metric_name = "roc_auc"
            metric = roc_auc_score(y_test, positive)
        else:
            metric_name = "rmse"
            metric = float(np.sqrt(mean_squared_error(y_test, prediction)))
        rows.append(
            {
                "dataset": name,
                "task": task,
                "seed": seed,
                "model": model_name,
                "metric_name": metric_name,
                "metric": float(metric),
                "fit_seconds": float(fit_seconds),
                "predict_seconds": float(predict_seconds),
                "pickle_bytes": len(pickle.dumps(model, protocol=pickle.HIGHEST_PROTOCOL)),
                "n_train": len(X_train),
                "n_test": len(X_test),
                "n_features": X_train.shape[1],
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="Run two datasets and one seed.")
    parser.add_argument("--output", type=Path, help="Optional CSV output path.")
    args = parser.parse_args()
    seeds = [42] if args.quick else [42, 43, 44]
    rows = []
    for dataset_name, task, X, y in datasets(args.quick):
        for seed in seeds:
            rows.extend(evaluate(dataset_name, task, np.asarray(X), np.asarray(y), seed))

    header = "dataset task seed model metric fit_s predict_s pickle_kib".split()
    print(" | ".join(header))
    for row in rows:
        print(
            f"{row['dataset']} | {row['task']} | {row['seed']} | {row['model']} | "
            f"{row['metric_name']}={row['metric']:.6f} | {row['fit_seconds']:.4f} | "
            f"{row['predict_seconds']:.6f} | {row['pickle_bytes'] / 1024:.1f}"
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSaved {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
