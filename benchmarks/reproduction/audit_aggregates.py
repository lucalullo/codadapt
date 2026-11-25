"""Verify the recorded aggregate evidence, never train or access source data."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "benchmarks/data"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def authenticated(relative):
    manifest = ROOT / "release/MANIFEST.json"
    expected = (ROOT / "release/SHA256SUMS.txt").read_text().split()[0]
    require(hashlib.sha256(manifest.read_bytes()).hexdigest() == expected, "Manifest digest mismatch")
    receipt = json.loads(manifest.read_text(encoding="utf-8"))["files"][relative]
    data = (ROOT / relative).read_bytes()
    require(len(data) == receipt["bytes"] and hashlib.sha256(data).hexdigest() == receipt["SHA256"], f"Aggregate integrity mismatch: {relative}")
    return data.decode("utf-8")


def csv_records(name):
    return list(csv.DictReader(authenticated(f"benchmarks/data/{name}").splitlines()))


def close_printed(printed, exact):
    value = Decimal(printed)
    # Printed tables round to the decimal places actually retained, not an invented CI.
    tolerance = Decimal(1).scaleb(value.as_tuple().exponent) / 2
    return abs(value - Decimal(str(exact))) <= tolerance + Decimal("1e-10")


def verify(slug=None):
    origins = json.loads(authenticated("benchmarks/reproduction/ORIGINS.json"))["origins"]
    names = {o["dataset"] for o in origins if slug is None or slug == o["slug"]}
    require(bool(names), f"Unknown dataset: {slug}")
    measurements = csv_records("measurements.csv")
    pairs = csv_records("paired_comparisons.csv")
    inventory = csv_records("datasets.csv")
    exact = json.loads(authenticated("benchmarks/data/full_precision.json"))["records"]
    keys = {(x["dataset"], x["algorithm"]): x for x in exact}
    require(len(keys) == len(exact) == len(measurements) == 97, "Measurement coverage mismatch")
    require(len(origins) == len(inventory) == 14, "Origin coverage mismatch")
    require(set(o["dataset"] for o in origins) == set(o["dataset"] for o in inventory), "Origin identities mismatch")
    require(Counter(p["status"] for p in pairs) == {"exploratory_favorable": 14, "inconclusive": 40, "exploratory_unfavorable": 29, "missing": 1}, "Original comparison status mismatch")
    metric_map = {"accuracy": "accuracy", "balanced_accuracy": "balanced_accuracy", "macro_f1": "macro_F1", "roc_auc": "ROC_AUC", "logloss": "logloss", "fpr_native_threshold": "FPR_native_threshold", "rmse": "RMSE", "mae": "MAE"}
    cost_map = {"fit_prep_s": ("fit_including_preprocessing_s", 1), "job_wall_s": ("complete_job_wall_s", 1), "cold_snapshot_s": ("cold_start_snapshot_s", 1), "b1_ms": ("raw_batch1_s", 1000), "b3000_ms": ("raw_batch3000_s", 1000), "rows_per_s": ("raw_batch3000_rows_per_s", 1), "load_ms": ("file_hash_unpickle_load_s", 1000), "model_bytes": ("model_B", 1), "train_rss_mib": ("train_process_peak_RSS_B", 1/1048576), "tree_peak_mib": ("controller_tree_peak_RSS_B", 1/1048576)}
    resident_map = {"loaded_rss_mib": ("process_RSS_loaded_B", 1/1048576), "load_retained_kib": ("retained_traced_unpickle_B", 1/1024), "load_peak_kib": ("peak_traced_unpickle_B", 1/1024), "os_peak_mib": ("process_OS_peak_B", 1/1048576)}
    compared = 0
    for row in measurements:
        if row["dataset"] not in names:
            continue
        source = keys[(row["dataset"], row["algorithm"])]
        for column, metric in metric_map.items():
            if row[column] not in ("ND", ""):
                require(close_printed(row[column], source["metrics"][metric]), f"Metric mismatch: {row['dataset']}/{row['algorithm']}/{column}")
                compared += 1
        for mapping, obj in ((cost_map, source["cost"]), (resident_map, source["cost"]["resident_RSS"])):
            for column, (key, scale) in mapping.items():
                if row[column] not in ("ND", ""):
                    require(close_printed(row[column], obj[key] * scale), f"Cost mismatch: {row['dataset']}/{row['algorithm']}/{column}")
                    compared += 1
    selected = [p for p in pairs if p["dataset"] in names]
    observed = {(r["dataset"], r["algorithm"]): r for r in measurements}
    for pair in selected:
        if pair["status"] == "missing":
            require((pair["dataset"], pair["competitor"]) not in keys, "Missing comparison has a measurement")
        else:
            require((pair["dataset"], pair["competitor"]) in keys, "Paired comparison missing its measurement")
            own = observed[(pair["dataset"], "CodAdapt 2.1.0")]
            other = observed[(pair["dataset"], pair["competitor"])]
            for column, field, row in (("codadapt_primary", "primary_metric", own), ("competitor_primary", "primary_metric", other), ("codadapt_loss", "loss_metric", own), ("competitor_loss", "loss_metric", other)):
                require(Decimal(pair[column]) == Decimal(row[pair[field]]), f"Paired numeric value mismatch: {pair['comparison_id']}/{column}")
                compared += 1
    return {"status": "PASS_AGGREGATE_AUDIT_ONLY", "datasets": sorted(names), "measurement_rows": sum(r["dataset"] in names for r in measurements), "numeric_values_checked": compared, "paired_outcomes": dict(Counter(p["status"] for p in selected)), "aggregate_sha256": hashlib.sha256((DATA / "full_precision.json").read_bytes()).hexdigest(), "exact_original_fit_reproduced": False, "new_fits": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", help="Dataset slug from ORIGINS.json (default: all)")
    args = parser.parse_args()
    print(json.dumps(verify(args.dataset), indent=2))
