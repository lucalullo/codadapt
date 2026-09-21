# CODADAPT RESEARCH MASTER

**Research continuity record — tracked in the repository.** Stato al 2026-09-21, ultima round completata: **43**. Leggere anche [RESEARCH_STATE.json](RESEARCH_STATE.json). Consolidazione iniziale R1–37 preservata; aggiornamenti con esperimenti Round38–43 completati. Nessun risultato mancante è stato ricostruito per supposizione.

## 1. Project identity

> **Continuity note:** this file and `RESEARCH_STATE.json` are intentionally versioned so a new Codex/session can reconstruct the project without the private experiment tree. Links to `research_private/` are historical source references from the original development workspace and may be unavailable in a clean clone; the round summaries below preserve the decisions, metrics and reopen conditions needed to continue safely.


CodAdapt, versione locale **0.2.0rc1** (candidata interna non pubblicata; core nativo **0.1.0** invariato), è una libreria sperimentale CPU per dati tabellari: memorie compatte indicizzate da codici e residual corrections, con un budget di lookup. Non è un albero né una rete. Non è dimostrata superiorità generale sui boosting.

API sklearn-style: `CodAdapt` è alias di `CodAdaptClassifier`; `CodAdaptRegressor` supporta regressione single-target. `fit`, `predict`, `predict_proba` per classificazione binaria, `get_params`/`set_params`, cloning/pipeline/CV, sample weights, eval_set, random_state e pickle/joblib. **Multiclass nativo non supportato**: i dataset originariamente multiclass dei benchmark sono stati binarizzati. La versione è verificata nel codice locale, non una verifica dello stato di pubblicazione remoto.

## 2. Current public core

**R42:** il namespace opzionale `codadapt.experimental` è ora implementato; vedere [contratto pubblico](../EBM_COMPILER.md). Non sostituisce il core descritto sotto. Il solo file pre-esistente modificato in src è `_version.py`; gli altri7 hash sono invariati.


Percorso effettivo verificato in `_base.py`, `_training.py`, `preprocessing.py`:

```text
raw DataFrame / dense numeric array
→ validazione input, pesi, split training/validation
→ preprocessing nativo train-only (quantili/categorie/missing)
→ shared finest encoding e mappe intere coarse-to-fine
→ fino a tre livelli di adaptive coded memory
→ main effects selezionati sul residuo
→ poche interaction memories a codici fissi
→ somma ordinata con intercetta; sigmoid per binary / score per regression
```

Al default `n_bins=32`, il finest effettivo è `min(16,n_bins)`: livelli **4/8/16**, non 32 bucket effettivi. Quantili float64 su massimo 20k training rows; `searchsorted(side="right")`; missing numerico separato. Categoriche: top 128, rare osservate/missing/unseen distinti e membership delle categorie viste; schema train-only. Una singola trasformazione fine alimenta mappe di livello, non tre fit separati.

Intercetta iniziale media/log-odds pesati, poi fissa. Budget totale default 24 lookup, ripartito tra livelli; circa 2/3 dei posti ai main. Prefiltro deterministico fino 512 righe, screening e feature stopping permanente. Tabelle ridge aggregate via `bincount`, valore B/(A+l2), l2 default 5. Classificazione usa il surrogato con curvatura globale 1/4. Le coppie vengono proposte da ranking univariato; codici interi pseudocasuali **non riadattati dal trainer corrente**; indirizzo somma-modulo, table_size default 256. Utility penalizza collisioni. Un bucket non supportato azzera l’interazione in prediction; celle vuote zero. Una tabella su una sola feature conta come main effect, non interazione.

Validation MSE/logloss non pesata ammette un livello solo oltre soglia relativa; al primo livello rifiutato termina. Non è il vecchio training iterativo a patience. `max_iter`, `adapt_codes`, `adapt_every`, `max_code_updates`, `n_candidates`, `min_code_count`, `patience` sono in gran parte parametri legacy validati ma non controllano questo percorso; `features_per_table` influenza stima RAM, non la coppia effettiva. Vedere audit per caveat esatti. Non usare timer legacy lasciati zero come profilazione reale. Nessun backfitting globale di default.

**Discrepanza documentale importante:** [docs/ALGORITHM.md](../ALGORITHM.md) descrive anche un motore legacy con coordinate di riindirizzamento, intercetta aggiornata e iterazioni non eseguite dal trainer pubblico attuale. Per ricostruire il comportamento hanno precedenza codice + [audit R7](../../research_private/round7_audit.md). Non correggere automaticamente codice/API per farli coincidere con quel documento.

**Pubblico e congelato:** tutto `src/codadapt/`, classifier, regressor, encoder, interaction engine, API/default v0.1.0. Da R42 il compiler EBM opzionale è integrato nel namespace pubblico experimental; le varianti di ricerca restano private e non sostituiscono il default. Limite preventivo 512MiB del fit è stima conservativa, non tetto RSS del processo.

## 3. Current evidence

**Ultima evidenza R43:** Local-only scope completed:375 passed,4 existing xfails,0 failed; Ruff/format clean; wheel+sdist rebuilt from the delivery ZIP; two fresh venvs with system-site-packages=false and isolated Python; base classifier/regressor, EBM compile+SAFE/REJECT and numerical fidelity PASS;16 pickle/joblib checks including12 historical exports in an environment where interpret is absent. Version/metadata0.2.0rc1 coherent. Clean folder+ZIP44 public files, no research/cache/venv/build output. User explicitly replaced remote validation with local checks and final source artifacts. No GitHub install, dispatch, Kaggle/Colab/SSH execution, commit, push, tag or release. Earlier read-only GitHub inspection showed green Python3.10/3.11/3.12 jobs only for v0.1.0, not this RC; it is not RC evidence.


**Evidenza storica R42:** 375 passed, 4 existing expected xfails, 0 failed/error; 25 real-EBM compiler tests; Ruff/format clean; wheel+sdist build and twine PASS; wheel and local source install PASS. Frozen cohort12/13 SAFE, raw bit mismatches0 against teacher and R37 across7 batch sizes; Diabetes47 REJECT because numerical category labels are outside the string-only public contract. Max probability difference2.22e-16, allowed absolute1e-15. All12 SAFE artifacts load/predict from installed wheel while interpret import is blocked. Candidata interna0.2.0rc1, non release finale; hardware indipendente ancora PENDING.


**Evidenza storica R41:** Independent hardware replication NO; portable kit prepared and executed locally only, Linux build UNRUN. Official R37 exact raw-score contract: single-row 3.838xEBM, >=3x on 9/13; deep memory 0.182x, <=0.30 on 11/13; sampled peak RSS100k 0.597x. FAST_SAFE 84/91 observed model/batch cases, SAFE 7/91. No universal monotonic batch cutoff. Raw scores and frozen compiled predictions bitwise exact; strict teacher-probability contract REJECT for 10/13 models, max difference 2.22e-16. No runtime fix; this clarifies prior raw-score versus probability fidelity scope. Opt-in exact binary logits and single-target regression; supported additive EBM schemas; target-host fidelity/profile before FAST_SAFE; no bitwise EBM probability guarantee Experimental YES (scoped), default NO.


**Evidenza storica R40:** Round39 replicated PARTIALLY. Historical ready/session [1.5097995780788627, 1.5223270633516743, 1.5121240266033158]; new ready/session [1.362480888455787, 1.385029012881379, 1.360380090821325]. Pooled ready 1.4323x, end-to-end 1.3457x, batch100k/EBM 1.0082x, single/EBM 0.2665x, deep/EBM 0.1857x. Historical complete gate PASS; new complete gate FAIL. R37 official research reference; R39 not promoted after independent replication. Power/Gas/Diabetes100k/EBM 2.1524/1.0082/1.2395x. Fidelity bucket/prediction/false-safe 0/0/0. Requested numerical gates pooled across13 datasets PASS; the conservative reference decision uses the additional preregistered separate-cohort transfer gate, not a claimed failure of pooled thresholds.


**Evidenza storica R39:** Layout D, colonne contigue dirette quando possibile, single-thread. Ready-buffer vs R37 1.5007x; end-to-end vs R37 1.3367x. Batch100k/EBM 1.0331x; Power/Gas/Diabetes 2.2778/1.0194/1.2293x. Single/EBM 0.2878x; deep/EBM 0.1701x; conversion share 5.57%. Bucket/prediction mismatch 0/0; nuovi false-safe0 sui sei SAFE congelati. Gate PASS. Margine ready rispetto alla soglia1.5x 0.0458%; mediane per sessione {'1': 1.4717679786503473, '2': 1.53024342881784}. Passaggio eventualmente nominale, non prova robusta di replica; nessuna promozione pubblica. Readiness PARTIALLY; usare i rapporti paired correnti e il report completo.


**Evidenza storica R38:** Backend c; thread grandi 4; bucket/prediction mismatch0/0 su 12,465,430 probe numerici. Kernel bucket speedup0.739x, fused0.781x. End-to-end single/1k/100k vs EBM 0.271/1.218/3.648x; speedup100k vs R37 0.504x; deep0.170xEBM. Gate mediano FAIL. I risultati R37 sotto sono storici, non la misura corrente.


Convenzioni: AUC gain = candidato−Base; RMSE gain =100×(1−candidato/Base), positivo migliore. Gap RMSE verso un riferimento =100×(modello/riferimento−1), positivo peggiore. Rapporti sistemi normalmente candidato/riferimento, minore migliore; R6 usa invece LightGBM/CodAdapt. Non sottrarre mediane per ottenere effetti paired; non sommare split sovrapposti come repliche indipendenti. Recovery teacher è la somma dei gain sui dataset teacher-positive, non il rapporto delle mediane né una misura universale di fidelity.

| Stato | Evidenza e limite |
|---|---|
| CONFIRMED | R15:27 nuovi×5, Base vs tunedLGBM −0.020297AUC; RMSE −3.848% con CI comprendente zero. Contro CatBoost Base è circa 8.26% peggiore in RMSE. Fit19/27,predict24/27,pickle24/27wins vs LGBM. Nessuna nicchia predittiva stabile contro tutti i riferimenti. |
| CONFIRMED | R23: strong additive+existing interactions +0.011209AUC/+7.98% RMSE sui12 nuovi, a costo fit26.945x. Opportunità main effects, non un nuovo core efficiente. |
| CONFIRMED | R26/R33: le funzioni additive EBM si conservano quasi interamente in export compatto sui cohort provati. R33 new15×5: +0.016102AUC/+7.115% RMSE vsBase; total fit19.289/23.425x C/R. Il teacher costa e resta necessario durante fit. |
| CONFIRMED | R35 exact/R36/R37:6 modelli verificati nel contratto supportato, teacher eliminato a inference, zero divergenze osservate; single-row/memoria sono i vantaggi principali. |
| EXPLORATORY | Oracle R19,meta-associazioni R15,frontiere R16,shape-cause R29 e tutte le ablation su development riusato: diagnosi, non nuove conferme. |
| FAILED TO REPLICATE | Classifier R9+0.014272AUC non replica R10(−0.008098) né R15(−0.020297), su cohort diversi. A+Bpromettente R7 non diventa core in R8/R9. Discovery R17/18,backfit R19→20,alpha R31 non superano la verifica successiva. |
| FAILED TO REPLICATE | R37 vantaggio apparente~34% su duewide in processi separati non replica nel controllo alternato: R37/R36≈0.992–1.012. Nessuna nuova accelerazione numerica dimostrata. |

### Provenienza e discrepanze da conservare

