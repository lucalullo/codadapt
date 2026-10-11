# Benchmark Disclosure

The frozen blind NEW_EXTERNAL benchmark is the primary evidence for current
**0.2.0rc2** product positioning. Earlier external pilots are secondary/historical
evidence; development and transfer panels are research evidence. The library's
overall verdict is **PRODUCT_POSITION_MIXED**. Historical measurements below remain
available, but do not override the blind panel for current external claims.

## Frozen Blind External Benchmark

Dataset selection preceded metrics, and the protocol, source/row contracts,
splits, seeds, public constructors, baseline presets and resource limits were
frozen before fitting. There was **zero tuning** or test-based candidate selection.
The panel contains **16 NEW_EXTERNAL primary datasets**, **72 primary conditions**
and **381 frozen model jobs**: **380 SUCCESS** and **1 MEMORY_GUARD_REJECT**.
No backup dataset was activated. NEW_EXTERNAL means unseen within the recoverable
source history; missing early research catalogs prevent an unconditional novelty claim.

Frozen protocol SHA256 receipt:

```text
ac9f75d1ce64cd559f2a17224704dd92c9558bb0e3ccd2d8103096b8ee80b075
```

Raw-results freeze receipt SHA256:

```text
32327f640777b9910b47f6edaaca610cfef50bfd9f85e24a5c338dcec92ca697
```

### Primary quality and serialized size

All deltas below are **relative primary loss**, `100 × (candidate / reference − 1)`;
positive means worse quality. Ratios are **candidate / reference**, so smaller
means less storage or time. Values are rounded from the frozen final aggregates,
using paired condition ratios, a median within each source, then an equal-source
median. They are not ratios of pooled raw losses.

| Task | Model | Datasets | Median primary-loss delta | Median serialized ratio | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| Regression | CodAdaptRegressor Base | 5 | +2.412976% RMSE | 0.125392× | Slightly behind the reference on median RMSE |
| Regression | SafeBlendRegressor | 5 | −0.665536% RMSE | 0.120452× | Promising compact regression trade-off; uncertainty remains |
| Binary | CodAdaptClassifier | 6 | +9.364320% logloss | 0.111256× | Current blind quality gap |
| Multiclass | CodAdaptClassifier | 5 | +22.031308% logloss | 0.146041× | Current blind quality gap despite technical Shared-OVR validation |

**Preregistered baseline leader** means the reference chosen per source by the
frozen analysis rule: the complete mainstream baseline with the lowest median
primary loss among HistGradientBoosting, LightGBM, CatBoost and XGBoost. Ties within
1e-12 use that order. The rule was preregistered; the leader's identity was determined
after evaluation. It is a descriptive benchmark reference and may differ by dataset;
it was not used to tune or choose CodAdapt predictions. It is not necessarily HGB.

SafeBlend passed both the compact and strong compact **regression** gates, with
**n=5 datasets and a 95% confidence interval including zero**. Its relative RMSE
delta CI is **[−4.661698%, +27.999900%]**. The corresponding gain interval also
includes zero; a general regression advantage is not established. Base regression's
relative RMSE delta CI is **[−3.913731%, +47.635643%]**.

The compact gate requires median serialized ratio ≤0.35, median relative loss
degradation ≤5%, at least 70% of sources within 10%, and competitiveness in every
covered task. The strong gate requires ≤0.25, ≤3%, at least 75% within 5%, and the
same task condition. Base covers all 16 sources and **fails both overall gates**;
SafeBlend is a separate five-source regression candidate and **passes both**.
Task competitiveness requires median relative loss degradation ≤10%, at least
half of sources within 10%, and a candidate failure fraction ≤10%. Coverage must
reach 95% overall and 90% in each task. Missing comparisons retain the frozen
failure penalties rather than being silently dropped; some confidence bounds
are infinite. Passing a size/quality gate is not a test of statistical superiority.
SafeBlend was not selected per dataset using TEST. Its validation branch was BASE
in 14 conditions and BLEND in seven; this does not measure avoided harm or guarantee
test improvement.

### Frozen systems context

Fit and warm inference include raw-input preprocessing through the complete
pipeline. The latency ratios use per-job p50 measurements, then the same paired,
source-first aggregation. All four frozen batch sizes are shown.

