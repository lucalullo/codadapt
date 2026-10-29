> Historical observations, not new G6-R1 measurements. Presets, source versions
> and unfavorable outcomes remain historical. Current results: [docs/PERFORMANCE.md](docs/PERFORMANCE.md).

# Benchmark Disclosure

The local 1.1.0rc1 adds no predictive-quality claim and does not rerun or rewrite
these frozen panels. Its scoped inference/size/admission claims are documented in
[the release notes](RELEASE_NOTES.md), with [tradeoffs](docs/RC1_KNOWN_LIMITATIONS.md).

The later independent SafeBlend regression qualification takes precedence for
current **SafeBlend positioning**: compact serialized models were confirmed,
while predictive quality leadership was not. The frozen blind NEW_EXTERNAL panel
remains the primary binary/multiclass evidence and its library-wide verdict remains
**PRODUCT_POSITION_MIXED**. Earlier external pilots are secondary/historical evidence;
development and transfer panels are research evidence. The panels below remain
separate; historical measurements do not override the later regression qualification.

## Independent SafeBlend Regression Qualification

This later qualification used **nine NEW_EXTERNAL real regression datasets**, all
primary, **45 frozen splits** and **270 model jobs**: **270 SUCCESS, zero terminal
failures**. Five sources used **GROUP_SPLIT** (25 conditions); four used
**TIME_SPLIT** (20 conditions), including UCI859's previously frozen forward-time
contract. The source/target/feature allowlists, exact split indices, seeds, presets,
versions, threads and resource limits were frozen before the first fit. There was
**zero tuning**, no outcome-based source substitution and no intermediate aggregate
analysis before terminal results were frozen.