- R1–6: sintesi utente nell’allegato iniziale; i report/raw originali non sono nel workspace. R1–2sono descritti insieme. R6 è parzialmente corroborata da BENCHMARKS.md. Numeri storici non equivalgono a nuova verifica. La sintesi originale utile è riportata nella timeline, quindi una sessione nuova non dipende dall’esistenza dell’allegato.
- `research_private/CODADAPT_PRIVATE_RESEARCH_HISTORY.txt` copre **solo R7–15**, non tutta la ricerca. Nessun file omonimo alla root e nessuna cartella discovery alla root: quelle esistenti sono sotto research_private. Gli artefatti locali sono indice delle osservazioni già usate: non chiamarli unseen.
- R10 family percentages43.6/39.2sono quote descrittive del gap positivo, non una causa provata. R29 poi classifica il direct learner come mixed, non leakage dimostrato.
- R20 non replica2.20% R19:20 pass sul vecchio subset danno1.026% nel nuovo protocollo; cambiano inizializzazione/ordine/stopping, non è un confronto causale unico.
- R25 teacher22.50% gain regressivo, R26 teacher1.48%,R33 teacher7.116% sono cohort diversi: fedeltà rappresentazionale confermata, ampiezza del vantaggio teacher variabile. R26 cap 512 non vincola; R34 dimostra che512non basta a tutti.
- R34 optimized può essere bitwise uguale al compiled lossy e tuttavia perdere0.033282AUC rispetto EBM suGas. R35 exact risolve questo caso aumentando capacità; non cancella la perdita precedente.
- R37 primo export deep0.355x duplicava buffer e viste al pickle. Persistenza corretta→0.167x, tagli/celle invariati; vecchie misure archiviate. Mediana100k1.099x corrente prevale su1.360x R36 come misura della sessione, ma non prova accelerazione, come mostra paired check. I casi individuali restano lenti.

## 4. Complete research timeline

Decisione riferita alla proposta della round, non a una promozione pubblica automatica. ACCEPT R4/R5 indica principi già incorporati secondo storia/codice; dal R7 nessun nuovo core è stato promosso. CONFIRMED significa risultato riportato nel perimetro indicato, anche negativo, non verità universale.


### Round 1 — Full code scan — attribuzione storica congiunta R1–2

**Hypothesis:** La ricerca esaustiva dei codici può migliorare la memoria.

**What was tested:** Full brute-force code scan; l’allegato descrive R1–2 insieme, non assegna ogni prova a una round precisa.

**Datasets/protocol:** Protocollo, dataset e risultati grezzi non reperiti.

**Main results:** Troppo lento secondo la sintesi utente; nessun multiplo di costo verificabile.

**Decision:** REJECT

**What we learned:** Il costo della ricerca esaustiva rende inadeguata la linea testata.

**Do not repeat:** Full scan senza una nuova riduzione dimostrata del costo.

**Next implication:** Preferire aggregazioni e budget limitati.

**Evidence:** HISTORICAL_UNVERIFIED. **Sources:** Sintesi utente iniziale; raw/report originali assenti. R6: anche [BENCHMARKS.md](../../BENCHMARKS.md).


### Round 2 — Residual-guided search — attribuzione storica congiunta R1–2

**Hypothesis:** Guidare i candidati con il residuo riduce il lavoro.

**What was tested:** Residual-guided candidate search; numerazione individuale non ricostruibile.

**Datasets/protocol:** Solo sintesi utente R1–2; nessuna confirmation identificabile.

**Main results:** Riduceva il lavoro, ma non abbastanza; quantità non disponibili.

**Decision:** REJECT

**What we learned:** Ridurre i candidati non ha risolto il costo.

**Do not repeat:** Riaprire questa ricerca come novità dimenticando la chiusura storica.

**Next implication:** Distinguere ricerca dei codici da successive memorie residuali.

**Evidence:** HISTORICAL_UNVERIFIED. **Sources:** Sintesi utente iniziale; raw/report originali assenti. R6: anche [BENCHMARKS.md](../../BENCHMARKS.md).


### Round 3 — Multi-resolution residual memory

**Hypothesis:** Più risoluzioni possono rappresentare segnali mancanti.

**What was tested:** Memorie residuali multirisoluzione, XOR, interazioni, regressione continua.

**Datasets/protocol:** Dataset e split non recuperati; sintesi utente.

**Main results:** Miglioramenti qualitativi importanti; troppi livelli aumentavano collisioni e inference cost. Nessuna misura precisa disponibile.

**Decision:** PARTIAL

**What we learned:** La risoluzione utile va selezionata, non aggiunta sempre.

**Do not repeat:** Stack multirisoluzione fisso e illimitato.

**Next implication:** Valutare livelli con validation stopping.

**Evidence:** HISTORICAL_UNVERIFIED. **Sources:** Sintesi utente iniziale; raw/report originali assenti. R6: anche [BENCHMARKS.md](../../BENCHMARKS.md).


### Round 4 — Adaptive resolution and validation stopping

**Hypothesis:** Fermare livelli dannosi migliora il trasferimento.

**What was tested:** Risoluzione adattiva e stopping; caso diabetes citato.

**Datasets/protocol:** Solo storia utente, non una replica indipendente.

**Main results:** Esito qualitativo positivo; diabetes beneficiava dello stop anticipato.

**Decision:** ACCEPT

**What we learned:** Il principio è incorporato nel core attuale; la misura storica non è ricostruibile.

**Do not repeat:** Forzare tutti i livelli indipendentemente dalla validation.

**Next implication:** Condividere il preprocessing tra risoluzioni.

**Evidence:** HISTORICAL_UNVERIFIED. **Sources:** Sintesi utente iniziale; raw/report originali assenti. R6: anche [BENCHMARKS.md](../../BENCHMARKS.md).


### Round 5 — Shared encoding

**Hypothesis:** Un solo encoding fine evita trasformazioni ripetute.

**What was tested:** Encoding condiviso e mappe coarse-to-fine.

**Datasets/protocol:** Sintesi utente; l’adozione è verificata nel codice pubblico.

**Main results:** Preprocessing circa −58%; ~97,5% del gain adaptive conservato; memoria inferiore. La frase storica «inference circa 1.265x il vecchio baseline» ha orientamento ambiguo e NON è normalizzata come speedup verificato.

**Decision:** ACCEPT

**What we learned:** Primo grande miglioramento di efficienza secondo la storia; implementazione attuale confermata.

**Do not repeat:** Encoder completi separati per ogni livello senza nuova motivazione.

**Next implication:** Congelare e confrontare il core con boosting.

**Evidence:** HISTORICAL_UNVERIFIED. **Sources:** Sintesi utente iniziale; raw/report originali assenti. R6: anche [BENCHMARKS.md](../../BENCHMARKS.md).


### Round 6 — Frozen release benchmark

**Hypothesis:** Valutare qualità e sistemi del candidato v0.1.0.

**What was tested:** Base, HistGradientBoosting e LightGBM budget-matched.

**Datasets/protocol:** 12 dataset, 5 split, 240 run; BENCHMARKS.md precisa 9 sintetici e 3 reali. Raw archive originale non presente.

**Main results:** Quality wins 0/12; fit 5/12, inference 10/12, memoria 12/12. Rapporti LightGBM/CodAdapt: fit 0.887x, inference 1.258x, memoria retained 8.830x; nessuna stable win. Delta «accuracy» −0.003840 solo nell’allegato, metrica aggregata non sufficientemente definita: non trattarlo come AUC.

**Decision:** DIAGNOSTIC ONLY

**What we learned:** Profilo compatto e spesso rapido, senza superiorità predittiva dimostrata.

**Do not repeat:** Confondere il sanity runner pubblico con la riproduzione di R6.

**Next implication:** Audit diretto e nuova baseline R7.

**Evidence:** HISTORICAL_DISCLOSURE. **Sources:** Sintesi utente iniziale; raw/report originali assenti. R6: anche [BENCHMARKS.md](../../BENCHMARKS.md).


### Round 7 — Numeric interpolation / residual proposal / capacity

**Hypothesis:** A interpolazione e B proposta residual-aware possono migliorare Base.

**What was tested:** A, B, C capacity allocation e combinazioni; audit del codice.

**Datasets/protocol:** 18 dataset: 5 reali, 13 sintetici; 5 split. Confirmation interleaved di timing sugli stessi dati, non unseen.

**Main results:** A+B +0.027688 AUC, RMSE ridotto 5.30%; fit/predict/pickle 1.510/1.226/1.009x. Gap AUC LightGBM −0.058450→−0.005409; gap RMSE +8.23%→+4.07%. XOR ~0.50→~0.995.

**Decision:** PARTIAL

**What we learned:** Proposta debole sui sintetici; nessuna stable real-data win contro LightGBM.

**Do not repeat:** Promuovere A+B/C sulla batteria synthetic-heavy.

**Next implication:** Nuovi dati e integrazione A→B.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round7_findings.md](../../research_private/round7_findings.md)


### Round 8 — Interaction refit after interpolation

**Hypothesis:** Rifittare B sulla rappresentazione A corregge il disallineamento.

**What was tested:** Base/A/B/AB e A_refit_B, scaffold/budget controllati.

**Datasets/protocol:** 18 development; 12 nuovi studi empirici ×5; Energy simulato separato dai gate.

**Main results:** Confirmation AUC −0.002013; RMSE ridotto 3.97%; fit 2.650x, predict 1.058x, pickle 1.010x. Gap LGBM −0.014917 AUC / +10.18% RMSE.

**Decision:** REJECT

**What we learned:** Il piccolo recupero regressivo non giustifica il costo e la perdita classification.

**Do not repeat:** Refit costoso come candidato pubblico senza nuovo motivo.

**Next implication:** Gating limitato, poi abbandonato R9.

**Evidence:** CONFIRMED. **Sources:** [research_private/round8_findings.md](../../research_private/round8_findings.md)


### Round 9 — Adaptive optional modules

**Hypothesis:** Attivare A/B solo quando validation migliora evita perdite.

**What was tested:** Gate su Base/A/B/AB; nessun refit dopo A.

**Datasets/protocol:** 10 nuovi reali (5+5) ×5 split; gate separato.

**Main results:** Base 35/50, A 7, B 5, AB 3; A inclusivo 10/50, B 8/50. Fit 4.883x; regression adaptive +5.69% RMSE peggiore di LGBM. Base +0.014272 AUC vs LGBM su soli 5 studi.

**Decision:** REJECT

**What we learned:** Rifiutare moduli evita deployment cost, non il training già pagato.

**Do not repeat:** Adaptive A/B gating con gli stessi candidati.

**Next implication:** Verificare il favorevole classifier su più dati.

**Evidence:** CONFIRMED. **Sources:** [research_private/round9_findings.md](../../research_private/round9_findings.md)


### Round 10 — Classifier freeze / local-linear cells

**Hypothesis:** Verificare il classifier e correggere la regressione localmente.

**What was tested:** Base/LGBM/HGB; local-linear memory da statistiche aggregate.

**Datasets/protocol:** 20 nuovi classification ×5; 13 reali regression noti +14 controlli sintetici.

**Main results:** Classifier gap LGBM −0.008098 AUC, CI [−0.024354,+0.007917], 0/20 stable wins. Local-linear RMSE ridotto 0.92%; fit/predict/memory 1.271/1.363/1.015x. Famiglie nonlinearità 43.6%, interazioni 39.2% del gap positivo aggregato.

**Decision:** REJECT

**What we learned:** Il risultato classifier R9 non replica; quote famiglie descrittive, non decomposizione causale.

**Do not repeat:** Local-linear nelle celle o rivendicare superiorità classifier generale.

**Next implication:** Studiare le interazioni con controlli reali.

**Evidence:** CONFIRMED. **Sources:** [research_private/round10_findings.md](../../research_private/round10_findings.md)


