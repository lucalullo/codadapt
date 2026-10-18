# API pubblica

> Candidate locale 1.1.0rc1: C1 congelata, default nativo `"auto"`.
> La 1.0.1 usava il default storico 512 MiB; un intero esplicito lo conserva.
> Preparazione locale, nessuna pubblicazione.

```python
from codadapt import CodAdapt, CodAdaptClassifier, CodAdaptRegressor

classifier = CodAdapt(random_state=42, verbosity=0)
regressor = CodAdaptRegressor(random_state=42, verbosity=0)
```

`CodAdapt` è un alias esplicito di `CodAdaptClassifier`. Entrambe le classi espongono
il protocollo `BaseEstimator`, con il mixin del task prima della classe base.
Il costruttore memorizza i parametri; il primo `fit` crea lo stato appreso.

## Parametri comuni

| Parametro | Default | Significato |
| --- | --- | --- |
| `n_bins` | `32` | Intero da 2 a 4096; il percorso nativo corrente limita la risoluzione numerica più fine a `min(16, n_bins)`, escluso il bucket mancante. |
| `max_categories` | `128` | Categorie frequenti conservate separatamente per feature. |
| `quantile_sample_size` | `20000` | Campione massimo per costruire quantili riproducibili. |
| `n_tables` | `8` | Numero di tabelle di interazione, da 0 a 128; `0` le disattiva. |
| `features_per_table` | `3` | Solo stima memoria; gruppi correnti di due feature (una se p=1). |
| `table_size` | `256` | Celle per tabella: potenza di due da 16 a 4096. |
| `main_effects` | `True` | Attiva gli effetti monovariati. |
| `lookup_budget` | `24` | Intero da 1 a 4096: limite totale dei lookup per campione, sommando tabelle monovariate e di interazione sui livelli conservati. Il modello può usarne meno; non sostituisce il limite `n_tables`. Nel multiclasse vale per ciascun head. |
| `l2` | `5.0` | Penalità positiva dei punteggi; l'intercetta è esclusa. |
| `categorical_features` | `None` | Riconoscimento automatico nei DataFrame; nomi o indici per dichiarazioni esplicite. |
| `early_stopping` | `True` | Arresto e ripristino sulla validation. |
| `validation_fraction` | `0.15` | Quota riservata se non viene fornito `eval_set`. |
| `tol` | `1e-5` | Soglia relativa: gain > tol × max(1, abs(previous_validation_loss)). |
| `random_state` | `None` | `None`, intero `[0, 2**32-1]` o `np.random.RandomState`; usa un intero per riprodurre il fit. |
| `verbosity` | `0` | 0 silenzioso; 1–2 riepilogo del fit corrente. |
| `memory_budget_mb` | `"auto"` | `"auto"` oppure intero positivo in MiB. AUTO estende il dominio storico solo con headroom visibile conservativo; un intero resta un limite rigido della stima E, non di RSS. |

Non esiste un parametro pubblico `verbose`. Nessun livello di `verbosity` sopprime
globalmente warning o eccezioni. I default non lanciano l'esplorazione dei candidati
di architettura: quella appartiene al runner sperimentale.

`n_tables=0, main_effects=True` dà una baseline monovariata;
`main_effects=False` conserva solo le interazioni;
`n_tables=0, main_effects=False` conserva soltanto l'intercetta.

## Migrazione pre-1.0 e contratto del trainer corrente

I costruttori nativi sono **keyword-only**: usare `CodAdapt(n_bins=8, l2=5.0)`,
non argomenti posizionali. I default predittivi dei parametri rimasti sono invariati. La 1.1.0rc1 modifica solo il default di ammissione memoria; vedere [AUTO_MEMORY.md](AUTO_MEMORY.md).

