# Native selection: bounded decision before new measurements

Scope: Windows x64 / CPython 3.10.22 and 3.14.10, their exact already installed
2.1.0 wheels and dependency pins. No fit, source modification, auto monkeypatch,
scientific dataset or protected holdout. Reuse the three trusted synthetic
engineering models and reconstruct the exact probe input seed 1729.

The existing G3 benefit criterion is retained: at least 20% end-to-end reduction
for multiclass batch 2048; median and p95 for batches 1/32 at most 1.05x Python;
whole-process peak RSS and serialized payload at most 1.05x Python. Additionally
record batch 65536 and reject extension if any measured task/batch has median or
p95 above 1.05x; no threshold change or retry to rescue a failed measurement.

Nine fresh paired processes per profile, alternating backend order; one numerical
thread; 30 prediction calls per cell for batches 1,32,2048 and five at 65536 after
one warmup. Resident ndarray inputs, three tasks. Report each sample, process
median/p95 and aggregate ratios (median of the nine process summaries), and rows
per second. Whole-process Windows peak working set includes imports, models,
queries, bindings and predictions; it is not isolated native heap or model RAM.
Different dependency profiles are never pooled. At most 300 seconds / 1.5 GiB
owned tree per profile. No concurrent Codex build/test/benchmark during timing.

Every process verifies predicted labels/values, probabilities and decision scores
at each batch via output hashes, and serialized model state before/after. Python
and native pairs must match dtype/shape/bytes exactly. Existing actual installed
full-suite boundary, robustness, persistence and API evidence is reused because
the product files are unchanged. This benchmark adds serial performance evidence,
not another claim of full platform qualification.

Automatic selection remains unchanged during evaluation. `_inference.py` is a
member of the serving source contract; any edit changes its producer identity.
The user expressly requires unchanged historical-export compatibility absent an
authorized verified migration. Therefore successful explicit-native performance
does not alone authorize a guard edit that invalidates current 2.1.0 exports.
Report performance and compatibility decisions separately. Preserve Python auto
on 3.10/3.14 unless all required gates, including persistence, are satisfied.

Source-contract SHA256 before work:
940f9fd84198feb1f6d6fb1a515ca2028a5f7a9ca65c4f98c8713391f58f462b.
No algorithmic benefit, training speedup, general accuracy, Linux/macOS support,
or automatic acceleration may be inferred from these finite inference timings.