### Round 11 — Pair-memory and nonlinear refinement

**Hypothesis:** Poche coppie e raffinamenti locali possono correggere residui.

**What was tested:** Pair, refinement e combinazione.

**Datasets/protocol:** Development noto/sintetico; 10 nuovi reali regression ×5.

**Main results:** Combinazione: development RMSE ridotto 0.46%; confirmation 0.00%; gap LGBM +1.77%; fit/predict/memory 1.191/1.005/1.039x; collisioni 0%.

**Decision:** REJECT

**What we learned:** Forti guadagni sintetici non trasferiscono.

**Do not repeat:** Confondere assenza di collisioni con generalizzazione.

**Next implication:** Diagnosi di coverage e validation transfer.

**Evidence:** CONFIRMED. **Sources:** [research_private/round11_findings.md](../../research_private/round11_findings.md)


### Round 12 — Proposal coverage and transfer

**Hypothesis:** Il limite può essere proposta o selezione, non capacità.

**What was tested:** Budget candidati, supporto, uncertainty penalty, test oracle solo diagnostico.

**Datasets/protocol:** Dati già osservati; nessuna confirmation indipendente.

**Main results:** True recall 76.7%@128,86.7%@512; rank mediano 1. Pearson 0.535, Spearman 0.387; validation-positive/test-negative 43.4%; oracle gap ~1.18 punti RMSE.

**Decision:** DIAGNOSTIC ONLY

**What we learned:** Limite misto; uncertainty penalty troppo conservativa.

**Do not repeat:** Usare l’oracle test per admission o aumentare candidati come cura generale.

**Next implication:** Admission indipendente R13.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round12_findings.md](../../research_private/round12_findings.md)


### Round 13 — Independent admission validation

**Hypothesis:** Una validation separata può migliorare la scelta delle coppie.

**What was tested:** A corrente, B indipendente, C subsplit, D consenso; candidati congelati.

**Datasets/protocol:** 10 nuovi reali regression ×5. Best-of-four descrittivo, non seconda confirmation.

**Main results:** D: harmful 6/28=21.4%, gain positivo retained 87.5%, RMSE ridotto 0.48%; fit/predict/memory ~1.159/1.001/1.008x. B harmful 36.4%; nessun CI dataset D esclude zero.

**Decision:** REJECT

**What we learned:** La reuse della validation non basta a spiegare l’instabilità.

**Do not repeat:** Pair ranking/admission e soglie sullo stesso cohort.

**Next implication:** Chiudere sparse pair-memory.

**Evidence:** CONFIRMED. **Sources:** [research_private/round13_findings.md](../../research_private/round13_findings.md)


### Round 14 — Shared low-rank coded interactions

**Hypothesis:** Condivisione dei parametri può generalizzare meglio delle coppie isolate.

**What was tested:** Ranghi 2/4/8, ridge coordinate updates; rank 8 congelato.

**Datasets/protocol:** 55 development (33 reali), 11 nuovi reali regression ×5.

**Main results:** Development gain 0.46%, confirmation 0.00%; fit/predict/memory 1.951/0.993/1.021x; active-only predict 1.255x, memory 1.249x. Nessun vantaggio mediano rispetto pair-memory.

**Decision:** REJECT

**What we learned:** Fallback rende economica la mediana ma non prova utilità; non è un’impossibilità di tutti i low-rank.

**Do not repeat:** Stessi ranghi/solver con nuova denominazione.

**Next implication:** Validazione esterna del core frozen.

**Evidence:** CONFIRMED. **Sources:** [research_private/round14_findings.md](../../research_private/round14_findings.md)


### Round 15 — Frozen core external validation

**Hypothesis:** Esiste una nicchia predittiva riproducibile di Base?

**What was tested:** Base/LGBM/CatBoost/XGBoost/HGB; piccolo tuning validation per boosting.

**Datasets/protocol:** 27 nuovi reali:15 binary,12 regression ×5; massimo 30k righe/166 feature.

**Main results:** Gap tuned LGBM −0.020297 AUC, −3.848% RMSE (Base migliore, CI include zero). CatBoost ~8.26% RMSE migliore di Base. Win/tie/loss9/2/16; fit19/27,inference24/27,pickle24/27. 1 stable LGBM win su bankruptcy50, 0 contro tutti i riferimenti.

**Decision:** PARTIAL

**What we learned:** Criterion B: forza nei sistemi, nessuna nicchia predittiva generale; metadata associations non sopravvivono Holm.

**Do not repeat:** Usare un singolo comparator o il caso50 righe per promuovere qualità.

**Next implication:** Quality/resource matching R16.

**Evidence:** CONFIRMED. **Sources:** [research_private/round15_findings.md](../../research_private/round15_findings.md)


### Round 16 — Quality-matched Pareto frontier

**Hypothesis:** Il vantaggio di sistemi sopravvive a qualità comparabile?

**What was tested:** 24 configurazioni tree per split, resource caps, batch/scaling.

**Datasets/protocol:** Stessi27 studi R15 ×5;3375 fit principali,50 scaling attempts (48ok). Non nuova confirmation.

**Main results:** Non-dominato quality/inference14/27; in≥4 fold11/27; joint20/27 (15/27 robusti). Strict quality matches all5 solo10 studi, test-mean match3 per latency/memory, CI-equivalent0. Strict selected latency1.084x e memory2.293x: niente vantaggio generale quality-matched.

**Decision:** PARTIAL

**What we learned:** Una frontiera finita point-estimate non è superiorità Pareto stabile.

**Do not repeat:** Ripetere wins di velocità senza quality matching/denominatori.

**Next implication:** Ricerca controllata di alternative, senza promozione.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round16_findings.md](../../research_private/round16_findings.md)


### Round 17 — Algorithm discovery lab

**Hypothesis:** Nuove rappresentazioni possono superare il core.

**What was tested:** 23 varianti/15 famiglie, basi, Nyström, neighbor/backoff e blend.

**Datasets/protocol:** 25 pattern×2task×3 seed;13 real×3 screen;10 nuovi×5 confirmation;4336 fit totali.

**Main results:** Primary joint_basis+Nyström: dev +0.015636 AUC/+6.839% RMSE; confirmation +0.000852 AUC, RMSE peggiore1.462%, CI entrambi zero incluso. Fit/predict/memory0.795/1.227/0.570x. Joint_basis solo memory0.061x ma perdite regressive stabili.

**Decision:** REJECT

**What we learned:** Screen vincente non replica; basso costo non implica sostituto a pari qualità.

**Do not repeat:** Riaprire lo stesso catalogo o promuovere il runner-up osservato sul test.

**Next implication:** Nuove ipotesi bounded, non ensemble post-test.

**Evidence:** FAILED TO REPLICATE. **Sources:** [research_private/discovery/DISCOVERY_REPORT.md](../../research_private/discovery/DISCOVERY_REPORT.md)


### Round 18 — Unexplored algorithms and auto preprocessing

**Hypothesis:** Preprocessing automatico e famiglie nuove possono dare robustezza.

**What was tested:** 8 varianti/6 direzioni,4 policy,27 strategie; isotonic@fixed primary.

**Datasets/protocol:** 18development×3;10 nuovi UCI (5+5)×5; provenance audit.

**Main results:** Confirmation AUC gain0.000000, RMSE peggiore18.186%; fit/predict/memory2.432/1.647/0.884x. LGBM gap RMSE+65.14%, CatBoost+44.73%.

**Decision:** REJECT

**What we learned:** Classification development non replica; automatic preprocessing non dimostrato robusto.

**Do not repeat:** Rescreen generale delle stesse trasformazioni o automata ricodificato come novità.

**Next implication:** Diagnosi del ceiling prima di altre architetture.

**Evidence:** FAILED TO REPLICATE. **Sources:** [research_private/discovery2/DISCOVERY2_REPORT.md](../../research_private/discovery2/DISCOVERY2_REPORT.md)


### Round 19 — Capacity ceiling / oracle diagnosis

**Hypothesis:** Il limite è capacità, encoder o fitting?

**What was tested:** Collision-free, più bin, all-pairs/triples, no-budget, refit/convex, truth oracle sintetico.

**Datasets/protocol:** 12vecchi piccoli reali×3;25 pattern×2×3;4722 fit. Oracle envelope test non deployabile.

**Main results:** No-budget convex +0.013533 AUC/+2.913% RMSE, fit14.51/11.51x. Identica struttura20 sweep +2.203% RMSE; fit1.729x. All-pairs senza refit −5.220% gain, con refit +3.246%. Collision-free +0.452%; bin512/2048 peggiorano ~11%.

**Decision:** DIAGNOSTIC ONLY

**What we learned:** Più capacità da sola non basta; fitting/stopping contano. Non è un ceiling universale.

**Do not repeat:** Promuovere test oracle/envelope (+0.018602AUC/+6.416% RMSE) o full all-pairs senza costi.

**Next implication:** Pochi passaggi cached sulla stessa struttura.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round19_findings.md](../../research_private/round19_findings.md)


### Round 20 — Fast backfitting

**Hypothesis:** Pochi passaggi recuperano il margine a costo limitato.

**What was tested:** 1/2/4/8/20 pass, due ordini, stopping validation;1 pass A selezionato.

**Datasets/protocol:** 17 real noti+25sintetici×5;12 nuovi regression×5.

**Main results:** Development +0.709% RMSE; confirmation +0.047%, CI[−0.024,+0.486]%; fit/predict/memory1.433/0.993/1.000x. 20 pass vecchio subset ora +1.026%, non2.20%.

**Decision:** REJECT

**What we learned:** Tempi passano, qualità no; cache non ripara trasferimento. Protocollo/inizializzazione differiscono da R19.

**Do not repeat:** Pass-count tuning sul cohort osservato.

**Next implication:** Ultima diagnosi congiunta a struttura fissa.

**Evidence:** FAILED TO REPLICATE. **Sources:** [research_private/round20_findings.md](../../research_private/round20_findings.md)


### Round 21 — Joint memory optimization

**Hypothesis:** Obiettivo globale sui valori fissi recupera qualità.

**What was tested:** Coordinate/block CD, PCG e LSQR oracle; CD interaction penalty cap 4 scelto.

**Datasets/protocol:** 29 real+25sintetici development;12 nuovi regression×5.

**Main results:** Development +1.3984%; confirmation +0.5650% CI[0.2527,2.2157]%; fit1.5783x, predict1.0055x, memory1.000x. Oracle stesso schema +0.6798%; LGBM gap+0.7605→+0.3704%, CatBoost+11.410→+6.515%.

**Decision:** REJECT

**What we learned:** Ottimizzazione più esatta di questo problema non genera un ampio guadagno di test.

**Do not repeat:** Confondere convergenza/training objective con generalizzazione.

**Next implication:** Interrompere tuning dei valori Base; controlli alternativi.

**Evidence:** CONFIRMED. **Sources:** [research_private/round21_findings.md](../../research_private/round21_findings.md)


### Round 22 — Paradigm break

**Hypothesis:** Rappresentazioni diverse possono avere una frontiera migliore.

**What was tested:** Supervised states, conditional states, prototypes, discrete dictionary, Boolean spectrum.

**Datasets/protocol:** 60case micro;3 seed second screen;12 nuovi (6+6)×5 confirmation.

**Main results:** D dictionary primary: AUC−0.008363, RMSE peggiore10.453%; fit/predict/memory0.950/0.908/0.278x. C prototypes−0.012704AUC, RMSE peggiore16.44%. Additive control stesso debole:−0.013847AUC/−24.40% gain.

**Decision:** REJECT

**What we learned:** Un additive scaffold debole confonde la prova delle interazioni.