Sono stati rimossi sette controlli inattivi: `max_iter`, `adapt_codes`,
`adapt_every`, `max_code_updates`, `n_candidates`, `min_code_count` e `patience`.
Non avevano effetto sul trainer; non vengono sostituiti da una nuova euristica.
Eliminarli dalle chiamate al costruttore, da `set_params`, dai dizionari salvati di
configurazione e dalle griglie di ricerca. Il costruttore ora rifiuta questi nomi
con `TypeError`, `set_params` con `ValueError`; non vengono ignorati silenziosamente.
Questa modifica prerelease è deliberatamente incompatibile a livello di firma,
ma conserva il fitting e le predizioni per configurazioni equivalenti.

`features_per_table` resta un parametro funzionale **solo per la stima preventiva
memoria**: il selettore propone coppie, o un gruppo singolo se p=1, indipendentemente
da questo valore. Cambiarlo può modificare `estimated_memory_bytes_` e l'ammissione
al budget, non la capacità predittiva. `n_bins` viene limitato a
`max(2, min(16, n_bins))` per l'encoding condiviso, con tre risoluzioni annidate;
aumentarlo oltre 16 non aumenta la risoluzione corrente.

Gli import root e `CodAdapt is CodAdaptClassifier` restano invariati. Il modulo
`codadapt.preprocessing` e `BucketEncoder` sono dettagli interni, non un'API
standalone supportata. Il percorso resta disponibile per gli import interni e
la persistenza dei modelli; nessun helper viene promosso a experimental.
La compatibilità dei vecchi pickle prerelease non è garantita: conservarne
l'ambiente originale. Un load riuscito non rende nuovamente validi i parametri rimossi.

## Input

Storicamente 1.0.0 e 1.0.1 pubblica conservano il budget introdotto nella RC2 e il default 512 MiB.
La 1.1.0rc1 usa `"auto"`, senza cambiare capacità, precisione o fitting;
la migrazione esplicita `memory_budget_mb=512` conserva la vecchia ammissione.
La stima ora include anche le righe di `eval_set` esterno prima delle copie e
dell'encoding. Non cambia fitting o predizioni dei fit ammessi; può rifiutare
validation molto grandi prima ignorate dal guard. Vedere
[LARGE_DATASETS.md](LARGE_DATASETS.md) per formula, configurazione, limiti e migrazione.
La finalizzazione stable non modifica il comportamento qualificato nella RC2.

`X` deve essere un DataFrame pandas o un array NumPy numerico bidimensionale. Nei
DataFrame, colonne numeriche sono numeriche; `category`, stringhe/`object` con scalari
supportati e booleani anche nullable sono categoriche. Le categorie vengono apprese
dai valori osservati, non dall'elenco completo `.cat.categories`.

Con `categorical_features=["codice"]` una colonna numerica del DataFrame diventa
categorica. Gli array richiedono indici, per esempio `categorical_features=[0, 2]`.
Non si inferiscono categorie da numeri interi o da identificativi.

`np.nan`, `None` e `pd.NA` sono ammessi nei dtype appropriati. Mancante, zero,
categoria rara osservata e categoria nuova sono distinti. I valori numerici finiti
fuori dal range vanno negli intervalli estremi. Gli infiniti vengono rifiutati.
I bucket nuovi non modificano il modello; il loro contributo è nullo come descritto
in [ALGORITHM.md](ALGORITHM.md).

Date non trasformate, matrici sparse, numeri complessi e oggetti non supportati vengono
rifiutati chiaramente. Nessun supporto a multilabel, ranking, GPU,
training online o target multipli è dichiarato. Prima della previsione su dati nuovi
occorrono gli stessi nomi di colonna: nomi duplicati, mancanti o aggiuntivi sono errori;
un ordine diverso viene riallineato. Il fit su DataFrame non abilita la previsione su
array senza nomi.

## Metodi

### `fit(X, y, sample_weight=None, eval_set=None)`

Restituisce `self`. `y` è monodimensionale, finito e senza mancanti. Il classificatore
richiede almeno due classi con peso positivo e preserva le etichette; il regressore richiede
valori numerici, inclusi target interi. Gli input non vengono modificati.

