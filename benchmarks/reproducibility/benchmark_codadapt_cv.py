"""Benchmark di stabilita' CodAdapt: cross-validation ripetuta, senza tuning.

Esecuzione dalla cartella del progetto con ambiente CodAdapt attivo:
  python "%USERPROFILE%\\Downloads\\benchmark_codadapt_cv.py" --quick
  python "%USERPROFILE%\\Downloads\\benchmark_codadapt_cv.py"

Nota: nessuna validazione indipendente; usa quattro piccoli dataset scikit-learn.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pickle
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
from codadapt import CodAdapt, CodAdaptRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.datasets import load_breast_cancer, load_diabetes, load_digits, load_wine
from sklearn.ensemble import (
    HistGradientBoostingClassifier, HistGradientBoostingRegressor,
    RandomForestClassifier, RandomForestRegressor,
)
from sklearn.metrics import mean_squared_error, roc_auc_score
from sklearn.model_selection import RepeatedKFold, RepeatedStratifiedKFold, StratifiedKFold, KFold
from threadpoolctl import threadpool_limits

FIELDS = [
    "dataset", "task", "repeat", "fold", "seed", "model", "metric_name", "metric",
    "fit_seconds", "predict_seconds", "pickle_kib", "n_train", "n_test", "n_features",
]


def datasets(quick):
    items = [
        ("breast_cancer", "classification", *load_breast_cancer(return_X_y=True)),
        ("diabetes", "regression", *load_diabetes(return_X_y=True)),
    ]
    if not quick:
        items.extend([
            ("wine", "classification", *load_wine(return_X_y=True)),
            ("digits", "classification", *load_digits(return_X_y=True)),
        ])
    return [(name, task, np.asarray(X), np.asarray(y)) for name, task, X, y in items]


def models(task, seed):
    if task == "classification":
        return {
            "codadapt": CodAdapt(random_state=seed, verbosity=0),
            "lightgbm": LGBMClassifier(n_estimators=100, n_jobs=1, random_state=seed, verbosity=-1),
            "random_forest": RandomForestClassifier(n_estimators=100, n_jobs=1, random_state=seed),
            "hist_gb": HistGradientBoostingClassifier(random_state=seed),
        }
    return {
        "codadapt": CodAdaptRegressor(random_state=seed, verbosity=0),
        "lightgbm": LGBMRegressor(n_estimators=100, n_jobs=1, random_state=seed, verbosity=-1),
        "random_forest": RandomForestRegressor(n_estimators=100, n_jobs=1, random_state=seed),
        "hist_gb": HistGradientBoostingRegressor(random_state=seed),
    }


def pkgver(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "non_disponibile"


def git_commit():
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def fingerprint(X, y):
    h = hashlib.sha256()
    for a in (X, y):
        a = np.ascontiguousarray(a)
        h.update(str((a.dtype.str, a.shape)).encode("utf-8"))
        h.update(a.tobytes())
    return h.hexdigest()


def cv_splits(task, folds, repeats, seed):
    if repeats == 1:
        return StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed) if task == "classification" else KFold(n_splits=folds, shuffle=True, random_state=seed)
    return RepeatedStratifiedKFold(n_splits=folds, n_repeats=repeats, random_state=seed) if task == "classification" else RepeatedKFold(n_splits=folds, n_repeats=repeats, random_state=seed)


def evaluate(dataset_name, task, X, y, repeat, fold, train_idx, test_idx, seed):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    for model_name, model in models(task, seed).items():
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        fit_seconds = time.perf_counter() - t0
        predict = model.predict_proba if task == "classification" else model.predict
        predict(X_test[:min(32, len(X_test))])  # Warm-up, non incluso nel tempo
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            predictions = predict(X_test)
            times.append(time.perf_counter() - t0)
        if task == "classification":
            labels = np.unique(y_train)
            if len(labels) == 2:
                metric_name = "roc_auc"
                positive_col = list(model.classes_).index(labels[-1])
                metric = roc_auc_score(y_test, predictions[:, positive_col])
            else:
                metric_name = "roc_auc_ovr_macro"
                metric = roc_auc_score(y_test, predictions, labels=model.classes_, multi_class="ovr", average="macro")
        else:
            metric_name = "rmse"
            metric = float(np.sqrt(mean_squared_error(y_test, predictions)))
        yield {
            "dataset": dataset_name, "task": task, "repeat": repeat, "fold": fold,
            "seed": seed, "model": model_name, "metric_name": metric_name, "metric": float(metric),
            "fit_seconds": float(fit_seconds), "predict_seconds": float(np.median(times)),
            "pickle_kib": len(pickle.dumps(model, protocol=pickle.HIGHEST_PROTOCOL)) / 1024,
            "n_train": len(X_train), "n_test": len(X_test), "n_features": X.shape[1],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="2 dataset, 2 fold, 1 ripetizione: 16 risultati")
    parser.add_argument("--output", type=Path, help="Percorso del CSV, se desiderato")
    args = parser.parse_args()
    folds, repeats, cv_seed = (2, 1, 20261009) if args.quick else (5, 3, 20261009)
    output = args.output or Path("results") / ("benchmark_cv_quick.csv" if args.quick else "benchmark_cv_full.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    items = datasets(args.quick)
    meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(), "cpu": platform.processor(),
        "git_commit": git_commit(), "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "packages": {name: pkgver(name) for name in (
            "codadapt", "numpy", "scipy", "pandas", "scikit-learn", "lightgbm", "threadpoolctl")},
        "protocol": {
            "kind": "cross_validation_ripetuta", "folds": folds, "repeats": repeats, "cv_seed": cv_seed,
            "threads": 1, "tuning": "nessuno", "fit_timing": "una misura per fold",
            "prediction_timing": "mediana di 5 dopo warm-up",
            "limiti": "quattro piccoli dataset scikit-learn; confronto esplorativo, non validazione indipendente",
        },
        "datasets": [
            {"name": name, "task": task, "rows": len(y), "features": X.shape[1], "sha256": fingerprint(X, y)}
            for name, task, X, y in items
        ],
    }
    metadata_path = output.with_suffix(".json")
    metadata_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    total = len(items) * folds * repeats * 4
    count = 0
    with threadpool_limits(limits=1), output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        try:
            for name, task, X, y in items:
                cv = cv_splits(task, folds, repeats, cv_seed)
                for index, (train_idx, test_idx) in enumerate(cv.split(X, y)):
                    repeat, fold = divmod(index, folds)
                    seed = cv_seed + index
                    for row in evaluate(name, task, X, y, repeat + 1, fold + 1, train_idx, test_idx, seed):
                        writer.writerow(row)
                        handle.flush()
                        count += 1
                        print(f"[{count}/{total}] {name} rip={repeat + 1} fold={fold + 1} "
                              f"{row['model']}: {row['metric_name']}={row['metric']:.5f}", flush=True)
        except Exception:
            print(f"ERRORE: risultati parziali conservati in {output}", file=sys.stderr)
            raise
    print(f"\nCompletato: {count} righe in {output}")
    print(f"Metadati: {metadata_path}")
    print("Nota: nessun tuning; la cross-validation non rende indipendente il benchmark.")


if __name__ == "__main__":
    main()