| Task / model | Fit ratio | Batch 1 latency | Batch 32 latency | Batch 1k latency | Batch 100k latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Regression / Base | 0.199636× | 0.630131× | 0.604165× | 0.517308× | 0.404786× |
| Regression / SafeBlend | 1.503666× | 0.914634× | 1.030971× | 0.847464× | 0.828687× |
| Binary / Base | 0.103710× | 0.667655× | 0.693234× | 0.645957× | 0.387222× |
| Multiclass / Base | 0.107231× | 1.389681× | 1.677359× | 1.517275× | 7.257287× |

Compact serialized models are a consistently observed strength on this tested
panel. They are not a guarantee of lower deep memory, peak RSS or latency.
In particular, multiclass inference and wide workloads can be expensive.
Deep-memory accounting is a native-heap lower bound; opaque native allocations
make it unsuitable for a universal RAM comparison. Process-tree peak RSS was
measured separately. No memory/latency/full Pareto counts are claimed:
the frozen outputs mark these **NOT_PREREGISTERED / NA**, because dominance axes,
tolerances and latency-batch definitions were not frozen. NA does not mean zero.

### Blind methodology and limits

| Task | Independent sources | Conditions | UCI source IDs |
| --- | ---: | ---: | --- |
| Regression | 5 | 21 | 382, 483, 511, 1175, 312 |
| Binary | 6 | 30 | 1150, 915, 967, 759, 451, 508 |
| Multiclass | 5 | 21 | 253, 333, 366, 763, 862 |

Five frozen conditions were used per source except the two explicit author
official holdouts, each evaluated once. Repeated conditions are not independent
datasets. Random/group conditions used seeds 784201–784205; official and
forward-time conditions used fixed model seeds without randomizing chronology.
Frozen outer group/time/official isolation was preserved. Native internal stopping
remained unchanged and TRAIN-only; it is not claimed group/time-aware.

Native estimators used public defaults with fixed random states. Baseline presets
were identical across tasks: HGB used 100 iterations, learning rate 0.1, 31 leaves,
zero L2 and automatic early stopping; LightGBM used 100 estimators, learning rate
0.1 and 31 leaves; CatBoost used 300 iterations, depth 6 and learning rate 0.05;
XGBoost used 300 estimators, depth 6, learning rate 0.05, histogram trees, full row/
column sampling and categorical support. Other parameters retained their frozen
defaults. LightGBM, CatBoost and XGBoost used **six threads**; accessories used at
most four. Public native defaults, including SafeBlend's one-thread default,
were preserved. One heavy process ran at a time.

Baseline adapters fitted numeric imputation/missing indicators and categorical
vocabularies only on TRAIN. HGB used its frozen categorical cap/OTHER mapping;
CatBoost used its string/category contract; XGBoost used the fixed training-label
wrapper and class order. Native category, missing and unseen handling remained
unchanged. Full heldout row alignment, natural-unit metrics and pickle/joblib
prediction equivalence were replay-verified for all **380 SUCCESS** jobs.

The environment was one Windows host, AMD Ryzen 7 255, 32 GB RAM, Python 3.12.14,
NumPy 2.3.5, pandas 2.2.3, SciPy 1.16.2, scikit-learn 1.8.0, LightGBM 4.7.0,
CatBoost 1.2.10 and XGBoost 3.4.1. Warm and cache-pressure timing used 20 alternating
repetitions per batch. Cache pressure is a proxy, not full CPU/OS cache eviction;
first-process-call latency was recorded separately. Oversized batches explicitly
cycled heldout rows and need not contain 100k unique samples.

The single **MEMORY_GUARD_REJECT** occurred in the LightGBM/MicroMass systems
measurement and remains a **coverage/system limitation** in the frozen denominator.
All CodAdapt jobs completed. No dataset replacement or larger budget was used.
The per-job supervisor retained its 10 GiB target, 12 GiB hard budget and 3,600-second
timeout. The previously documented Covtype-like large-N safe-memory exclusion
remains a separate deployment boundary; it was not part of these 16 sources.

Source-bootstrap CIs used 10,000 draws with seed 784299. Small source counts
(5 regression, 6 binary, 5 multiclass), overlapping split conditions and conservative
failure penalties limit precision. No confirmed regime or universal niche is
inferred: the frozen protocol supplied no regime-support threshold. Performance
depends on domain, hardware and protocol. No historical sources were pooled into
these primary statistics, and no algorithmic research or default change follows
automatically from this documentation update.

## Historical 0.1.0 engineering comparison