`sample_weight` è un vettore finito non negativo con somma positiva. Righe a peso zero
sono escluse prima di imparare preprocessing e codici. La loss di training è una somma
pesata: riscalare tutti i pesi cambia l'effetto di `l2`.
Target o pesi di magnitudine estrema possono causare overflow della loss quadratica
anche se finiti: un `FloatingPointError` richiede di riscalare target o pesi.

`eval_set=(X_valid, y_valid)` fornisce una validation esplicita. La sua loss è non
pesata e senza penalità L2: MSE per regressione, log-loss per classificazione.
Senza `eval_set`, l'early stopping crea uno split interno riproducibile, stratificato
per la classificazione, prima del fitting del preprocessing. Se lo split è impossibile,
il messaggio suggerisce `early_stopping=False`. Con quest'ultimo e senza validation
esplicita sono usate tutte le righe positive del training.

La validation controlla soltanto l'arresto. Il modello non adatta i codici usando
validation/test e non esegue refit nascosti. Ogni nuovo `fit` riparte dai parametri
del costruttore e sostituisce lo stato appreso precedente. Con `early_stopping=False`
ed `eval_set` la loss di validation viene soltanto registrata: non causa arresto o
ripristino dello stato.

### `predict(X)`

Restituisce un array monodimensionale di etichette originali per il classificatore,
di punteggi reali per il regressore. Non esegue fitting o ricerca dei codici.

### `predict_proba(X)` e `decision_function(X)`

Disponibili nel classificatore. `predict_proba` ha forma `(n_rows, n_classes)`: colonne nello
stesso ordine di `classes_`, valori finiti e somma di riga uno.
`decision_function` restituisce `F` con forma `(n_rows,)` nel caso binario, con segno
positivo a favore di `classes_[1]`; nel multiclasse restituisce `(n_rows, K)`.

### `get_params(deep=True)`, `set_params(**params)`, `score(X, y, sample_weight=None)`

Protocollo scikit-learn per parametri, clone, Pipeline, cross-validation e scoring.
Il classificatore usa accuracy come `score`, il regressore usa R². Per confronti
scientifici scegliere esplicitamente ROC-AUC/log-loss oppure RMSE/MAE.

## Attributi dopo il fitting

| Attributo | Contenuto |
| --- | --- |
| `classes_` | Etichette ordinate (`np.unique`) delle classi a peso positivo. |
| `n_classes_` | Numero di classi nel percorso multiclass; il binario conserva gli attributi precedenti. |
| `n_features_in_` | Numero delle feature. |
| `feature_names_in_` | Nomi delle colonne, quando appropriato. |
| `n_iter_` | Numero di livelli conservati, da zero a tre. |
| `best_iteration_` | Uguale a `n_iter_` nel trainer corrente. |
| `training_history_` | Loss dei livelli accettati; coordinate e mosse adattive sono zero. |
| `timings_` | Tempi in secondi delle componenti e del fit completo. |
| `encoder_` | Soglie, vocabolari e supporti appresi soltanto dal training. |
| `groups_`, `codes_` | Gruppi di feature e codici adattivi delle interazioni. |
| `main_tables_`, `tables_` | Tabelle monovariate e di interazione. |
| `intercept_` | Intercetta scalare. |
| `accepted_moves_` | Zero: il trainer corrente non effettua mosse iterative dei codici. |
| `estimated_memory_bytes_` | Stima conservativa delle allocazioni controllata prima del training. |

`timings_` riporta preprocessing, validation e fit totale insieme a contatori interni
del trainer. Alcune chiavi legacy possono valere zero; non costituiscono un profiler
completo. `n_iter_ == best_iteration_` conta i livelli conservati. Il primo livello
rifiutato compare in `allocation_history_`, non in `training_history_`.
Gli attributi di rappresentazione e le chiavi diagnostiche sono dettagli di
implementazione per ispezione, non un'interfaccia per modificare il modello.
Non sono conservati target o copie del dataset. Il contratto di stabilità e
persistenza è in [STABILITY.md](STABILITY.md).