**Do not repeat:** Rilanciare queste cinque implementazioni senza un controllo main adeguato.

**Next implication:** Strong additive control R23.

**Evidence:** CONFIRMED. **Sources:** [research_private/round22_findings.md](../../research_private/round22_findings.md)


### Round 23 — Strong additive control

**Hypothesis:** Il main-effect engine spiega parte del gap.

**What was tested:** Ridge/linear, spline, GAM, EBM, isotonic, piecewise; Base/main-only/strong/hybrid.

**Datasets/protocol:** 12vecchi reali+10 synthetic×2;12 nuovi (6+6)×5;pool scelto per-fit su validation.

**Main results:** Strong additive +0.011443AUC/+6.57% RMSE; aligned hybrid +0.011209/+7.98%, regression CI[3.88,17.16]%. Sopra strong, interazioni −0.000059AUC/+0.67% RMSE. Strong fit25.168x, hybrid26.945x.

**Decision:** PARTIAL

**What we learned:** Main effects sono priorità empirica, non prova che interazioni siano risolte. GAM più scelto20/60; nessun vincitore globale preregistrato.

**Do not repeat:** Rieseguire R23 per scegliere a posteriori EBM come vincitore; numeri frozen.

**Next implication:** Controllo nativo singolo, poi distillazione.

**Evidence:** CONFIRMED. **Sources:** [research_private/round23_findings.md](../../research_private/round23_findings.md)


### Round 24 — Native additive core

**Hypothesis:** Un unico core spline nativo può sostituire il pool costoso.

**What was tested:** Spline16 knots, penalized solve/logistic L-BFGS, compile polinomi; nessun fit interazioni.

**Datasets/protocol:** 220 split R23 riusati, incluso ex-confirmation ora development; nessun nuovo dato.

**Main results:** Ex-confirmation +0.009743AUC, RMSE peggiore1.44%; fit3.067/2.203x, predict1.658/1.629x, memory0.235/0.214x C/R.

**Decision:** REJECT

**What we learned:** Classificazione parzialmente riprodotta; grandi perdite temporali regression, extrapolation ipotesi non causalmente provata.

**Do not repeat:** Promuovere il singolo GAM come equivalente al pool o chiamare nuova confirmation dati R23.

**Next implication:** Separare apprendimento delle forme dalla loro rappresentazione.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round24_findings.md](../../research_private/round24_findings.md)


### Round 25 — Additive shape distillation

**Hypothesis:** Le shape forti possono essere memorie compatte.

**What was tested:** EBM fisso, shared grid4/8/16 nodes; primary16 e hybrid esistente.

**Datasets/protocol:** 12 nuovi reali×5;teacher train-only;16 nodi preregistrati, non scelti sul test.

**Main results:** Teacher +0.016462AUC/+22.50% RMSE; student +0.017995/+10.61%. Teacher-positive recovery97.73/68.96%;predict 0.996/0.938x, memory0.341/0.405x C/R. Teacher fit10.81/14.68x, total12.16/16.25x.

**Decision:** PARTIAL

**What we learned:** Classification rappresentabile; regression perde forme nella griglia. Joint gate fallito.

**Do not repeat:** Nascondere costo teacher o chiamare recovery rapporto delle mediane.

**Next implication:** Diagnosi di compressione per-feature.

**Evidence:** CONFIRMED. **Sources:** [research_private/round25_findings.md](../../research_private/round25_findings.md)


### Round 26 — Additive compression diagnosis

**Hypothesis:** Boundary placement e shared grid causano la perdita.

**What was tested:** Dense, shared4–64,quantile/adaptive/greedy knots, constant/linear, total256/512/1024.

**Datasets/protocol:** R25 development×5;12 nuovi×5;constant512 congelato.

**Main results:** Development regression recovery: dense99.92%,shared16 68.96%,quantile16 95.46%,adaptive-linear16 102.57%,greedy-constant16 99.26%. Confirmation ~100% teacher gain conservato; teacher RMSE gain solo1.48%, non5%. Predict0.684/0.544x, memory0.090/0.257x.

**Decision:** PARTIAL

**What we learned:** Rappresentazione sufficiente per teacher di questi dati; cap 512 non vincolante, non garanzia wide.

**Do not repeat:** Aggiungere nodi sopra codici già collassati; confondere fedele con migliore di Base ovunque.

**Next implication:** Tentativo direct learning, successivamente chiuso.

**Evidence:** CONFIRMED. **Sources:** [research_private/round26_findings.md](../../research_private/round26_findings.md)


### Round 27 — Direct adaptive additive learning

**Hypothesis:** Imparare le stesse forme senza teacher.

**What was tested:** Microbins, aggregate residual/Newton updates, greedy merging, zeroing;128 bins16 states shrink 20 penalty.002 1 pass.

**Datasets/protocol:** 24 noti×5 dev;15 nuovi (7C/8R)×5.

**Main results:** Confirmation AUC−0.020751;RMSE peggiore1.2916%;logloss peggiore4.77%. Fit1.544/1.011x, predict 0.336/0.464x, memory0.0477/0.0741x.

**Decision:** REJECT

**What we learned:** Molto economico ma non riproduce qualità EBM; spiegazione underfit da verificare.

**Do not repeat:** Promuovere risparmi derivanti da feature azzerate ignorando perdita di qualità.

**Next implication:** Ablation development only.

**Evidence:** CONFIRMED. **Sources:** [research_private/round27_findings.md](../../research_private/round27_findings.md)


### Round 28 — Direct training diagnosis

**Hypothesis:** Shrinkage, passes, merging o zeroing distruggono qualità?

**What was tested:** Ablation sequenziale; reverse/nozero/unregularized8 diagnostici.

**Datasets/protocol:** 24 noti(12+12)×5;nessuna nuova confirmation.

**Main results:** Best shrink 20,2 pass, penalty.0005,weak merging: +0.003014AUC/+0.6425% RMSE, CI includono zero. Unregularized8 trainMSE0.702x ma validation1.221x, testRMSE peggiore5.27%.

**Decision:** REJECT

**What we learned:** Rimuovere regolarizzazione migliora train e peggiora trasferimento; gate fallisce.

**Do not repeat:** Ulteriori sweep identici o aumentare passaggi come cura.

**Next implication:** Diagnosi feature-shape.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round28_findings.md](../../research_private/round28_findings.md)


### Round 29 — Feature shape transfer diagnosis

**Hypothesis:** Variance, confounding o leakage spiegano forme diverse?

**What was tested:** Teacher/direct/Base su stessa griglia; bootstrap/halves/sample10–100%;raw/residual/OOF.

**Datasets/protocol:** 24 noti×5;2070 feature/model/split,3864stability,2200sample-size rows.

**Main results:** Causa G mixed; low support/error Spearman−0.384R/−0.195C. OOF riduce shape MSE ma test-loss benefit CI include zero; harmful C15.2→17.5%,R24.3→21.6%. Teacher/direct correlation C/R 0.987162/0.909236; bootstrap teacher/direct C0.897/0.936,R0.864/0.800, con CI differenze che includono zero. Sample-size10→100%: shape NMSE C0.786→0.114,R0.709→0.532 su tre studi per task; residuo regressivo persiste.

**Decision:** DIAGNOSTIC ONLY

**What we learned:** Finite-sample e amplitude/formulation bias plausibili; leakage dominante non dimostrato, teacher non ground truth.

**Do not repeat:** Riaprire cross-fitting come cura già confermata.

**Next implication:** Tre ipotesi mirate: smoothing, honest discovery, amplitude; poi testate R30–31.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round29_findings.md](../../research_private/round29_findings.md)


### Round 30 — Support-aware shape learning

**Hypothesis:** Smoothing delle statistiche riduce errore low-support.

**What was tested:** Local/global/combined smoothing, treintensità; local 1 scelto.

**Datasets/protocol:** 24 noti×5;nessuna confirmation:gate fallito.

**Main results:** +0.004432AUC/+0.915535% RMSE; fit0.948/2.025x, predict 0.676/0.631x, memory0.101/0.122x. Low-support R shape MSE ridotta8.60%, non cura completa.

**Decision:** REJECT

**What we learned:** Contributo del rumore supportato, guadagno troppo piccolo.

**Do not repeat:** Continuare sweep intensità smoothing.

**Next implication:** Tenere confini fissi per isolare valori/ampiezza.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round30_findings.md](../../research_private/round30_findings.md)


### Round 31 — Fixed states, value estimation

**Hypothesis:** Valori/ampiezza sbagliati sono correggibili a stati fissi.

**What was tested:** Mean, ridge, EB, fold-out, alpha global/per feature, separate discovery/estimation.

**Datasets/protocol:** 24 noti×5;alpha_feature passa gateC+0.005210,poi12 nuovi×5.

**Main results:** Confirmation +0.001880AUC/+0.559588% RMSE; fit4.069/4.417x. Amplitude error ridotta solo0.249/2.044%;shape correlation0.8284/0.7766.

**Decision:** REJECT

**What we learned:** Calibrazione non salva il learner; confini restano una spiegazione non isolata.

**Do not repeat:** Ritocchi amplitude/value shrinkage con stessi stati e dati.

**Next implication:** Ultimo test globale, poi chiusura.

**Evidence:** FAILED TO REPLICATE. **Sources:** [research_private/round31_findings.md](../../research_private/round31_findings.md)


### Round 32 — Global shape optimization

**Hypothesis:** Fitting globale regolarizzato può superare stima locale.

**What was tested:** Ridge/first/second differences,32/64 bins, lambda.001/.01;L-BFGS con bincount, senza matrice one-hot enorme.

**Datasets/protocol:** 24 noti×5;1440global fits convergenti; nessuna confirmation.

**Main results:** Selected second 64 lambda.01: AUC−0.003744,RMSE peggiore2.484%,logloss peggiore0.896%. Fit1.082/1.975x, predict 0.842/0.900x, memory0.217/0.361x. Tutte12 varianti sotto zero per mediane qualità.

**Decision:** REJECT

**What we learned:** Chiudere la linea compact direct-learning testata, non dimostrazione di impossibilità matematica.

**Do not repeat:** R27–32 con ulteriori tuning locali/globali senza nuova evidenza.

**Next implication:** Compiler offline teacher-trained.

**Evidence:** EXPLORATORY. **Sources:** [research_private/round32_findings.md](../../research_private/round32_findings.md)


### Round 33 — Model compilation into coded memory

**Hypothesis:** Compilare un teacher forte ed eliminarlo al deployment.

**What was tested:** EBM/LGBM/CatBoost fissi; additive+0/1/2/3residual codebooks; EBM 0 selezionato.

**Datasets/protocol:** 24 noti×5 dev;15 nuovi (7C/8R)×5 confirmation.

**Main results:** Teacher/compiled +0.016102AUC, +7.116/+7.115% RMSE; recovery100/100% su4/7C e6/8Rteacher-positive. NMSE3.32e−16/7.38e−16. Totalfit19.289/23.425x, predict 0.395/0.666x, memory0.073/0.225x Base.

**Decision:** PARTIAL

**What we learned:** EBM additivo comprimibile; non dimostrato trasferimento generale di interazioni tree.

**Do not repeat:** Chiamare il compiler nuovo learner diretto o nascondere fit teacher.

**Next implication:** Deployment grande/wide.

**Evidence:** CONFIRMED. **Sources:** [research_private/round33_findings.md](../../research_private/round33_findings.md)


### Round 34 — Compiled deployment validation

**Hypothesis:** Il budget512 è sufficiente e utile su grande scala?

**What was tested:** Cinque fonti nuove, nove stresscase, Power10k–600k, wide e categoriche; layout ottimizzato.