CodAdapt 0.1.0 was experimental software. Its release comparison is intended to describe observed
trade-offs, not to claim general superiority over established tabular models.

The frozen release candidate was compared with HistGradientBoosting and budget-matched LightGBM on
12 datasets and five shared splits per dataset (240 valid runs). Nine datasets were synthetic and
three were scikit-learn real datasets. Raw-input preprocessing was included in the latency protocol.

Ratios below are `LightGBM / CodAdapt`; values above one favor CodAdapt for speed or compactness.

| Result | Value |
| --- | ---: |
| Predictive-quality mean wins | 0 / 12 |
| End-to-end training-time median wins | 5 / 12 |
| Raw-input inference-latency median wins | 10 / 12 |
| Retained model-memory wins | 12 / 12 |
| Median fit-speed ratio | 0.887x |
| Median inference-speed ratio | 1.258x |
| Median retained-memory ratio | 8.830x |
| Stable predictive wins | none |
| Four-dimensional Pareto dominance | none |

The measured candidate therefore showed a useful low-memory / low-latency profile, but no general
predictive-quality advantage over budget-matched LightGBM. The median fit ratio also favored
LightGBM overall.

These results are hardware-, dataset-, version-, split-, thread-, and workload-dependent. New users
should benchmark on their own data before drawing conclusions.

## Public sanity runner

The repository includes a deliberately small, self-contained sanity benchmark using built-in
scikit-learn and synthetic datasets:

```bash
python benchmarks/run_benchmarks.py --quick
```

The public runner compares native CodAdapt with sklearn HistGradientBoosting only.
The optional benchmark extra supplies system measurement tooling, not LightGBM:

```bash
python -m pip install -e ".[benchmark]"
python benchmarks/run_benchmarks.py --output benchmark_results/results.csv
```

The public runner is not an exact reproduction of the frozen release protocol; it exists so users
can quickly compare quality, fit time, prediction time, and serialized model size in their own
environment.

## Experimental EBM compiler — frozen local validation

This subsequent compiler validation is separate from the native v0.1.0 comparison
above. It evaluates the opt-in `codadapt.experimental` compiler, not a change to the
native learner or default. The compiler remains experimental and non-default.

### Panel and protocol

The frozen panel used **12 known datasets × 3 fixed splits = 36 cases per environment**:
Adult, SDSS STAR, Breast Cancer and binary Wine classification; Diabetes, California,
Superconduct, SGEMM, Buzz, Diamonds, House Sales and Green Taxi Tips regression.
Native Windows and WSL/Linux ran on the **same physical AMD Ryzen 7 255 host** with
32 GB installed RAM (about 15.6 GB exposed to WSL), using a **one-thread protocol**.
This is software-environment replication, not independent-hardware validation or new
dataset confirmation.

Windows used Python 3.12.14; WSL Ubuntu 24.04.4 used Python 3.12.3. Both used NumPy
2.3.5, pandas 2.2.3, SciPy 1.16.2, scikit-learn 1.8.0 and interpret-core 0.7.8.
The fixed additive EBM recipe used `interactions=0`, `max_bins=256`, `outer_bags=4`,
`max_rounds=2000`, `learning_rate=0.04`, `smoothing_rounds=200`,
`early_stopping_rounds=50`, `n_jobs=1` and seeds 44001–44003. The frozen compiler was
the public NumPy runtime; these were newly fitted teachers for that validation,
not a replay of the original research teacher objects.

Timing used three interleaved blocks, three warmups and 15 repetitions. Blocks are
not independent hardware or temporal-session replications. Paired session ratios
were aggregated by median across splits within each source, then by equal-source
median, P90 and worst ratio. The same source-balanced aggregation applies to memory.

### Quality / fidelity

Teacher-to-compiled verification passed **36/36 cases on Windows and 36/36 on WSL**.
Raw binary scores and regression predictions were bitwise identical; AUC, RMSE and
MAE deltas were zero on the measured data. The largest absolute log-loss delta was
approximately 1.86e-15, within the frozen metric tolerance.

Cross-OS raw scores/regression predictions and class labels were also bitwise identical.
Probability differences reached **2.22e-16**, within the frozen compiler contract
`atol=1e-15, rtol=0`. Numerical equivalence is not probability-bitwise equality:
strict cross-OS checks failed for the 12 classifiers in each transfer direction,
while the 24 regressors passed. These bitwise failures remain recorded; they are
not numerical-fidelity failures and the tolerance was not changed. The overall
frozen validation verdict remains mixed rather than an unconditional portability pass.