## Errori, compatibilità e persistenza

Predire prima del fit solleva `sklearn.exceptions.NotFittedError`. Input o parametri
non validi producono eccezioni informative, senza tentare fallback predittivi impliciti.
I limiti delle allocazioni vengono controllati prima dei grandi array.

La riproducibilità vale a parità di seed, dati, ordine e ambiente. Non si garantiscono
bit identici fra versioni delle dipendenze. La matrice CI e le verifiche locali sono
riportate nel [benchmark disclosure](../BENCHMARKS.md); un intervallo di dipendenze ammesso dal
packaging non significa che ogni sua combinazione sia stata provata.

È possibile serializzare con pickle/joblib e caricare senza refit, preferibilmente
nello stesso ambiente. Caricare file non attendibili può eseguire codice arbitrario.
Conserva insieme al modello versione CodAdapt e versioni delle dipendenze.

## Multiclass Shared OVR

`CodAdapt` e `CodAdaptClassifier` rilevano automaticamente il target single-label:
meno di due classi a peso positivo è un errore; due usano il percorso binario
invariato; più di due usano K head binari nativi, senza modelli esterni.
Interi, interi non contigui, stringhe ed etichette categorical-like comparabili
seguono l'ordine `np.unique` in `classes_`.

Schema, soglie, vocabolari, missing e codici finest/coarse sono condivisi. Ogni
head mantiene valori, residuali, selezione e arresto specifici del proprio target.
`predict_proba` normalizza le sigmoidi dei K score, non usa softmax; le righe sono
finite, non negative e sommano a uno entro tolleranza numerica. `predict` usa
l'argmax e in caso di parità sceglie la prima classe nell'ordine `classes_`.

I pesi originali non vengono riscalati per classe. Righe a peso zero sono escluse
prima dell'encoding. `eval_set` viene codificato una volta e ogni head usa
`y_valid == classe`; label validation assenti dal training positivo sono errori.
Senza `eval_set`, tutti gli head condividono un solo split stratificato train-only.
Una classe con meno di cinque esempi TRAIN a peso positivo genera un warning.
Uno split impossibile genera un errore: fornire un `eval_set` valido oppure
`early_stopping=False`. Non viene introdotta una nuova euristica per classi rare.

Nel multiclasse `encoder_` e `shared_encoder_` sono lo stesso oggetto; gli head
compatti sono privati e non sono K estimator completi. `n_iter_` e
`best_iteration_` riassumono il massimo numero di livelli conservati fra gli head;
`lookup_count_per_sample_` somma i lookup degli head. `estimated_memory_bytes_`
è la preflight estimate nativa, non una misura del picco RSS. `timings_` registra
preprocessing e fit totale. Cronologie e cache di training non sono conservate;
gli attributi per singolo head del percorso binario non vengono simulati.

Refit binario→multiclasse o multiclasse→binario ripulisce lo stato precedente.
Clone/Pipeline/CV e `score` (accuracy) valgono per entrambi. Pickle/joblib preservano
predizioni e identità dell'encoding condiviso; nessun modulo di ricerca o teacher
è richiesto al reload. Preferire lo stesso ambiente numerico.

## SafeBlendRegressor sperimentale

`codadapt.experimental.SafeBlendRegressor` espone `fit(X, y)`: non supporta
`sample_weight` né `eval_set`. I parametri comuni della tabella precedente
appartengono agli estimator Base, non al costruttore minimale SafeBlend.
Il contratto completo è in [SAFE_BLEND_EXPERIMENTAL.md](SAFE_BLEND_EXPERIMENTAL.md).

Un fit fallito, anche durante un refit, elimina lo stato appreso e quello parziale:
`check_is_fitted` e `predict` sollevano `NotFittedError`. Il modello precedente
non rimane utilizzabile; occorre completare un nuovo fit valido.
