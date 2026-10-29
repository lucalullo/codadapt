# Piano definitivo dei 59 file storici

Tutti i 59 percorsi hanno una decisione individuale e un hash verificato sulla copia di ripristino autorizzata.
Il repository reale non è stato consultato o modificato. Nessuna rimozione è stata eseguita.

Le classificazioni tecniche originarie sono conservate: 6 ESCLUDERE, 34 INTEGRARE,
4 CONSERVARE_AGGIORNARE, 10 AGGIORNARE e 5 CONSERVARE.
Per il trasferimento a livello di percorso, gli stessi 59 diventano **38 REMOVE proposti, 16 MODIFY e 5 KEEP**.
Le 38 rimozioni comprendono anche i vecchi percorsi di funzionalità ricollocate, non solo i sei contenuti esclusi.

Sono preservati 30 moduli/helper storici in `tests/legacy`: 28 byte-identici e due adattati
unicamente per `class_weight=None`. Dei 30, 29 compaiono in questo inventario dei 59;
il trentesimo è `conftest.py`, conservato byte-identico in `tests/legacy/conftest.py` mentre
il nuovo `tests/conftest.py` configura il percorso degli artifact. Non rimuovere il nuovo conftest.
La vecchia harness packaging è preservata ma esclusa esplicitamente dall'esecuzione predefinita:
il suo path injection è sostituito da installazioni pulite e controlli delle distribuzioni, senza attribuirle PASS.

Documentazione API, algoritmo, memoria, optional EBM/SafeBlend, migrazioni, esempi misti e risultati storici
restano nella copia finale. Le note storiche non certificano il nuovo backend o piattaforme non testate.

**Una copia sovrapposta è insufficiente:** resterebbero quattro vecchi workflow, test duplicati e materiali
non destinati alla consegna. Le rimozioni richiedono approvazione personale e verifica dell'hash attuale.
Leggere [elenco rimozioni](REMOVALS_REQUIRING_APPROVAL.md) e
[istruzioni definitive](ISTRUZIONI_TRASFERIMENTO_GITHUB.md).

