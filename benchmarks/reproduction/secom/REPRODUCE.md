# Reproduce: SECOM

**Evidence level B0 - public-source identification and aggregate reproduction; original refit blocked.**

## Source and access

- Recorded origin: `UCI179`; [publisher catalogue](https://archive.ics.uci.edu/dataset/179/secom).
- Public UCI catalogue (CC BY 4.0 stated).
- No source data, fitted real-data models, protected targets or split indices are distributed here. A catalogue URL is not authentication of the exact historical asset. Do not treat the current download as the original fit input.

## Recorded experiment

| Field | Recorded value |
|---|---|
| CodAdapt version | 2.1.0 |
| Task | binary |
| CORE / VALID rows | 201 / 279 |
| VALID groups | 10 |
| Features / categorical | 590 / 0 |
| Original data SHA-256, version and row order | Not available in this source bundle |
| Original seed, group-to-role indices and exact estimator parameters | Not available in this source bundle |

## Reproduce the available evidence

From the repository root, run:

```bash
python benchmarks/reproduction/audit_aggregates.py --dataset secom
python benchmarks/plot_overview.py
```

The first command authenticates aggregate inputs against the bundled manifest and checks the selected dataset's recorded values and paired outcomes. The second regenerates the comparative overview from aggregate values. Neither command trains a model, downloads a dataset or establishes statistical equivalence. See [full results](../../RESULTS.md), [paired comparisons](../../COMPARISONS.md) and [methodology](../../METHODOLOGY.md).

## Requirements for an exact refit

Recover timestamp/group assignment, inclusion and feature exclusion rules, and original operating threshold. In addition, recover the versioned asset SHA-256, row identities, full role mapping, original split seed, feature pipeline and exact estimator parameters from the original experiment records. Verify the applicable terms before obtaining or redistributing data. Use the original 2.1.0 learner and recorded dependency/hardware profile for comparable timings. A new split or a different estimator configuration is a new experiment, not a reproduction of the published table. No exact-fit command is asserted until these prerequisites are available.

[Reproducibility matrix](../../REPRODUCE.md).