Each unit compared public-default CodAdaptRegressor Base and SafeBlendRegressor
with fixed HistGradientBoosting, LightGBM, CatBoost and XGBoost baselines. Recipes,
train-only baseline adapters and versions were those of the earlier
[blind protocol](#blind-methodology-and-limits): boosting retained six threads,
accessories at most four, and public SafeBlend retained its one-thread default.
One heavy process ran at a time. Two separately counted deterministic refits checked
observer parity and persistence; they are additional to the 270 primary jobs.

Frozen protocol SHA256:

```text
349a025c290168c06e4a58ec5be6d0232e5e8aaa73bd57cd12cb2c941ab1b665
```

Raw-results freeze receipt SHA256:

```text
059739d004179c47e5058885d1f53325aa5b63a0b78b170b60eac35044c8c107
```

### Independent quality and downside

The **preregistered external leader** is the best RMSE among the four fixed
baselines **per evaluation unit**. Its identity is determined after evaluation;
it is a descriptive reference, not a test-selected deployable model or an input
to SafeBlend selection. This differs from the earlier blind **per-source** leader.
Relative RMSE delta is `100 × (candidate / leader − 1)`; positive means worse.
Paired unit deltas are reduced by within-source median, then equal-source median.

Absolute RMSE values below are within-source medians in each target's natural
units; the leader column summarizes the per-unit leader. The paired-delta column
is **not** a ratio of these separately summarized RMSE columns. Target scales
must not be pooled. Each source has five complete conditions.

| Source / target | Split | Base RMSE | SafeBlend RMSE | Leader RMSE | SafeBlend paired median delta |
| --- | --- | ---: | ---: | ---: | ---: |
| UCI859 / measured execution time | TIME | 0.187011 | 0.184826 | 0.138509 | +0.14% |
| SteelStrength, Figshare 7250453 / yield strength (MPa) | GROUP | 187.891 | 181.137 | 117.802 | +29.98% |
| CitrineThermal, Figshare 7231202 / thermal conductivity (W/mK) | GROUP | 42.8523 | 41.625 | 39.092 | +6.48% |
| Rifugio Boe, Zenodo 17473383 / room temperature (°C) | TIME | 4.49584 | 4.45897 | 4.35791 | +4.62% |
| Cyprus PV, Zenodo 17775544 / inverter power (W) | TIME | 1161.68 | 1201.06 | 1036.39 | +6.69% |
| BLS QCEW 2024 / weekly industry wage (USD) | GROUP | 727.922 | 723.998 | 817.766 | −11.47% |
| NOAA NDBC 46042 / significant wave height (m) | TIME | 0.776111 | 0.764086 | 0.698192 | +6.55% |
| BigSolDB nonaqueous, Zenodo 22648301 / mole-fraction solubility | GROUP | 0.106517 | 0.106417 | 0.107372 | −0.55% |
| WeldFatigue, Figshare 29254265 / fatigue life (cycles) | GROUP | 9.7621e+07 | 9.76339e+07 | 9.97056e+07 | +0.15% |

| Equal-source aggregate | Base | SafeBlend |
| --- | ---: | ---: |
| Median relative RMSE delta vs external leader | +4.65% | +4.62% |
| Median serialized-size ratio vs external leader | 0.110× | 0.129× |

SafeBlend's dataset wins/ties/losses were **2/0/7**; only **2/9** source medians
were favorable. Its diagnostic source-bootstrap 95% median-delta interval was
**[−0.55%, +6.69%]**, from 10,000 draws with seed 785299. The median RMSE improvement
versus standalone Base was only **0.094%**. These results do not confirm a predictive
quality advantage. Repeated group/time conditions are not 45 independent datasets.

The **worst dataset mean degradation was +30.85%** (SteelStrength). Its paired
median above is a different statistic. The **worst split was +116.29%**, UCI859
condition 0 versus CatBoost. All fits succeeded; severe predictive downside is
not a technical failure and is not hidden by successful execution or the medians.
The frozen catastrophic flag used source-mean degradation above 50% or model/
nonfinite failures; its absence does not imply absence of severe split downside.

Group-source median RMSE delta was **+0.15%** (five sources); time-source median
was **+5.58%** (four). These observed blocks do not define a validated deployment
niche or a rule for choosing SafeBlend before results are known.

### Independent compactness and systems

All ratios are **SafeBlend / the same per-unit RMSE leader**, aggregated within
source then across sources. They are not SafeBlend/Base ratios. Warm latency
includes raw-input preprocessing through the complete fitted pipeline.

| Measure | Source-balanced median ratio |
| --- | ---: |
| Serialized model size | 0.129× |
| Reachable deep retained memory | 3.368× |
| Fit time | 1.210× |
| Warm inference latency, batch 1 | 0.765× |
| Warm inference latency, batch 32 | 0.765× |
| Warm inference latency, batch 1k | 0.684× |
| Warm inference latency, batch 100k | 0.807× |
| Sampled process-tree peak RSS | 0.980× |

**Serialized compactness is independently replicated; a deep-RAM advantage is
not demonstrated.** Deep accounting covers reachable Python/NumPy/pandas objects
and omits opaque native baseline heaps, so its ratio is an incomplete RAM
comparison. Process-tree peak RSS includes inputs and runtime state, not only the
model; the SafeBlend source-median peak was 179,916,800 bytes. Neither measure is
interchangeable with serialized size. Base was smaller than SafeBlend on this panel.

SafeBlend showed faster inference than the quality leader on this tested panel,
but was **not a fit-speed specialist**. The environment was one Windows host,
AMD Ryzen 7 255, 32 GB RAM, Python 3.12.14 and the package versions listed in the
blind methodology. Timing used 20 alternating repetitions per batch; cache pressure
was a proxy, and oversized batches cycled heldout rows. Ratios are **hardware- and
protocol-specific**; independent-hardware replication is not established.

### Independent safety and positioning

Internal validation selected **32 BLEND / 13 BASE** branches. There were **9 harmful
admissions out of 32 BLEND selections (28.125%)**: test RMSE exceeded that of the
retained internal Base. Six of the 13 rejected blends would have improved test
RMSE; these are diagnostic counterfactuals, never used for selection. The internal
Base has a different training/validation split from standalone Base. Validation
fallback reduces risk but **does not eliminate harmful admissions on unseen domains**.

The verdict is **COMPACT_REGRESSION_SPECIALIST_CONFIRMED**: serialized ratio ≤0.35×
and median RMSE degradation ≤5% passed. The strong compact gate (≤0.20× and ≤3%)
failed, as did the quality-specialist gate (median delta ≤0, at least 60% nonworse
sources, improvement over Base, worst dataset mean ≤5%, no catastrophic failure).
SafeBlend offers a strong model-size and inference-efficiency trade-off on this
panel, but its predictive quality was weaker than the preregistered external leader.
It remains an opt-in, experimental **compact regression specialist**.

**QUALITY DID NOT REPLICATE**: the earlier five-dataset blind median was **−0.67%
RMSE**, versus **+4.62%** here. **COMPACTNESS DID REPLICATE: 0.120× → 0.129×**
serialized size. The earlier evidence remains below, with its own uncertainty and
different leader rule; the panels are not pooled. This later qualification takes
precedence for current SafeBlend positioning.

NEW_EXTERNAL remains conditional on recoverable history, with missing early
catalogs. Frozen outer group/time isolation and TRAIN-only preprocessing were
preserved; unchanged internal validation is not group/time-aware. Temporal sources
evaluate future observations of known hosts/sites, not unseen-site or operational
forecasting performance. Original feature exclusions, missing values and natural
target tails were retained. No algorithm, safety rule, public default or version
changed as a result of this qualification.

## Frozen Blind External Benchmark

This earlier panel remains primary for binary/multiclass. Its five-source
SafeBlend quality advantage did not replicate in the later independent
qualification above; serialized compactness did. Historical gates and values
below describe only this earlier protocol.

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
| Regression | SafeBlendRegressor | 5 | −0.665536% RMSE | 0.120452× | Earlier quality advantage did not replicate; compactness did |
| Binary | CodAdaptClassifier | 6 | +9.364320% logloss | 0.111256× | Current blind quality gap |
| Multiclass | CodAdaptClassifier | 5 | +22.031308% logloss | 0.146041× | Current blind quality gap despite technical Shared-OVR validation |

**Preregistered baseline leader** means the reference chosen per source by the
frozen analysis rule: the complete mainstream baseline with the lowest median
primary loss among HistGradientBoosting, LightGBM, CatBoost and XGBoost. Ties within
1e-12 use that order. The rule was preregistered; the leader's identity was determined
after evaluation. It is a descriptive benchmark reference and may differ by dataset;
it was not used to tune or choose CodAdapt predictions. It is not necessarily HGB.

On this earlier panel, SafeBlend passed both the compact and strong compact **regression** gates, with
**n=5 datasets and a 95% confidence interval including zero**. Its relative RMSE
delta CI is **[−4.661698%, +27.999900%]**. The corresponding gain interval also
includes zero; a general regression advantage is not established. Base regression's
relative RMSE delta CI is **[−3.913731%, +47.635643%]**.

The compact gate requires median serialized ratio ≤0.35, median relative loss
degradation ≤5%, at least 70% of sources within 10%, and competitiveness in every
covered task. The strong gate requires ≤0.25, ≤3%, at least 75% within 5%, and the
same task condition. Base covers all 16 sources and **fails both overall gates**;
SafeBlend was a separate five-source regression candidate and **passed both**
under this earlier protocol, not under the later independent quality gates.
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

The current 1.0.0rc1 candidate retains the automatic single-label multiclass classification added in the 0.2.0rc2 line.
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
uses the [independent SafeBlend regression qualification](#independent-safeblend-regression-qualification)
and the [blind binary/multiclass evidence](#frozen-blind-external-benchmark) above; the pilot's
two-source binary estimate is not the current headline. Its results are retained
without changing their original HGB reference or aggregation.

This separate frozen product pilot evaluated the historical **0.2.0rc2** public
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
