# API pubblica

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
| `n_bins` | `32` | Numero massimo di intervalli numerici, escluso il bucket mancante; da 2 a 4096. |
| `max_categories` | `128` | Categorie frequenti conservate separatamente per feature. |
| `quantile_sample_size` | `20000` | Campione massimo per costruire quantili riproducibili. |
| `n_tables` | `8` | Numero di tabelle di interazione, da 0 a 128; `0` le disattiva. |
| `features_per_table` | `3` | Feature distinte per gruppo, da 1 a 32; ridotte se le feature totali sono meno. |
| `table_size` | `256` | Celle per tabella: potenza di due da 16 a 4096. |
| `main_effects` | `True` | Attiva gli effetti monovariati. |
| `max_iter` | `20` | Massimo numero di passaggi completi di training. |
| `l2` | `5.0` | Penalità positiva dei punteggi; l'intercetta è esclusa. |
| `adapt_codes` | `True` | Abilita la ricerca discreta dei codici. |
| `adapt_every` | `2` | Frequenza dei passaggi adattivi, dopo il riscaldamento. |
| `max_code_updates` | `64` | Coordinate massime valutate per tabella/passaggio adattivo. |
| `n_candidates` | `4` | Nuovi codici distinti proposti per coordinata; da 1 a `min(64, table_size-1)`. |
| `min_code_count` | `5` | Righe a peso positivo minime per rendere adattabile un bucket. |
| `categorical_features` | `None` | Riconoscimento automatico nei DataFrame; nomi o indici per dichiarazioni esplicite. |
| `early_stopping` | `True` | Arresto e ripristino sulla validation. |
| `validation_fraction` | `0.15` | Quota riservata se non viene fornito `eval_set`. |
| `patience` | `4` | Passaggi consecutivi senza miglioramento sufficiente prima dell'arresto. |
| `tol` | `1e-5` | Tolleranza assoluta non negativa per il miglioramento della loss di validation. |
| `random_state` | `None` | `None`, intero `[0, 2**32-1]` o `np.random.RandomState`; usa un intero per riprodurre il fit. |
| `verbosity` | `0` | `0`: silenzioso; `1`: riepilogo; `2`: dettagli per iterazione. |

Non esiste un parametro pubblico `verbose`. Nessun livello di `verbosity` sopprime
globalmente warning o eccezioni. I default non lanciano l'esplorazione dei candidati
di architettura: quella appartiene al runner sperimentale.

`n_tables=0, main_effects=True` dà una baseline monovariata;
`main_effects=False` conserva solo le interazioni;
`n_tables=0, main_effects=False` conserva soltanto l'intercetta.
`adapt_codes=False` conserva codici e gruppi iniziali, continuando ad apprendere punteggi.

## Input

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
rifiutati chiaramente. Nessun supporto a multiclasse, multilabel, ranking, GPU,
training online o target multipli è dichiarato. Prima della previsione su dati nuovi
occorrono gli stessi nomi di colonna: nomi duplicati, mancanti o aggiuntivi sono errori;
un ordine diverso viene riallineato. Il fit su DataFrame non abilita la previsione su
array senza nomi.

## Metodi

### `fit(X, y, sample_weight=None, eval_set=None)`

Restituisce `self`. `y` è monodimensionale, finito e senza mancanti. Il classificatore
richiede due classi con peso positivo e preserva le etichette; il regressore richiede
valori numerici, inclusi target interi. Gli input non vengono modificati.

`sample_weight` è un vettore finito non negativo con somma positiva. Righe a peso zero
sono escluse prima di imparare preprocessing e codici. La loss di training è una somma
pesata: riscalare tutti i pesi cambia l'effetto di `l2`.

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

Disponibili nel classificatore. `predict_proba` ha forma `(n_rows, 2)`: colonne nello
stesso ordine di `classes_`, valori finiti e somma di riga uno.
`decision_function` restituisce `F`, con segno positivo a favore di `classes_[1]`.

### `get_params(deep=True)`, `set_params(**params)`, `score(X, y, sample_weight=None)`

Protocollo scikit-learn per parametri, clone, Pipeline, cross-validation e scoring.
Il classificatore usa accuracy come `score`, il regressore usa R². Per confronti
scientifici scegliere esplicitamente ROC-AUC/log-loss oppure RMSE/MAE.

## Attributi dopo il fitting

| Attributo | Contenuto |
| --- | --- |
| `classes_` | Due etichette ordinate, soltanto nel classificatore. |
| `n_features_in_` | Numero delle feature. |
| `feature_names_in_` | Nomi delle colonne, quando appropriato. |
| `n_iter_` | Numero di passaggi realmente eseguiti. |
| `best_iteration_` | Iterazione corrispondente allo stato selezionato. |
| `training_history_` | Loss, coordinate esaminate e mosse accettate per iterazione. |
| `timings_` | Tempi in secondi delle componenti e del fit completo. |
| `encoder_` | Soglie, vocabolari e supporti appresi soltanto dal training. |
| `groups_`, `codes_` | Gruppi di feature e codici adattivi delle interazioni. |
| `main_tables_`, `tables_` | Tabelle monovariate e di interazione. |
| `intercept_` | Intercetta scalare. |
| `accepted_moves_` | Mosse accettate nell'intera storia eseguita, anche oltre lo stato poi ripristinato. |
| `estimated_memory_bytes_` | Stima conservativa delle allocazioni controllata prima del training. |

`timings_` contiene `preprocessing`, `index_build`, `score_updates`, `code_search`,
`validation`, `restore` e `fit_total`; `validation` comprende anche le copie degli stati
migliori. I tempi di trasformazione e inferenza sui nuovi batch sono misurati dai
runner, non aggiunti retroattivamente ai tempi di `fit`.

`n_iter_` può superare `best_iteration_`: la cronologia conserva i passaggi eseguiti,
mentre codici, tabelle e intercetta contengono l'intero stato migliore ripristinato.
Gli attributi interni di rappresentazione servono all'ispezione, non vanno mutati
manualmente per alterare il modello. Non sono conservati target o copie del dataset.

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