**Datasets/protocol:** Un split per case, teacher fisso; scalePower non studi indipendenti.

**Main results:** Power600k NMSE~1e−16,serialized0.219x EBM, single0.343x; large batch>2x teacher. Gas AUC−0.033282;Blog280/SECOM590/Diabetes47 non compilabili nel budget.

**Decision:** REJECT

**What we learned:** Equivalenza runtime ottimizzato/student non implica fidelity teacher;512 non universale.

**Do not repeat:** Deployment lossy silenzioso o omettere casi non compilabili.

**Next implication:** Exact compiler e pre-flight.

**Evidence:** CONFIRMED. **Sources:** [research_private/round34_findings.md](../../research_private/round34_findings.md)


### Round 35 — Safe compiler and capacity

**Hypothesis:** Capacità auditata e verify possono impedire export degradati.

**What was tested:** Exactcompile, float64,preflight SAFE/WARNING/REJECT, uniform error bound, curve128–8192+exact.

**Datasets/protocol:** 5 teacher R34+Mfeat649nuovo;6 modelli,48budget attempts; validation-only admission.

**Main results:** Exact6/6fedele;14/48ammessi,34/48rifiutati,0false-safe. StatiPower428,Gas13275,Diabetes2802,Blog4816,SECOM24813,Mfeat33488. Single speedup3.24x; large1.59x; pickle0.193x, deep0.246x EBM.

**Decision:** PARTIAL

**What we learned:** Gas perdeva per compressione/capacità, non inevitabile errore della rappresentazione esatta.

**Do not repeat:** 512 states fissi per tutti o interpretare minimo formato come minimo teorico.

**Next implication:** Ottimizzazione runtime senza cambiare funzione.

**Evidence:** CONFIRMED. **Sources:** [research_private/round35_findings.md](../../research_private/round35_findings.md)


### Round 36 — Fast compiled runtime

**Hypothesis:** Ottimizzare esecuzione e categoriche mantenendo i bit.

**What was tested:** Contiguità, buffers, layout, cache categoriale schema-bounded, ordered accumulation.

**Datasets/protocol:** Stessi6 teacherSAFE; batch1/8/32/128/1k/10k/100k;221241 boundaryprobe.

**Main results:** Single4.19x piùrapido;1k0.717x;100k1.360x; deep0.238x EBM. Bitwise6/6;0 nuovifalse-safe; Diabetes categorical migliorato, numeric searchsorted+gather residuo.

**Decision:** PARTIAL

**What we learned:** Categoria→codice diretto evita oggetti Python per riga; batch grande resta limite.

**Do not repeat:** Cambiare categoriche/predizioni per vincere timing o usare np.sum non ordinato.

**Next implication:** Confronto kernels numerici R37.

**Evidence:** CONFIRMED. **Sources:** [research_private/round36_findings.md](../../research_private/round36_findings.md)


### Round 37 — Fast numeric discretizer

**Hypothesis:** Un kernel numerico specializzato può battere searchsorted.

**What was tested:** A–Gsearch/grouped/packed/binary/fewbin/coarse/uniform, gathers/layout; fix persistence buffer/views.

**Datasets/protocol:** Stessi6frozen; synthetic2–128 cuts, missing0/10/50%,1–100kbatch;126workerrecords; controllo alternato.

**Main results:** Bestsearchsorted; numeric0.999x speedup, gather0.973x. MedianlatencyEBM single0.274x,1k0.723x,100k1.099x; deep0.167x. 11,036,405 probe,0bucket/0predictionmismatch. Power100k2.627x, Gas1.482x, Diabetes1.206x.

**Decision:** PARTIAL

**What we learned:** Target mediani passano nella sessione ma paired R37/R36≈0.992–1.012: nessuna accelerazione algoritmica dimostrata. Persistenza senza copie duplicate è un guadagno strutturale.

**Do not repeat:** Attribuire il cambio1.360→1.099 al nuovo discretizzatore; altri sweepNumPy già perdenti.

**Next implication:** Kernel nativo esatto solo come prossimo esperimento preregistrato, non già eseguito.

**Evidence:** CONFIRMED. **Sources:** [research_private/round37_findings.md](../../research_private/round37_findings.md)


### Round 38 — Exact native numeric kernel

**Hypothesis:** un kernel CPU compilato può fondere exact bucket, gather e accumulo mantenendo identica la funzione EBM.

**What was tested:** C/Zig e Numba research-only; binary e count specializzato per <=8/16/32/>32 cut; stadi bucket, gather, fused; thread1/2/4/8. Small batch conserva Round37, categoriche immutate, somme per feature ordinate.

**Datasets/protocol:** stessi sei teacher SAFE; selezione solo sulla validation; tre sessioni fresche alternate,21ripetizioni warm, sette batch;150combinazioni sintetiche fino1Mrighe in streaming8192righe, non matrice residente. Nessun nuovo teacher né confirmation di qualità. Preflight/SAFE congelati.

**Main results:** Backend c; thread grandi 4; bucket/prediction mismatch0/0 su 12,465,430 probe numerici. Kernel bucket speedup0.739x, fused0.781x. End-to-end single/1k/100k vs EBM 0.271/1.218/3.648x; speedup100k vs R37 0.504x; deep0.170xEBM. Gate mediano FAIL. Throughput sintetico1Mrighe,20feature/64cut: 2,971,729righe/s. Questo valore esclude conversione applicativa.

**Decision:** REJECT per il nuovo adapter nativo. Nessuna promozione del package pubblico. Bottleneck: NO; readiness del ramo compiler precedente: PARTIALLY.

**What we learned:** La compilazione da sola non supera tutti i target; kernel-only e costo end-to-end devono rimanere distinti. Modello, cut, celle e ordine invariati; memoria DLL/JIT/processo distinta dalla deep del predictor.

**Measured diagnosis:** conversione input pari al 89.0% del tempo su SECOM e 89.8% su Mfeat nel profilo parallelo congelato. Kernel fused single-thread piu lento in 4/6 casi su buffer pronti. La policy globale a quattro thread non e raccomandabile: peggiora Power e Diabetes gia sulla validation. Non e una prova che ogni implementazione nativa debba fallire.

**Do not repeat:** altri sweep NumPy già chiusi; non aumentare automaticamente i thread o attribuire il percorso small-batch ereditato al kernel nativo. Non interpretare streaming sintetico come throughput end-to-end industriale.

**Next implication:** Feature-major native runtime with conversion isolation, proposta non eseguita.

**Evidence:** CONFIRMED nel perimetro dei sei teacher su questo host, non garanzia universale. **Sources:** [round38_findings.md](../../research_private/round38_findings.md), [protocol](../../research_private/round38/protocol.json), [manifest](../../research_private/round38/manifest.json).

### Round 39 — Feature-major zero-copy runtime

**Hypothesis:** feature-major native execution can avoid row-major conversion and fuse exact bucket/lookup/ordered accumulation on contiguous columns.

**What was tested:** frozen R37 NumPy; R38 native row-major one thread; feature-major copy; direct columns; explicit persistent snapshots. Validation selects D and one thread. Threads2/4 tested only after a single-thread improvement, then rejected by the per-workload guard. No teacher/cut/cell/category/SAFE/API changes.

**Datasets/protocol:** same six SAFE exports; two fresh processes per dataset, seven alternating repeats, seven batches. Actual frozen R37 ready-input control is used for gate A; reconstructed NumPy proxy is only diagnostic. Twelve full resident synthetic matrices up to1M×300, C/F/row-strided layouts, three repeats. Reused R38 edge probes, missing/unseen and teacher-blocked save/load.

**Main results:** Layout D, colonne contigue dirette quando possibile, single-thread. Ready-buffer vs R37 1.5007x; end-to-end vs R37 1.3367x. Batch100k/EBM 1.0331x; Power/Gas/Diabetes 2.2778/1.0194/1.2293x. Single/EBM 0.2878x; deep/EBM 0.1701x; conversion share 5.57%. Bucket/prediction mismatch 0/0; nuovi false-safe0 sui sei SAFE congelati. Gate PASS. Margine ready rispetto alla soglia1.5x 0.0458%; mediane per sessione {'1': 1.4717679786503473, '2': 1.53024342881784}. Passaggio eventualmente nominale, non prova robusta di replica; nessuna promozione pubblica.

**Decision:** PARTIAL_SYSTEMS_GATE_PASS. Native research continuation **YES**; compiler readiness **PARTIALLY**. Bottleneck **KERNEL**. No public promotion.

**What we learned:** input copies are observed rather than inferred from DataFrame/NumPy labels. Snapshot bytes are separate from predictor memory. A fast ready kernel is not automatically fast end-to-end; results are paired on this host, not compared with historical absolute timings.

**Do not repeat:** retuning equivalent kernels/layouts on these same test models, silently caching raw input identity, hiding resident input memory, claiming inherited small-batch performance as a new native gain.

**Next implication:** Independent validation of frozen column-direct runtime; proposed, not executed.

**Evidence:** CONFIRMED within measured host and six frozen exports; not independent general deployment confirmation. **Sources:** [round39_findings.md](../../research_private/round39_findings.md), [protocol](../../research_private/round39/protocol.json), [manifest](../../research_private/round39/manifest.json).

### Round 40 — Independent runtime replication

**Hypothesis:** frozen R39 layout D gains replicate temporally and transfer to workloads not used to select it.

**What was tested:** EBM, frozen R37 and frozen R39 D, one thread; three independent fresh-process sessions, shuffled workload order, alternating model order, seven batches,20 observations/model/path. No runtime optimization or model/cut/cell/SAFE/API changes.

**Datasets/protocol:** historical six exports plus seven new runtime workloads: Breast Cancer, California Housing, Phoneme, Adult, Bank, Clean1, Covertype. New fixed EBM teachers admitted SAFE before timing. Dataset novelty is relative to R39 runtime selection, not all previous predictive research. Same Windows host; no second machine. Covertype100k untiled holdout; small-dataset large batches explicitly tiled. Paired cycle-bootstrap95% CIs. Full original fidelity coverage, including12,009,816 numeric probes and72 resident scaling/layout cases up to1M×300.

**Main results:** Round39 replicated PARTIALLY. Historical ready/session [1.5097995780788627, 1.5223270633516743, 1.5121240266033158]; new ready/session [1.362480888455787, 1.385029012881379, 1.360380090821325]. Pooled ready 1.4323x, end-to-end 1.3457x, batch100k/EBM 1.0082x, single/EBM 0.2665x, deep/EBM 0.1857x. Historical complete gate PASS; new complete gate FAIL. R37 official research reference; R39 not promoted after independent replication. Power/Gas/Diabetes100k/EBM 2.1524/1.0082/1.2395x. Fidelity bucket/prediction/false-safe 0/0/0. Requested numerical gates pooled across13 datasets PASS; the conservative reference decision uses the additional preregistered separate-cohort transfer gate, not a claimed failure of pooled thresholds.

**Decision:** R37_REFERENCE_RETAINED_REPLICATION_GATE_FAIL. Experimental compiler readiness **PARTIALLY**. No public promotion, no commit/push.

**What we learned:** temporal replication, new-workload transfer and isolated ready-buffer improvement are distinct claims. Both cohorts must satisfy the full preregistered gate; an aggregate median does not establish universal serving performance. Small-row gains are inherited, not a new R39 improvement.

**Do not repeat:** equivalent kernel/layout retuning in response to these results; favorable reruns; reducing fidelity coverage; hiding Power/Gas/Diabetes or tiling/input-preparation costs.

**Next implication:** Validate an explicit small-batch/compact-memory deployment contract on independent hardware; keep R37 as reference and do not resume equivalent runtime tuning. Proposed, not executed.