### Memory

Ratios here and in the latency table are **compiled / EBM**, unlike the native
comparison above. Smaller values favor the compiled model.

| Model-memory measure | Windows median | WSL median | P90, both OS | Worst, both OS |
| --- | ---: | ---: | ---: | ---: |
| Deep retained memory | 0.195x | 0.195x | 0.308x | 0.390x |
| Serialized size | 0.236x | 0.236x | 0.252x | 0.265x |

The reciprocals of the unrounded median ratios are approximately **5.13x deep** and
**4.24x serialized** compression factors. These are descriptive reciprocals, not
separately aggregated median compression factors or universal memory guarantees.
Deep retained memory counts the deduplicated Python/array object graph, not every
native allocation. Whole-job peak RSS included inputs and multiple models, so an
isolated compiled/teacher peak-RSS ratio cannot be inferred.

### Latency

**Ratio >1 means compiled is slower than EBM.** All measured batch sizes and both
environments are shown; the favorable Windows batch100k median is not a general claim.

| Batch | Sources | Windows median | Windows P90 | Windows worst | WSL median | WSL P90 | WSL worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 12 | 2.703x | 3.236x | 3.319x | 2.533x | 3.356x | 3.387x |
| 32 | 12 | 2.684x | 2.839x | 2.906x | 2.621x | 2.929x | 3.116x |
| 1,000 | 12 | 1.307x | 2.088x | 2.273x | 1.484x | 1.985x | 2.824x |
| 100,000 | 9 | 0.926x | 3.897x | 5.416x | 1.115x | 1.996x | 2.739x |

The batch100k comparison covers nine eligible sources under the frozen rule and uses
labeled cyclic replay where needed; it does not always represent 100k unique rows.
**The historical single-row speed advantage did not replicate.** A general
inference-speed advantage is not established, and no universal batch crossover has
been demonstrated. Differences from earlier research timings cannot be attributed
to the OS alone: teacher recipe, cohort and runtime/input paths also differed.

### Standalone

Loading and inference passed **36/36 cases in a local Windows environment with
interpret physically absent**. Compiled artifacts retain no teacher; CodAdapt and
its normal runtime dependencies are still needed. WSL standalone checks blocked
teacher imports, while interpret remained installed in the fitting environment.
Cross-OS loading succeeded even where probability-bitwise checks failed.

This supports compact standalone deployment within the verified contract, not
compatibility with every future platform, package version or hardware configuration.
Teacher training remains an upstream cost. See the [compiler contract](docs/EBM_COMPILER.md)
for supported models, schemas, mandatory verification and explicit `REJECT` behavior.

## Native multiclass Shared OVR — frozen engineering transfer

Current working tree 0.2.0rc2 adds automatic single-label multiclass classification.
The frozen transfer compared9 real UCI datasets ×3 identical splits against K
independently fitted native CodAdapt binary heads, with the same parameters,
training/validation rows and normalized-sigmoid probability contract.

| Shared artifact / independent OVR | Transfer source median |
|---|---:|
| Complete fit including finalization |0.605×|
| Serialized model bytes |0.662×|
| Deep retained memory, deduplicated owners |0.232×|
| Inference latency, batch1k |0.334×|

Logits, probabilities, decisions and task metrics were exact-equivalent. These
ratios describe this single-host, one-thread panel; they are not a claim of better
quality than boosting, a speed guarantee or hardware-independent scaling. The
separate productization panel contained four >15% workload timing flags relative
to the earlier shared prototype. Fresh public-port timing is recorded separately;
no historical training-only or composed fit clock is relabeled as a fresh fit.
The binary and regression recipes, experimental EBM compiler and SafeBlend are unchanged.

### Current public-port systems replication

A fresh matched six-case panel (Iris, Car, Digits, Dry Bean, Hand Postures and
Urban Land Cover; the same frozen train/validation/test rows) measured complete
fit plus final dump and seven alternating warm prediction repeats. One thread
was used on the local Windows host; batch100k uses labeled cyclic replay.

| Public port / independent native OVR | Six-case median |
|---|---:|
| Complete fit |0.579×|
| Serialized bytes |0.636×|
| Owner-aware deep memory |0.214×|
| Inference latency, batch1 /32 /1k /100k |0.319× /0.300× /0.322× /0.374×|

