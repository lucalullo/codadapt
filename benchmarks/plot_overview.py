"""Build a descriptive summary from recorded benchmark CSVs; no model execution."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "overview"


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value):
    return f"{value:.6g}"


def chart(rows, filename, title, subtitle, ratio_key):
    """Use a symmetric log-ratio scale: left is numerically better/smaller."""
    width = 920
    row_height = 35
    height = 145 + len(rows) * row_height
    logs = [math.log2(row[ratio_key]) for row in rows]
    extent = max(1, math.ceil(max(map(abs, logs))))
    center, half = 505, 210
    esc = escape
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f'<title>{esc(title)}</title>',
        f'<desc>{esc(subtitle)} Lower ratios indicate a favorable numerical direction; not a significance test.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<g font-family="Arial, Helvetica, sans-serif" fill="#172638">',
        f'<text x="24" y="32" font-size="21" font-weight="bold">{esc(title)}</text>',
        f'<text x="24" y="55" font-size="12" fill="#475569">{esc(subtitle)}</text>',
        '<text x="24" y="83" font-size="12" font-weight="bold">Dataset / metric</text>',
        f'<text x="{center-half}" y="83" font-size="11" fill="#246b83">Lower ratio</text>',
        f'<text x="{center+half}" y="83" font-size="11" text-anchor="end" fill="#9b5622">Higher ratio</text>',
        '<text x="896" y="83" font-size="12" font-weight="bold" text-anchor="end">Ratio</text>',
    ]
    for i, (row, log) in enumerate(zip(rows, logs)):
        y = 93 + i * row_height
        if i % 2 == 0:
            svg.append(f'<rect x="18" y="{y}" width="884" height="{row_height}" fill="#f3f6f9"/>')
        label = f'{row["dataset"]} / {row["metric"]}' if ratio_key == "quality_ratio" else row["dataset"]
        svg.append(f'<text x="24" y="{y+23}" font-size="12">{esc(label)}</text>')
        svg.append(f'<line x1="{center}" y1="{y}" x2="{center}" y2="{y+row_height}" stroke="#94a3b8" stroke-dasharray="3 3"/>')
        end = center + log / extent * half
        color = "#246b83" if log < 0 else "#b76e32" if log > 0 else "#64748b"
        svg.append(f'<line x1="{center}" y1="{y+17}" x2="{end:.2f}" y2="{y+17}" stroke="{color}" stroke-width="8" stroke-linecap="round"/>')
        svg.append(f'<circle cx="{end:.2f}" cy="{y+17}" r="5" fill="{color}"/>')
        svg.append(f'<text x="896" y="{y+22}" font-size="12" text-anchor="end">{row[ratio_key]:.4g}x</text>')
    y = 93 + len(rows) * row_height
    for tick in sorted({-extent, 0, extent}):
        x = center + tick / extent * half
        svg.append(f'<text x="{x:.2f}" y="{y+17}" font-size="11" text-anchor="middle">{2.0**tick:.4g}x</text>')
    svg.append(f'<text x="{center}" y="{y+36}" font-size="11" text-anchor="middle" fill="#475569">Log-ratio axis | 1x = same recorded value | descriptive, not a statistical test</text>')
    svg.append('</g></svg>')
    (OUT / filename).write_text("\n".join(svg) + "\n", encoding="utf-8")


def summarize(rows, project, scope, cost_label):
    OUT.mkdir(exist_ok=True)
    for row in rows:
        # Invert higher-is-better scores so all chart ratios have the same direction.
        value, baseline = row["value"], row["baseline"]
        row["quality_ratio"] = baseline / value if row["higher"] else value / baseline
        row["size_ratio"] = row["bytes"] / row["baseline_bytes"]
    with (OUT / "summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = [f"# {project} benchmark summary", "", scope, "", "## Predictive performance", "", "| Dataset | Primary metric | Project | Best eligible external baseline | Baseline value | Directional ratio |", "|---|---|---:|---|---:|---:|"]
    for r in rows:
        lines.append(f'| {r["dataset"]} | {r["metric"]} ({"higher" if r["higher"] else "lower"} is better) | {number(r["value"])} | {r["comparator"]} | {number(r["baseline"])} | {number(r["quality_ratio"])} |')
    lines += ["", "The quality ratio is project / baseline for lower-is-better loss, and baseline / project for higher-is-better scores. A ratio below one favors the project numerically; this is not a confidence interval or an equivalence test. Ties are broken alphabetically for choosing the resource comparator.", "", "## Computational efficiency", "", f"| Dataset | Quality-selected comparator | {cost_label}: project / baseline | Training RSS MiB: project / baseline | Serialized KiB: project / baseline |", "|---|---|---:|---:|---:|"]
    for r in rows:
        lines.append(f'| {r["dataset"]} | {r["comparator"]} | {number(r["cost"])} / {number(r["baseline_cost"])} | {number(r["rss"])} / {number(r["baseline_rss"])} | {number(r["bytes"]/1024)} / {number(r["baseline_bytes"]/1024)} |')
    lines += ["", "The comparator is selected by predictive quality, not by resource cost. Training and RSS definitions are protocol-specific; do not compare the two repositories as if they used a common workload. Stored bytes are not loaded RAM. See the [benchmark overview](../README.md) for coverage, detailed timing and scientific limitations.", "", "[Machine-readable summary](summary.csv). Regenerate from the recorded source CSV with `python benchmarks/plot_overview.py`. No new measurements are generated.", ""]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    chart(rows, "quality.svg", f"{project} | Predictive quality", "Directional ratio against the best eligible external primary-metric baseline; see summary table for raw scores.", "quality_ratio")
    chart(rows, "model_size.svg", f"{project} | Serialized model size", "Project bytes / bytes of the same quality-selected comparator; not loaded RAM.", "size_ratio")


def main():
    raw = read_csv(ROOT / "data/measurements.csv")
    groups = defaultdict(list)
    for r in raw:
        groups[r["dataset"], r["task"]].append(r)
    rows = []
    order = {"binary": 0, "multiclass": 1, "regression": 2}
    metrics = {"binary": ("roc_auc", "ROC-AUC", True), "multiclass": ("balanced_accuracy", "Balanced accuracy", True), "regression": ("rmse", "RMSE", False)}
    for (dataset, task), entries in sorted(groups.items(), key=lambda item: (order[item[0][1]], item[0][0])):
        key, metric, higher = metrics[task]
        own, = [r for r in entries if r["algorithm"] == "CodAdapt 2.1.0"]
        eligible = [r for r in entries if r is not own and r[key] not in ("", "ND")]
        best = min(eligible, key=lambda r: ((-1 if higher else 1)*float(r[key]), r["algorithm"]))
        rows.append(dict(dataset=dataset, task=task, metric=metric, higher=higher, value=float(own[key]), comparator=best["algorithm"], baseline=float(best[key]), cost=float(own["fit_prep_s"]), baseline_cost=float(best["fit_prep_s"]), rss=float(own["train_rss_mib"]), baseline_rss=float(best["train_rss_mib"]), bytes=float(own["model_bytes"]), baseline_bytes=float(best["model_bytes"])))
    assert len(rows) == 14
    summarize(rows, "CodAdapt 2.1.0", "Fixed configurations on the 14 development origins; aggregate printed-precision measurements. Select the numerically best available external comparator for each primary metric. Missing results remain missing; 2.2.0 technical evidence is separate.", "Fit + preparation s")


if __name__ == "__main__":
    main()