**Evidence:** CONFIRMED within measured temporal/process and workload scope; hardware independence remains untested. **Sources:** [round40_findings.md](../../research_private/round40_findings.md), [replication](../../research_private/round40_replication.csv), [environment](../../research_private/round40_environment.json), [protocol](../../research_private/round40/protocol.md).

### Round 41 — Deployment envelope validation

**Hypothesis:** a supported output/schema/hardware/batch contract can distinguish FAST_SAFE, SAFE and REJECT without changing the frozen compiler or runtime.

**What was tested:** same13 frozen teacher/exports; official R37 and secondary R39 separately;7 batches;20 paired measurements/model/contract; separate fresh-process RSS. Both exact raw_score and prediction contracts tested. Twelve million numeric probes,65 negative admission checks, teacher-blocked persistence26 exports. No algorithms/cuts/cells/runtime/compiler/API changes.

**Main results:** Independent hardware replication NO; portable kit prepared and executed locally only, Linux build UNRUN. Official R37 exact raw-score contract: single-row 3.838xEBM, >=3x on 9/13; deep memory 0.182x, <=0.30 on 11/13; sampled peak RSS100k 0.597x. FAST_SAFE 84/91 observed model/batch cases, SAFE 7/91. No universal monotonic batch cutoff. Raw scores and frozen compiled predictions bitwise exact; strict teacher-probability contract REJECT for 10/13 models, max difference 2.22e-16. No runtime fix; this clarifies prior raw-score versus probability fidelity scope.

**Deployment envelope:** FAST_SAFE requires exact requested output and (>=1.5x latency OR <=0.50 deep memory), with latency/memory/both reason explicit. SAFE preserves exactness without performance guarantee. REJECT covers insufficient capacity, unsupported schema/model or unverified/failed requested fidelity. Feature/state counts, categorical and missing fractions are observed descriptors, not unseen performance guarantees. Memory-only FAST_SAFE is not throughput advice.

**Decision:** SCOPED_EXPERIMENTAL_RECOMMENDED_EXTERNAL_HARDWARE_PENDING. Can expose reliable scoped mode YES; v0.2 EXPERIMENTAL recommendation YES; default NO. R37 remains official research reference; R39 is not promoted or selected per workload. No public API implementation in this round.

**Recommended scope:** Opt-in exact binary logits and single-target regression; supported additive EBM schemas; target-host fidelity/profile before FAST_SAFE; no bitwise EBM probability guarantee.

**Limitations:** no independent host executed; Linux recipe untested; RSS1ms sampling may miss brief peaks, allocator/holdout costs disclosed; only observed combinations profiled. Bitwise EBM probability replacement excluded despite numerically tiny differences.

**Do not repeat:** reinterpret local packaging/container tests as independent hardware; infer universal throughput from a memory-only FAST_SAFE label; silently relax strict fidelity or optimize runtime in response.

**Next implication:** Run the supplied unchanged kit on independent hardware, validate target ABI/fidelity and scope per-host performance labels; then separately authorize public opt-in packaging. No new runtime optimization. Proposed, not executed.

**Evidence:** CONFIRMED_LOCAL_SCOPE, external hardware PENDING. **Sources:** [findings](../../research_private/round41_findings.md), [results](../../research_private/round41_results.csv), [envelope](../../research_private/round41_deployment_envelope.csv), [reproduction kit](../../research_private/round41_reproduction.zip).

### Round 42 — v0.2 compiler integration

**Hypothesis:** the verified additive EBM exporter can be integrated as a safe standalone opt-in public compiler without changing the native default.

**What was tested:** public API/preflight/post-verification, binary/regression/categorical/missing/capacity rejection, boundaries ±1ULP/NaN/infinities/signed zero, sklearn prediction semantics, pickle and installed-wheel teacher-blocked persistence; complete prior suite and distribution privacy. Frozen R37 artifacts reused only for parity, no closed round rerun.

**Main results:** 375 passed, 4 existing expected xfails, 0 failed/error; 25 real-EBM compiler tests; Ruff/format clean; wheel+sdist build and twine PASS; wheel and local source install PASS. Frozen cohort12/13 SAFE, raw bit mismatches0 against teacher and R37 across7 batch sizes; Diabetes47 REJECT because numerical category labels are outside the string-only public contract. Max probability difference2.22e-16, allowed absolute1e-15. All12 SAFE artifacts load/predict from installed wheel while interpret import is blocked.

**Decision:** INTERNAL_RC_READY, version0.2.0rc1 prepared after full tests; no publication/commit/push. Opt-in codadapt.experimental.compile_ebm(teacher, *, X_verify, max_states=None); interpret-core0.7.8 additive standard EBM only, binary/scalar regression; named DataFrames, real numeric and string categorical labels, supported missing/unseen. Exact raw/regression; numerical probability fidelity, not bitwise. Mandatory exact capacity/schema checks and heldout compile-then-verify. No teacher retained. Existing native API/default unchanged; standalone runtime ports frozen R37 ordered NumPy lookup and buffer persistence; no R38/R39 native backend.

**Limits:** local Python3.12 gate; cross-version GitHub CI configured but unrun. No independent hardware or remote install claim. Probability tolerance explicitly authorized by this round, not a retrospective relaxation of R41's strict bitwise experiment. Diabetes rejected instead of extending category coercion semantics.

**Do not repeat:** reopen native/direct-learning lines; promote R39 as universal runtime; infer speed from fidelity; publish research memory or call this a final release.

**Next implication:** Execute the configured Python3.10-3.12 CI matrix and unchanged deployment kit on independent hardware, review the candidate package, then authorize any release separately. Numeric categorical labels remain REJECT until separately tested/scoped. No default change or new optimization.

**Evidence:** CONFIRMED_LOCAL_INTEGRATION. **Sources:** [findings](../../research_private/round42_findings.md), [gate](../../research_private/round42/release_gate.json), [parity](../../research_private/round42/parity.json), [public contract](../EBM_COMPILER.md).

### Round 43 — Release candidate validation, local-only scope

**Hypothesis:** the candidate can be reproduced, installed and handed off as a clean source repository without changing its frozen implementation.

**Scope revision:** User explicitly replaced remote validation with local checks and final source artifacts. No GitHub install, dispatch, Kaggle/Colab/SSH execution, commit, push, tag or release. Earlier read-only GitHub inspection showed green Python3.10/3.11/3.12 jobs only for v0.1.0, not this RC; it is not RC evidence.

**What was tested:** two fresh isolated venvs, base and EBM extra; standalone persistence with interpret physically absent; full suite/Ruff, build/install and version checks from final ZIP extraction; archive allowlist, file hashes, privacy, frozen source hashes. Python3.12 only.

**Main results:** Local-only scope completed:375 passed,4 existing xfails,0 failed; Ruff/format clean; wheel+sdist rebuilt from the delivery ZIP; two fresh venvs with system-site-packages=false and isolated Python; base classifier/regressor, EBM compile+SAFE/REJECT and numerical fidelity PASS;16 pickle/joblib checks including12 historical exports in an environment where interpret is absent. Version/metadata0.2.0rc1 coherent. Clean folder+ZIP44 public files, no research/cache/venv/build output.

**Decision:** LOCAL_HANDOFF_READY_EXTERNAL_VALIDATION_EXCLUDED. Ready for requested source handoff YES; original external publication gate NOT EVALUATED. No new features or compiler fix. README/release notes clarified; local latest-DLL import issue avoided with a reproducible fixed stack, no OS policy modification.

**Do not repeat:** relabel v0.1.0 CI as RC CI, isolated venv as independent hardware, or prepared workflow as executed. No remote action under current instruction.

**Next implication:** User reviews and manually uploads the delivered source repository when desired. External CI/hardware remain unverified and are excluded from this task. Do not run them, publish, tag, commit or push without new instruction.

**Evidence:** CONFIRMED_LOCAL_INTEGRATION_ONLY. **Sources:** [findings](../../research_private/round43_findings.md), [CI scope](../../research_private/round43_ci.md), [checks](../../research_private/round43_external_validation.csv), [archive manifest](../../research_private/round43/package_manifest.json).

## 5. Ideas permanently rejected

**R39:** non adottare la policy globale a2/4thread: fallisce il guard di non-regressione per workload sulla validation. Nessuna promozione basata solo su ready-buffer o cache dello stesso input; non continuare tuning equivalente sui sei casi osservati.


**R38, scoped rejection:** non promuovere l'adapter nativo testato (conversione a blocchi, loop nativo row-major, pool per chiamata): il gate end-to-end non passa. Questo non rifiuta ogni futura esecuzione nativa. Riaprire solo con una diagnosi misurata del costo dominante e un nuovo protocollo congelato; non ripetere lo stesso adapter con altri teacher.


Chiusura operativa **nelle formulazioni testate**, non teorema di impossibilità. “Permanentemente” significa non ripetere senza nuova evidenza che soddisfi la condizione seguente. Nessuna voce è promossa.

| Direzione / round | Perché e su quale evidenza | Cosa deve cambiare |
|---|---|---|
| full scan / 1,2 | Costo storico eccessivo; nessuna confirmation grezza recuperata. | Una riduzione di complessità dimostrata, non hardware più veloce soltanto. |
| residual guided code search / 1,2 | Riduzione del lavoro storica insufficiente; distinta dal pair proposal R7. | Nuovo limite di costo verificabile con baseline identica. |
| fixed multi-resolution / 3,4 | Troppi livelli: costi/collisioni; validation stopping evita livelli dannosi. | Nuova prova che livelli fissi aggiungano qualità indipendente a pari costo. |
| adaptive module gating / 8,9 | R8 dodici nuovi e R9 dieci nuovi: costi2.65/4.883x senza qualità sufficiente. | Candidati realmente diversi e costo di selezione sostanzialmente minore. |
| local-linear memory / 10 | 13 realnoti:gain0.92%,predict1.363x; nessuna nuova confirmation regression. | Nuova stima/realizzazione sostenuta da controllo che risolva costo e trasferimento. |
| pair-memory line / 11,12,13 | 10 nuovi R11 gain0%;10 nuovi R13 gain0.48%,harmful21.4%. | Correzioni statisticamente diverse; non altro ranking/admission dello stesso schema. |
| low-rank interactions / 14 | 11 nuovi:gain0%,fit1.951x; active-only costi peggiori. | Nuova evidenza sull’apprendimento/statistical sharing oltre i ranghi già provati. |
| discovery catalog and automatic preprocessing / 17,18,22 | 10+10+12 nuovi:primary non replica o perde; controlli additive deboli. | Ipotesi specifica con scaffold adeguato e falsificazione prima del nuovo cohort. |
| fast backfitting and joint memory optimization / 20,21 | 12 nuovi ciascuno:gain0.047% e0.565%,sotto gate. | Dimostrare nuovo margine generalizzabile a struttura fissa, non solo training loss. |
| native additive spline replacement / 24 | Reimpiego R23:regression peggiore1.44%,predict~1.65x; nessuna nuova confirmation. | Separare extrapolation e funzione target con evidenza indipendente. |
| direct additive learner / 27,28,29,30,31,32 | R27 15 nuovi perde; R31 12 nuovi non salva; R32 dev negativo non autorizza confirmation. | Nuova spiegazione falsificabile del gap, non altra variazione di iperparametri. |
| smoothing sweep / 30 | Development24:gain0.004432AUC/0.916% RMSE, gate fallito; confirmation non eseguita. | Nuovo meccanismo causale, non intensità diverse dello stesso smoother. |
| amplitude calibration and fixed-state value estimation / 31 | 12 nuovi:0.001880AUC/0.560% RMSE, fit>4x. | Nuova evidenza su partizioni/identifiabilità che questa prova non isola. |
| global additive optimization / 32 | 1440 fit convergenti, gate dev fallito; nessuna confirmation. | Obiettivo o informazione diversa motivati, non solver più lungo sugli stessi bin. |
| fixed 512-state universal compiler / 34,35 | Gas degrada ewide falliscono; exact capacity fino 33488. | Budget guidato dall’audit già implementato R35,non comprimere a caso. |
| NumPy numeric kernel proliferation / 36,37 | Nessuna alternativa searchsorted vinceglobalmente; pairedruntime invariato. | Kernel realmente diverso nativo/esatto e benchmark interleaved preregistrato. |