Against the frozen shared prototype, fit was0.986×, deep memory1.000× and
inference1k0.993×. All three arms were prediction-equivalent. The original Dry
Bean fit observation was1.496× the prototype and remains an explicit >15% flag;
its separate fixed-repeat cost investigation is not substituted into this table.
Historical timing flags are retained. These results establish faithful engineering
transfer on this panel, not universal workload or independent-hardware guarantees.

## External leakage-audited product qualification

This earlier pilot is secondary/historical evidence. Current product positioning
uses the [frozen blind panel](#frozen-blind-external-benchmark) above; the pilot's
two-source binary estimate is not the current headline. Its results are retained
without changing their original HGB reference or aggregation.

This separate frozen product pilot evaluated the current **0.2.0rc2** public
estimators on **6 real datasets, 11 evaluation units and 36 valid fitted runs**.
Source provenance, feature/target contracts, seeds and train/test row indices
were frozen before fitting. There was **no tuning** or test-based model selection.
CodAdapt used public defaults with frozen random states; the references were
Dummy and a fixed sklearn HistGradientBoosting (HGB) preset. HGB's categorical
mapping was fitted only on training rows. This is a small external pilot, not a
comparison with the best tuned model for every dataset.

Each evaluation unit used the same outer training/test rows for all estimators.
The three regression units compared CodAdaptRegressor, the separate opt-in
SafeBlendRegressor, Dummy and HGB. The four binary and four multiclass units each
compared CodAdaptClassifier, Dummy and HGB. The micro gas turbine used one official
holdout; DARWIN used two stratified random splits, and the remaining four sources
used two frozen group splits. Identical-profile groups were isolated where entity
identifiers were unavailable; this cannot prove the
independence of hidden entities. Source/split leakage was audited within these
contracts, not certified absent under every possible deployment scenario.

The local Windows pilot used an AMD Ryzen 7 255 host with 32 GB RAM, Python
3.12.14, NumPy 2.3.5, pandas 2.2.3, SciPy 1.16.2 and scikit-learn 1.8.0, with
four threads and one heavy process at a time. This is not independent-hardware
confirmation. None of the earlier native or compiler panels above is replaced.

### Dataset-specific predictive results

Absolute values are arithmetic means of the frozen split metrics for each source
(one official split for the turbine, two splits otherwise). Relative delta is the
mean of the **paired split-relative deltas**, `100 × (CodAdapt loss / HGB loss − 1)`;
it is not generally the ratio of the displayed absolute means. Lower RMSE and
logloss are better, so negative deltas favor CodAdapt. RMSE units differ by source.

| Task | Dataset | Model | Primary metric | CodAdapt | HGB | Relative delta | Interpretation |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| Regression | Micro gas turbine | CodAdaptRegressor | RMSE | 374.213636 | 376.755515 | −0.674676% | Near HGB on the official experiment holdout |
| Regression | Micro gas turbine | SafeBlendRegressor | RMSE | 373.218021 | 376.755515 | −0.938936% | Separate opt-in result, near HGB |
| Regression | Soybean cultivars | CodAdaptRegressor | RMSE | 545.997985 | 554.687029 | −1.504930% | Favorable mean versus HGB; did not consistently improve on Dummy |
| Regression | Soybean cultivars | SafeBlendRegressor | RMSE | 533.728824 | 554.687029 | −3.746854% | Separate opt-in result; same Dummy/group-shift caveat |
| Binary | DARWIN | CodAdaptClassifier | Logloss | 0.412124771 | 0.201464048 | +126.980810% | Weak relative to HGB on both splits |
| Binary | Iranian Churn | CodAdaptClassifier | Logloss | 0.182275366 | 0.093278915 | +115.735709% | Weak relative to HGB on both splits |
| Multiclass | CNAE-9 | CodAdaptClassifier | Logloss | 1.075441172 | 0.644209742 | +67.082502% | Weak relative to HGB on both splits |
| Multiclass | Mice Protein | CodAdaptClassifier | Logloss | 1.371754045 | 2.667591222 | −48.473094% | Strong logloss result; macro-F1 slightly worse |

Task summaries first average the paired deltas within each source, then take the
median across the two sources per task, so sources have equal weight:

| Task / model | Sources | Evaluation units | Median relative primary-loss delta vs HGB | Unit wins / ties / losses |
| --- | ---: | ---: | ---: | ---: |
| Regression / CodAdaptRegressor | 2 | 3 | −1.089803% RMSE | 1 / 1 / 1 |
| Regression / SafeBlendRegressor | 2 | 3 | −2.342895% RMSE | 1 / 2 / 0 |
| Binary / CodAdaptClassifier | 2 | 4 | +121.358260% logloss | 0 / 0 / 4 |
| Multiclass / CodAdaptClassifier | 2 | 4 | +9.304704% logloss | 2 / 0 / 2 |

Wins/ties/losses use a descriptive ±1% primary-loss tie interval. These counts
are not significance tests; no confidence interval or universal quality ranking
is inferred from this pilot.

### Technical robustness and predictive limits

All **11/11 units and 36/36 fitted runs completed**, with no observed public API
or data-handling failure. Four representative pickle/joblib persistence checks
and three same-seed deterministic replay fits passed bitwise prediction checks
(and probability checks for classifiers), covering all three tasks. Replay fits
are separate from the 36 quality-evaluation fits. These technical checks do not
establish predictive competitiveness on every workload.

The final product verdict was **EXTERNAL_PRODUCT_QUALIFICATION_MIXED**. Regression
showed modest favorable aggregate RMSE deltas versus HGB on this small external
pilot. The heldout-cultivar soybean results did not consistently beat Dummy;
the contract covers one site/harvest, not future-season extrapolation. Group-shift
effects were not isolated against a matched random-split control.

**BINARY_EXTERNAL_QUALITY_GAP = YES.** Both binary sources showed substantially
higher logloss than HGB. The source-balanced AUC delta was also **−0.060360** and
the Brier delta **+0.044113**, so the observation is not characterized as a
calibration-only deficit. This is a known limitation on two untuned sources,
not a universal result or evidence for a particular algorithmic fix.

Multiclass Shared OVR was technically qualified, while external predictive
results were mixed across domains. Mice improved logloss and accuracy (mean
accuracy delta **+0.022222**) but reduced macro-F1 (**−0.017634**). CNAE-9 lost
on both splits; the two-source aggregate accuracy and macro-F1 deltas were
**−0.081249** and **−0.096343**, respectively. Two multiclass datasets do not
establish general competitiveness or across-metric dominance.

SafeBlend's **−2.342895%** regression summary belongs to SafeBlend, not the Base
regressor. Its internal validation fallback selected BASE once and BLEND twice;
the final model was worse than a separately fitted CodAdaptRegressor on one of
three units. The standalone Base has a different fit/internal split from the
Base component inside SafeBlend. Rejected blend components and accepted mixed-input
component counterfactuals were not observable through the public API here, so
these observations do not quantify harmful admission, avoided harm or useful
rejection rates. Internal validation fallback does not guarantee test improvement.

### Large-N deployment boundary

A separate frozen memory audit found that **Covtype-like large-N multiclass
workloads remain excluded by the conservative safe-memory guard in the tested
configuration**. The full fit was not authorized under that guard; **no actual
out-of-memory event or Covtype fit peak was measured**. This is a tested deployment
boundary, not a predictive loss, and Covtype is not one of this six-dataset pilot's
evaluation units. The guard and predictive implementation are unchanged.

## Additional author-run reproducibility support

The [exploratory repeated-CV report](benchmarks/reproducibility/BENCHMARK_CV_REPORT.md), [runner](benchmarks/reproducibility/benchmark_codadapt_cv.py), [240 archived result rows](benchmarks/reproducibility/benchmark_cv_full.csv) and [historical metadata](benchmarks/reproducibility/benchmark_cv_full.json) are retained as intentional public support. This four-small-dataset, author-run experiment is secondary/historical evidence, not independent validation and not a replacement for the frozen blind panel. Its original run script hash is distinct from the formatted/import-sorted supplied runner; see the report's provenance note. No benchmark was rerun here.

## Exact SafeBlend callback engineering measurement

The later exact callback optimization removes redundant diagnostic gradient computation. The paired six-case engineering panel reported **43.55%** lower Rational fit time and **27.27%** lower total SafeBlend fit time, with serialized/deep memory and inference effectively unchanged. The qualification replay preserved coefficients, trace, branch decisions and predictions bitwise. These panel-specific implementation measurements do not change the frozen scientific recipe, blind quality figures or hardware/workload caveats. Round 78's approximately 4.13× Base fit ratio predates this callback optimization. See the [SafeBlend contract](docs/SAFE_BLEND_EXPERIMENTAL.md).