| Percorso storico | Decisione tecnica | Azione sul percorso | Destinazione / motivo |
|---|---|---|---|
| `.github/workflows/publish-pypi.yml` | ESCLUDERE | REMOVE | Nessun equivalente di pubblicazione |
| `.github/workflows/publish-testpypi.yml` | ESCLUDERE | REMOVE | Nessun equivalente di pubblicazione |
| `.github/workflows/release-qualification.yml` | INTEGRARE | REMOVE | .github/workflows/qualification.yml; docs/QUALIFICATION.md |
| `.github/workflows/tests.yml` | INTEGRARE | REMOVE | .github/workflows/qualification.yml; docs/QUALIFICATION.md |
| `AGENTS.md` | ESCLUDERE | REMOVE | Documentazione pubblica normale; memoria privata preservata separatamente |
| `BENCHMARKS.md` | CONSERVARE_AGGIORNARE | MODIFY | BENCHMARKS.md con etichetta storica; docs/PERFORMANCE.md |
| `benchmarks/reproducibility/BENCHMARK_CV_REPORT.md` | CONSERVARE_AGGIORNARE | MODIFY | Stesso percorso, con banner storico |
| `benchmarks/reproducibility/benchmark_codadapt_cv.py` | AGGIORNARE | MODIFY | Stesso percorso o runner storico documentato |
| `benchmarks/reproducibility/benchmark_cv_full.csv` | CONSERVARE | KEEP | Stesso percorso |
| `benchmarks/reproducibility/benchmark_cv_full.json` | CONSERVARE | KEEP | Stesso percorso |
| `benchmarks/run_benchmarks.py` | AGGIORNARE | MODIFY | Stesso percorso |
| `docs/ALGORITHM.md` | AGGIORNARE | MODIFY | docs/ALGORITHM.md |
| `docs/AUTO_MEMORY.md` | AGGIORNARE | MODIFY | docs/AUTO_MEMORY.md |
| `docs/EBM_COMPILER.md` | AGGIORNARE | MODIFY | docs/EBM_COMPILER.md |
| `docs/LARGE_DATASETS.md` | AGGIORNARE | MODIFY | docs/LARGE_DATASETS.md |
| `docs/OFFICIAL_PRODUCT_CANDIDATE.md` | ESCLUDERE | REMOVE | docs/HANDOFF_REPORT.md; RELEASE_NOTES.md |
| `docs/PYTHON_COMPATIBILITY.md` | INTEGRARE | MODIFY | docs/COMPATIBILITY.md; qualification/PLATFORM_MATRIX.json |
| `docs/RC1_KNOWN_LIMITATIONS.md` | INTEGRARE | MODIFY | docs/LIMITATIONS.md; docs/HANDOFF_REPORT.md |
| `docs/RELEASING.md` | AGGIORNARE | MODIFY | docs/RELEASING.md; procedura versionamento; ISTRUZIONI_TRASFERIMENTO_GITHUB.md |
| `docs/SAFE_BLEND_EXPERIMENTAL.md` | AGGIORNARE | MODIFY | docs/SAFE_BLEND_EXPERIMENTAL.md |
| `docs/STABILITY.md` | AGGIORNARE | MODIFY | docs/STABILITY.md; docs/PERSISTENCE.md |
| `docs/V1_0_1_TO_V1_1_0RC1_COMPATIBILITY.md` | CONSERVARE_AGGIORNARE | MODIFY | Stesso percorso con banner storico |
| `docs/V1_0_1_TO_V2_0_COMPATIBILITY.md` | CONSERVARE_AGGIORNARE | MODIFY | Stesso percorso con banner storico |
| `docs/research/RESEARCH_MASTER.md` | ESCLUDERE | REMOVE | docs/PERFORMANCE.md; docs/HANDOFF_REPORT.md solo sintesi verificata |
| `docs/research/RESEARCH_STATE.json` | ESCLUDERE | REMOVE | Matrice/stati pubblici sintetici, memoria privata integra |
| `examples/basic_classification.py` | CONSERVARE | KEEP | Stesso percorso |
| `examples/basic_multiclass.py` | CONSERVARE | KEEP | Stesso percorso |
| `examples/basic_regression.py` | CONSERVARE | KEEP | Stesso percorso |
| `examples/kaggle_quickstart.ipynb` | AGGIORNARE | MODIFY | Stesso percorso o guida equivalente completa |
| `examples/release_smoke.py` | INTEGRARE | REMOVE | examples/basic_usage.py; tools/engineering_probe.py; optional smoke mirato |
| `tests/_binary_reference.py` | INTEGRARE | REMOVE | tests/legacy/_binary_reference.py |
| `tests/_multiclass_helpers.py` | INTEGRARE | REMOVE | tests/legacy/_multiclass_helpers.py |
| `tests/test_adaptive_levels.py` | INTEGRARE | REMOVE | tests/legacy/test_adaptive_levels.py |
| `tests/test_addressing.py` | INTEGRARE | REMOVE | tests/legacy/test_addressing.py |
| `tests/test_auto_memory.py` | INTEGRARE | REMOVE | tests/legacy/test_auto_memory.py |
| `tests/test_auto_memory_cgroup.py` | INTEGRARE | REMOVE | tests/legacy/test_auto_memory_cgroup.py |
| `tests/test_auto_memory_policy.py` | INTEGRARE | REMOVE | tests/legacy/test_auto_memory_policy.py |
| `tests/test_cardinality.py` | INTEGRARE | REMOVE | tests/legacy/test_cardinality.py |
| `tests/test_classifier.py` | INTEGRARE | REMOVE | tests/legacy/test_classifier.py |
| `tests/test_classifier_training.py` | INTEGRARE | REMOVE | tests/legacy/test_classifier_training.py |
| `tests/test_coded_memory.py` | INTEGRARE | REMOVE | tests/legacy/test_coded_memory.py |
| `tests/test_default_api.py` | INTEGRARE | REMOVE | tests/legacy/test_default_api.py |
| `tests/test_ebm_compiler.py` | INTEGRARE | REMOVE | tests/legacy/test_ebm_compiler.py |
| `tests/test_incremental_gain.py` | INTEGRARE | REMOVE | tests/legacy/test_incremental_gain.py |
| `tests/test_independence.py` | INTEGRARE | REMOVE | tests/legacy/test_independence.py |
| `tests/test_inference_metadata_exact.py` | INTEGRARE | REMOVE | tests/legacy/test_inference_metadata_exact.py |
| `tests/test_memory_budget.py` | INTEGRARE | REMOVE | tests/legacy/test_memory_budget.py |
| `tests/test_multiclass.py` | INTEGRARE | REMOVE | tests/legacy/test_multiclass.py |
| `tests/test_no_leakage.py` | INTEGRARE | REMOVE | tests/legacy/test_no_leakage.py |
| `tests/test_packaging.py` | INTEGRARE | REMOVE | tests/legacy/test_packaging.py |
| `tests/test_persistence.py` | INTEGRARE | REMOVE | tests/legacy/test_persistence.py |
| `tests/test_pre_rc_api.py` | INTEGRARE | REMOVE | tests/legacy/test_pre_rc_api.py |
| `tests/test_preprocessing.py` | INTEGRARE | REMOVE | tests/legacy/test_preprocessing.py |
| `tests/test_rational_callback.py` | INTEGRARE | REMOVE | tests/legacy/test_rational_callback.py |
| `tests/test_regressor.py` | INTEGRARE | REMOVE | tests/legacy/test_regressor.py |
| `tests/test_release_contracts.py` | INTEGRARE | REMOVE | tests/legacy/test_release_contracts.py |
| `tests/test_safe_blend.py` | INTEGRARE | REMOVE | tests/legacy/test_safe_blend.py |
| `tests/test_shared_encoder.py` | INTEGRARE | REMOVE | tests/legacy/test_shared_encoder.py |
| `tests/test_sklearn_compat.py` | INTEGRARE | REMOVE | tests/legacy/test_sklearn_compat.py |

[HISTORICAL_MIGRATION.json](HISTORICAL_MIGRATION.json) conserva motivazione, hash, dimensioni e verifiche per ogni voce.
[FILE_COMPARISON.json](FILE_COMPARISON.json) copre anche tutti gli altri file aggiunti, modificati e conservati.