## 6. Important discoveries

1. Shared encoding è stato il primo grande miglioramento di efficienza secondo storia R5; il riuso è verificabile oggi, gli effect sizes precisi restano storici.
2. Validation stopping evita aggiunta indiscriminata di livelli. R19–21mostrano inoltre che minimizzare meglio la loss di training non implica test migliore.
3. Più capacità non basta: all-pairs/raw e bin più fini possono peggiorare, zero collisioni non garantisce generalizzazione.
4. R23 localizza una debolezza main-effect, con opportunità empirica ma overhead enorme e pool eterogeneo.
5. Le funzioni EBM additive possono essere esportate quasi perfettamente. Shared grid rigida perde informazione; confini per-feature preservano gli step.
6. Imparare direttamente le stesse forme non è risolto: R27–32chiuse. La rappresentabilità non certifica una buona procedura di stima statistica.
7. Exact EBM richiede capacità sufficiente e dominio supportato; SAFE/REJECT+verify evita i casi lossy testati.
8. Il runtime ha vantaggi di memoria/single-row; miglioramento categorico R36 e persistenza R37 sono reali modifiche di esecuzione, non nuovi modelli.
9. Large-batch numerico e variabilità dei benchmark restano il principale problema di deployment; un buon aggregato non cancella Power/Gas/Diabetes.

## 7. EBM compiler branch

**R33→37 è export offline, non il core predittivo nativo.** Teacher fisso additive EBM, interpret-core0.7.8, interactions=0,max_bins128,outer_bags4,max_rounds1000,smoothing_rounds50,early_stopping_rounds50,n_jobs1; seed di split nelle prime round,34034nei teacher stress R34/35. L’early stopping teacher usa training-only. Training totale può essere costoso; non serve il teacher dopo compilation.

R33 ha scelto EBM+0residual codebooks globalmente prima della confirmation; nessuna selezione teacher dataset-specifica. LightGBM/CatBoost distillation e residual books non dimostrano trasferimento generale delle loro interazioni. R26/33inizialmente conservano float32 approssimati; R35 exact conserva float64 e ordine, unisce solo intervalli adiacenti con score identico, preservando missing/unknown.

Capacità esatta minima nel formato corrente: numerica =1+transizioni di score+missing+unknown; categorica =etichette+missing+unknown. Scala O(somma transizioni + cardinalità), non soltanto righe o numero feature. Non è un minimo teorico in byte. Stati≠picklebytes≠deepheap≠RSS.

| Teacher frozen | Feature | Exact states |
|---|---:|---:|
| Power600k |6|428|
| Gas128 |128|13275|
| Diabetes47 |47|2802|
| Blog280 |280|4816|
| SECOM590 |590|24813|
| MultipleFeatures649 |649|33488|

Preflight: SAFE: capienza sufficiente all’esatto; WARNING: capienza minima ma compressione necessaria; REJECT: schema non supportato o sotto minimo. **Sempre compile-then-verify** su training-heldout/validation, non test: raw max≤1e−6×(1+max|teacher raw|),NMSE≤1e−8,|ΔAUC|≤1e−5o|ΔRMSE relative|≤1e−4; inoltre somma conservativa dei massimi errori per-feature su tutti gli stati≤tolleranza. Fallimento→`NotSafelyCompilable`, nessun modello finale. R35:14/48 tentativiSAFE/ammessi,34/48reject,0false-safe;6/6exact. R36/37non aggiungono nuove ammissioni: zero nuovi false-safe non è un’altra prova su48 modelli.

Contratto: EBM univariato additivo ordinato, binary/single-target regression, score finiti e DataFrame/schema valido. Interazioni, multiclass, oggetti categorici arbitrari o input numerici invalidi sono rifiutati. Mancanti e unseen hanno stati esatti. Categorie scalar string/int/float/bool/bytes secondo normalizzazione auditata, non ogni oggetto Python. Non promettere compatibilità con qualunque futura versione EBM.

Categoriche R36: pandas categorical codes riutilizzati; cache al massimo uno schema per feature, invalidazione corretta; object fallback factorize e normalizzazione delle sole categorie distinte. Nessun oggetto Python per riga. Cache esclusa dal pickle, inclusa deep warm; thread check R36 copre128 chiamate/4 thread. Questa parte è ereditata invariata da R37.

Numeric R37: searchsorted resta vincente. Grouped search, packed edges, branch-reduced, fewcut/coarse/uniformexact non battono il riferimento end-to-end. Uniform shortcut sempre verificato sui cut con fallback. Gatheradvanced rimane preferito; float64 addition nello stesso ordine, mai somma riassociata. Batch≤32percorso R36;grandi feature loop/input nativo. Persistenza salva una sola volta buffer contigui e ricostruisce le viste al load; niente copia duplicata di celle.

| Risultato storico R37 | Valore |
|---|---:|
| Numeric speedup vs R36 |0.998600x (~0.999)|
| Gather speedup vs R36 |0.973009x|
| Single latency / EBM |0.274312x|
| Mediana single speedup |3.648796x (non reciproco esatto della mediana dei rapporti)|
| Batch1k latency / EBM |0.722776x|
| Batch100k latency / EBM |1.098764x|
| Deep retained / EBM |0.167248x|
| Probe numerici |11,036,405|
| Bucket/prediction mismatch |0 / 0|
| Nuovi false-safe |0|
| Power/Gas/Diabetes100k / EBM |2.627 / 1.482 / 1.206x|

Questi probe contano posizioni/scenari, non tutti valori distinti; non moltiplicare per il numero kernel. Test di cut esatti,±1ULP, NaN,±inf, estremi; uint64bit check, holdout completi, missing/unseen, reorder, batch boundary, pickle. Non enumerano tutte le combinazioni multivariate possibili.

Persistence senza teacher verificata bloccando import interpret/teacher/LGBM/CatBoost; NumPy/pandas/SciPy restano runtime dependencies private. L’indipendenza dalteacher non implica dipendenze zero. File di riferimento: [compiler35.py](../../research_private/round35/compiler35.py), [runtime36.py](../../research_private/round36/runtime36.py), [runtime37.py](../../research_private/round37/runtime37.py), [final manifest](../../research_private/round37/final_manifest.json). Modelli in round37/models; evitare rigenerazione senza motivo. I CSV di round37sono risultati, non ricette da ritoccare dopo test.

### Aggiornamento storico Round 38

Backend c; thread grandi 4; bucket/prediction mismatch0/0 su 12,465,430 probe numerici. Kernel bucket speedup0.739x, fused0.781x. End-to-end single/1k/100k vs EBM 0.271/1.218/3.648x; speedup100k vs R37 0.504x; deep0.170xEBM. Gate mediano FAIL.

La tabella R37 precedente rimane storia congelata: non usare tempi tra round come stima del guadagno. Per il confronto corrente usare i rapporti paired R38/R37 delle stesse sessioni. Readiness: **PARTIALLY**. Nuovo collo di bottiglia prioritario: conversione, dispatch e costi di esecuzione end-to-end da isolare.

### Aggiornamento storico Round 39

Layout D, colonne contigue dirette quando possibile, single-thread. Ready-buffer vs R37 1.5007x; end-to-end vs R37 1.3367x. Batch100k/EBM 1.0331x; Power/Gas/Diabetes 2.2778/1.0194/1.2293x. Single/EBM 0.2878x; deep/EBM 0.1701x; conversion share 5.57%. Bucket/prediction mismatch 0/0; nuovi false-safe0 sui sei SAFE congelati. Gate PASS. Margine ready rispetto alla soglia1.5x 0.0458%; mediane per sessione {'1': 1.4717679786503473, '2': 1.53024342881784}. Passaggio eventualmente nominale, non prova robusta di replica; nessuna promozione pubblica.

Bottleneck corrente: **KERNEL**. Validate the frozen column-direct runtime on independent workloads and hardware; retain R37 fallback and explicit input-layout contract. Do not change the predictive model.

### Aggiornamento storico Round 40

Round39 replicated PARTIALLY. Historical ready/session [1.5097995780788627, 1.5223270633516743, 1.5121240266033158]; new ready/session [1.362480888455787, 1.385029012881379, 1.360380090821325]. Pooled ready 1.4323x, end-to-end 1.3457x, batch100k/EBM 1.0082x, single/EBM 0.2665x, deep/EBM 0.1857x. Historical complete gate PASS; new complete gate FAIL. R37 official research reference; R39 not promoted after independent replication. Power/Gas/Diabetes100k/EBM 2.1524/1.0082/1.2395x. Fidelity bucket/prediction/false-safe 0/0/0. Requested numerical gates pooled across13 datasets PASS; the conservative reference decision uses the additional preregistered separate-cohort transfer gate, not a claimed failure of pooled thresholds.

Validate an explicit small-batch/compact-memory deployment contract on independent hardware; keep R37 as reference and do not resume equivalent runtime tuning.

### Aggiornamento storico Round 41

Independent hardware replication NO; portable kit prepared and executed locally only, Linux build UNRUN. Official R37 exact raw-score contract: single-row 3.838xEBM, >=3x on 9/13; deep memory 0.182x, <=0.30 on 11/13; sampled peak RSS100k 0.597x. FAST_SAFE 84/91 observed model/batch cases, SAFE 7/91. No universal monotonic batch cutoff. Raw scores and frozen compiled predictions bitwise exact; strict teacher-probability contract REJECT for 10/13 models, max difference 2.22e-16. No runtime fix; this clarifies prior raw-score versus probability fidelity scope.

Run the supplied unchanged kit on independent hardware, validate target ABI/fidelity and scope per-host performance labels; then separately authorize public opt-in packaging. No new runtime optimization.

### Aggiornamento storico Round 42

Opt-in codadapt.experimental.compile_ebm(teacher, *, X_verify, max_states=None); interpret-core0.7.8 additive standard EBM only, binary/scalar regression; named DataFrames, real numeric and string categorical labels, supported missing/unseen. Exact raw/regression; numerical probability fidelity, not bitwise. Mandatory exact capacity/schema checks and heldout compile-then-verify. No teacher retained. Existing native API/default unchanged; standalone runtime ports frozen R37 ordered NumPy lookup and buffer persistence; no R38/R39 native backend.

Execute the configured Python3.10-3.12 CI matrix and unchanged deployment kit on independent hardware, review the candidate package, then authorize any release separately. Numeric categorical labels remain REJECT until separately tested/scoped. No default change or new optimization.

### Aggiornamento corrente Round 43

User explicitly replaced remote validation with local checks and final source artifacts. No GitHub install, dispatch, Kaggle/Colab/SSH execution, commit, push, tag or release. Earlier read-only GitHub inspection showed green Python3.10/3.11/3.12 jobs only for v0.1.0, not this RC; it is not RC evidence.

User reviews and manually uploads the delivered source repository when desired. External CI/hardware remain unverified and are excluded from this task. Do not run them, publish, tag, commit or push without new instruction.

## 8. Current bottlenecks

