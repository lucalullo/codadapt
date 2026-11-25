# Benchmark reproducibility

This page separates source access, executable historical replay and numerical report reproduction. It does not claim that public availability alone makes an original experimental split reproducible.

## Evidence levels

| Level | Meaning |
|---|---|
| A | Exact fold inputs, seeds and runnable estimator recipe authenticated; refitting is possible with those inputs and the correct environment. |
| B | Data obtained separately under its terms, with authenticated asset and original split/configuration reconstruction sufficient for a refit. |
| B0 | Public catalogue identified, but original asset identity or complete role/configuration receipts unavailable. Aggregate verification and chart regeneration only. |
| C | Restricted/protected or otherwise inaccessible exact inputs; no refit offered. |

The 14-origin development benchmark is B0 throughout: source catalogues are identifiable, but no complete original competitive split/configuration or raw asset SHA-256 is present. The missing items are explicit, not guessed. No protected dataset is bundled, and no undocumented source is labelled restricted simply because it is absent. A separate historical classification panel has level-A fold-level evidence, staged from the original public assets rather than copied into this package. Exact hardware timing and fresh execution are not certified.

## Development origins (CodAdapt 2.1.0)

| Dataset | Task | Level | CORE / VALID | Source | Instructions |
|---|---|---|---:|---|---|
| Breast Cancer Wisconsin | binary | B0 | 274 / 171 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/15/breast+cancer+wisconsin+original) | [REPRODUCE](reproduction/breast-cancer-wisconsin/REPRODUCE.md) |
| Danish occupancy | binary | B0 | 3264 / 1280 | [Publisher catalogue](https://www.en.build.aau.dk/web/builddata/datasets) | [REPRODUCE](reproduction/danish-occupancy/REPRODUCE.md) |
| Denver trees | binary | B0 | 52 / 3372 | [Publisher catalogue](https://data.colorado.gov/Natural-Resources/Tree-Inventory-Denver/wz8h-dap6) | [REPRODUCE](reproduction/denver-trees/REPRODUCE.md) |
| SECOM | binary | B0 | 201 / 279 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/179/secom) | [REPRODUCE](reproduction/secom/REPRODUCE.md) |
| Statlog German Credit | binary | B0 | 426 / 267 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data) | [REPRODUCE](reproduction/german-credit/REPRODUCE.md) |
| Annealing | multiclass | B0 | 340 / 213 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/3/annealing) | [REPRODUCE](reproduction/annealing/REPRODUCE.md) |
| Forest Types | multiclass | B0 | 83 / 53 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/333/forest+type+mapping) | [REPRODUCE](reproduction/forest-types/REPRODUCE.md) |
| Glass | multiclass | B0 | 91 / 57 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/42/glass+identification) | [REPRODUCE](reproduction/glass/REPRODUCE.md) |
| Pen Digits | multiclass | B0 | 3199 / 1998 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/81/pen+based+recognition+of+handwritten+digits) | [REPRODUCE](reproduction/pen-digits/REPRODUCE.md) |
| Abalone | regression | B0 | 1781 / 1114 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/1/abalone) | [REPRODUCE](reproduction/abalone/REPRODUCE.md) |
| Automobile | regression | B0 | 84 / 54 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/10/automobile) | [REPRODUCE](reproduction/automobile/REPRODUCE.md) |
| Concrete | regression | B0 | 431 / 271 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) | [REPRODUCE](reproduction/concrete/REPRODUCE.md) |
| Edge task execution times | regression | B0 | 1236 / 502 | [Publisher catalogue](https://archive.ics.uci.edu/dataset/859/image+recognition+task+execution+times+in+mobile+edge+computing) | [REPRODUCE](reproduction/edge-task/REPRODUCE.md) |
| NYC Reservoir | regression | B0 | 588 / 252 | [Publisher catalogue](https://data.cityofnewyork.us/Environment/Current-Reservoir-Levels/zkky-n5j3) | [REPRODUCE](reproduction/nyc-reservoir/REPRODUCE.md) |

## Historical classification panel (separate evidence)

| Dataset | Level | Instructions |
|---|---|---|
| Music | A, original fold replay | [Historical recipe](historical/REPRODUCE.md#music) |
| Wireless | A, original fold replay | [Historical recipe](historical/REPRODUCE.md#wireless) |
| Rice | A, original fold replay | [Historical recipe](historical/REPRODUCE.md#rice) |

## Commands for the development report

```bash
python benchmarks/reproduction/audit_aggregates.py
python benchmarks/plot_overview.py
python benchmarks/plot_results.py
```

The audit uses the standard library. Detailed figures require NumPy and Matplotlib. These commands use aggregate tables only. They do not execute competitive fits. Regenerating charts can change presentation bytes; refresh the source manifest only after reviewing intentional edits. See [methodology](METHODOLOGY.md) and [provenance](data/provenance.json).

## Evidence development

Independent confirmation and a preregistered Pareto evaluation remain research objectives. No complete independent cohort, scheduled run or successful validation is claimed. Reproducibility work does not change any existing performance estimate or statistical classification.