| Priorità | Evidence / likely cause | Già provato | Ancora non verificato |
|---|---|---|---|
|1 Deployment envelope + external validation|R41 scoped raw-score export; no universal crossover; probability-bitwise contract rejected where mismatched|One host, 13 models, exact scores, independent hardware still pending|Run private replication kit elsewhere; keep R37 official and no new optimization|
|2 Native predictive quality|R15 nessuna nicchia stabile; R23 mainopportunity|A/B, pairs, lowrank, refit, discovery|Nuovo principio indipendentemente motivato; non sweep|
|3 Direct strong shape learning|R27–32falliti; cause miste/non isolate|smoothing, ampiezza, honesty, globalobjective|Nuova spiegazione statistica falsificabile, non ancora disponibile|
|4 Wide/high-cardinality capacity|R35 fino 33488 states; Diabetes deep relativo piùalto|Auditbudget, exact, float64,persistence|Preflight/allocations su cardinalità/versioni/schema oltre copertura|
|5 Multiclass|Base/compiler non supportano|Task multiclass binarizzati soltanto|Obiettivo/schema/export multiclass completo; nessuna promozione attuale|
|6 General deployment scale|Power600ktraining, batch100k; unhost|ScalePower ewide 649 feature|Concorrenza larga, serving reale, altri hardware/workloads epeakRAM riproducibile|

## 9. Open research questions

- Un backend numerico esatto può accelerare i grandi batch mantenendo la nicchia single-row e la memoria?
- Il vantaggio di export persiste su nuovi hardware, dtype, schemi e budget qualità/risorse realmente equivalenti?
- Quale packaging sperimentale può rendere espliciti supporto EBM/versione, schema, capacity e failure senza cambiare il default?
- Il memory audit resta prevedibile oltre 649 feature e ad alta cardinalità, con cache e persistenza misurate interamente?
- Esiste un nuovo principio di apprendimento diretto giustificato da dati indipendenti? La linea provata è chiusa; la domanda teorica resta aperta, senza autorizzare nuovi sweep.

## 10. Experiments worth retrying

| Why revisit | What must be different | Minimal experiment | Success criterion |
|---|---|---|---|
|Numeric throughput ancora aperto|Kernel nativo esatto, non altro composito NumPy|Protocollo R38 sotto|Bitwise0 error, paired speedup≥15%,gates memoria/latency|
|Vantaggio systems dipende da host|Nuove workload/CPU, benchmark alternato|Frozen compiler vs EBM su nuovi input preregistrati, senza retuning|Stessa fidelity e vantaggio riproducibile, denominatori chiari|
|SAFE limitato alcontratto testato|Nuove versioni/schema mantenendo rejection esplicita|Property tests indipendenti per categoriche/missing/persistence/capacity|0false-safe e mapping dimostrato; unsupported rifiutati|

Non è un elenco di esperimenti già autorizzati/eseguiti. Ogni eventuale riapertura del learner richiede prima evidenza nuova e ipotesi distinta dalle roundchiuse.

## 11. Experiments NOT worth retrying

Fullscan; residual-guidedsearch storico; fixed multiresolution indiscriminato; A/Bgating; local-linear; pair proposal/ranking/admission e uncertainty thresholds; rank 2/4/8ripetuti; pass count/refit sweeps; cataloghi discovery già negativi; direct learner R27–31;smoothing intensity; alpha calibration; stesso obiettivo globale R32;più nodi sopra shared grid collassata;512 states universali; raggruppamenti searchsorted NumPy già perdenti. Non rieseguire R23 o vecchie confirmation per selezionare nuovi vincitori.

## 12. Current promising directions

| Priorità | Direzione | Fondamento |
|---|---|---|
|HIGH PRIORITY|Safe exact EBM export e risoluzione numeric throughput|Fidelity/capacity R35,memory/single R36–37;limite ancora misurabile|
|MEDIUM PRIORITY|Persistence/compatibility/independent deployment validation|Bug buffer R37 corretto; sei teacher e unhostnon coprono produzione|
|LOW PRIORITY|Multiclass e scala oltre copertura|Necessità possibile ma nessun risultato positivo locale che giustifichi promozione|
|ARCHIVED|Nuovo core nativo, local/pair/lowrank/directadditive giàtestati|Gate falliti o confirmation negativa; nessun cambio default|

## 13. Next recommended round

**id:** MANUAL_SOURCE_HANDOFF

**priority:** 1

**name:** User-controlled review and upload of validated local candidate

**status:** PREPARED_NOT_PUBLISHED

**mechanism:** User reviews and manually uploads the delivered source repository when desired. External CI/hardware remain unverified and are excluded from this task. Do not run them, publish, tag, commit or push without new instruction.

**success_criterion:** Explicit future user decision; no current external requirement claimed passed

**stop_criterion:** No automatic remote execution/publication, new feature or default change

## 14. v0.2 readiness

**Aggiornamento R43:** local source handoff YES,44-file clean ZIP verified; no final release. User excludes all external checks/actions. RC remote CI/GitHub install/independent hardware are NOT RUN, not PASS. Default unchanged; current compiler contract unchanged.


**Aggiornamento R42:** YES for local internal0.2.0rc1 opt-in experimental compiler, gate PASS. No final release or default change. Binary raw/regression exact; probabilities numerically equivalent at absolute1e-15. Independent hardware and remote CI pending. The checklist below is historical R37–41, superseded for packaging/API only.


**Aggiornamento R41:** YES only as a recommended opt-in EXPERIMENTAL raw-score/regression export within the verified contract; not shipped publicly. Independent hardware NO/PENDING. Default NO. Strict teacher-probability bitwise replacement excluded. Earlier readiness statements below are historical.


**Aggiornamento R40:** PARTIALLY. R37 official research reference; R39 not promoted after independent replication. Replica PARTIALLY; no public inclusion. Same-host temporal validation is not cross-hardware validation. The following R39 readiness statement is historical and superseded by this decision.


**Aggiornamento R39:** PARTIALLY; gate sperimentale PASS, non promozione pubblica. Native research YES; fidelity esatta sui casi misurati. Le righe storiche seguenti non sono evidenza indipendente di deployment.


| Checklist | Stato | Perimetro |
|---|---|---|
|Native predictive core stronger than v0.1|NO|Nessun candidato promosso|
|Multiclass|NO|Solo binary|
|Regression ready|YES|Regressore pubblico single-target esistente; NON nuova superiorità v0.2|
|EBM compiler safe|YES|Contratto univariate additive supportato e sei teacher verificati|
|EBM compiler fidelity|YES|Exact, float64,bitwise nei casi verificati|
|Single-row performance|YES|Target mediano; eccezioni individuali|
|Large-batch performance|NO|R38 gate mediano fallito; compatibilità e nuovi workload ancora da validare|
|Persistence without teacher|YES|Blocco import/load/predict verificati|
|Wide datasets|YES|Audit esatto fino 649 feature, non garanzia di qualunque budget/throughput|
|Public API frozen|YES|Nessun cambio pubblico|
|Enough evidence for v0.2|PARTIALLY|Direzione compiler sperimentale, non nuovo core pubblico né release autorizzata|

## 15. Rules for future Codex sessions

1. Leggere questo file prima di qualsiasi lavoro.
2. Leggere `RESEARCH_STATE.json` e controllare ultima round/fonti.
3. Non ripetere esperimenti già chiusi senza nuova motivazione falsificabile.
4. Non modificare API/default senza confirmation indipendente e scope esplicito dell’utente.
5. Development != confirmation: una fonte già osservata resta osservata.
6. Synthetic win != real-data win.
7. Ogni nuova promotion richiede unseen confirmation; per runtime usare workload/hardware indipendenti e fidelity, senza pretendere che teacher frozen siano nuovi dati predittivi.
8. Non fare commit/push automatici.
9. `docs/research/` è memoria di ricerca tracciata nel repository e va mantenuta aggiornata; `research_private/` resta locale/esclusa e non va pubblicata.
10. Aggiornare entrambi i file dopo ogni round, con nuove fonti, gates, decisioni, discrepanze e prossimo esperimento.
11. Leggere il codice in caso di conflitto con documentazione legacy; non inventare protocolli mancanti.
12. Distinguere teacher quality, function fidelity, train cost, compiled latency, pickle, deep memory eRSS. Riportare casi falliti, denominatori e CI.
13. Non scegliere nuovi teacher/kernel/configurazioni sui test. Non interpretare mediane tra cohort come miglioramenti causali.
14. Per riprendere ilcompiler leggere R35 findings/compiler35, poi R36,R37,freeze/manifest epaired check; non lanciare automaticamente benchmark costosi.

### Indice delle fonti e riproducibilità della memoria

I link nella timeline rimandano ai report primari locali; gli stessi report citano CSV, protocollo, freeze, source audit e predizioni. Sono stati inventariati i documenti disponibili nel tree privato, escludendo distribuzioni dipendenze e dataset binari. Non si è rifatta alcuna analisi predittiva. L’inventario non pretende che ogni file di dati grezzi sia stato semanticamente riletto. Le cifre derivano dai report finali e summary, con precedenza all’evidenza più recente sullo stesso quesito; le fonti precedenti restano citate.

R17:[Discovery report](../../research_private/discovery/DISCOVERY_REPORT.md). R18:[Discovery2 report](../../research_private/discovery2/DISCOVERY2_REPORT.md) e [preprocessing](../../research_private/discovery2/PREPROCESSING_REPORT.md). Storia R7–15:[history](../../research_private/CODADAPT_PRIVATE_RESEARCH_HISTORY.txt). Verifica R37:[summary](../../research_private/round37/summary.json) e [pairedcheck](../../research_private/round37/paired_runtime_check.csv).

Le fonti R1–6 erano nell’allegato `bd0dab7b-54cb-4c3f-9139-35c35d016a46/pasted-text.txt`; la timeline incorpora tutte le affermazioni storiche pertinenti. Non sono presenti report locali che permettano di verificare indipendentemente split/dataset R1–5 o di separare con sicurezza R1 e R2. **Completezza dell’indice:43/43; completezza delle prove primarie:37/43 (R7–43),più storia sintetica R1–6 e disclosure R6.** Non confondere i due indicatori.


### Regola obbligatoria di chiusura, dalla Round 38

Alla fine di OGNI futura round aggiornare automaticamente entrambi i file: timeline completa, ipotesi/protocollo/risultati/decisione, cosa non riprovare, nuovo bottleneck e prossimo esperimento. Aggiornare last_completed_round, current_research_branches, confirmed_findings, rejected_directions se necessario, partially_promising, open_questions, next_experiments e v0_2_readiness. Verificare JSON, coerenza, copertura continua delle round, privacy Git e integrità del runtime pubblico. Non eseguire build_research_memory.py della prima consolidazione come se fosse un aggiornamento: contiene lo stato storico R37.

### Release/CI fix — notebook version alignment (0.2.0rc1)

Corrected the six current-release references in `examples/kaggle_quickstart.ipynb`
(title, future tag, wheel filenames, installation pin and installed-version assertion)
from 0.1.0 to 0.2.0rc1. Historical core/changelog/research references remain unchanged.
Only the current canonical checkout was used; no earlier project directory or ZIP.

Validation on Python3.12.14 with the CI recent NumPy/pandas/sklearn versions:
Ruff zero errors; pytest375 passed,4 expected xfails,0 failed; classifier/regressor
examples PASS; CI notebook PASS, all7 code cells executed against the installed wheel.
Dynamic pyproject version, _version.py, README, release notes and package metadata
agree on0.2.0rc1. All runtime/compiler source hashes are unchanged.
This is a release/CI fix, not a new research round; last_completed_round remains43.
