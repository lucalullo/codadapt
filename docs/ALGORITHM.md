# Algoritmo di CodAdapt 0.1.0

## Modello e rappresentazione

Per il bucket `z_j(x)` della feature `j`:

```text
F(x) = intercept + Σ_j U_j[z_j(x)] + Σ_t V_t[address_t(x)]
address_t(x) = (Σ_{j in S_t} C_tj[z_j(x)]) mod M
```

`U` sono gli effetti monovariati, `C` codici interi in `[0, M-1]`, `V` punteggi reali.
`M=table_size` è una potenza di due fra 16 e 4096. I gruppi pseudocasuali contengono
`min(features_per_table, n_features)` variabili distinte; tabelle diverse possono
condividere lo stesso gruppo, con codici indipendenti. La somma dei codici avviene
in interi sufficientemente ampi prima del modulo.

Il regressore restituisce `F`. Il classificatore restituisce la sigmoide stabile
`sigmoid(F)` come probabilità di `classes_[1]`, preservando le etichette originali.
Non si usano `hash()` Python, alberi o modelli predittivi esterni.

Quantili e vocabolari sono appresi soltanto dal training effettivo, dopo esclusione
delle righe a peso zero ed eventuale split interno. Sono poi fissi. Bucket compatti
vengono calcolati una volta per training o batch; i codici sono la parte che cambia.
Per numeriche si eliminano soglie duplicate e si riserva il bucket dei mancanti.
Le categorie frequenti conservano bucket distinti; rare osservate, nuove e mancanti
sono tre casi diversi. I quantili non convertono preventivamente in `float32`.

La convenzione numerica è `searchsorted(thresholds, value, side="right")`: un valore
uguale a una soglia va nell'intervallo a destra. I bucket finiti sono `0..len(thresholds)`;
il mancante è `len(thresholds)+1`. Si eliminano soglie duplicate e soglie uguali al
minimo; una soglia uguale al massimo rimane se compare fra i quantili, così può
separare anche valori discreti come 0 e 1. I quantili usano interpolazione lineare
in `float64`. Categoriche: `0` mancante, `1` rara osservata, `2` nuova, frequenti da `3`.
A parità di frequenza prevale la prima osservazione nel training. Sono supportati
stringhe, booleani, interi e reali finiti: `"1"`, `1` e `True` sono distinti; `1` e
`1.0` rappresentano la stessa categoria numerica.

Un bucket senza supporto nel training dà effetto monovariato zero. Se un'interazione
contiene almeno un bucket senza supporto, l'intera tabella contribuisce zero per
quella riga: nessuna collisione restituisce un valore appreso da righe estranee.
Le celle di memoria vuote hanno punteggio zero.

## Obiettivi e aggiornamento dei blocchi

La penalità riguarda `U` e `V`, mai l'intercetta:

```text
regressione = 0.5 Σ_i w_i (y_i-F_i)² + 0.5 l2 (Σ U² + Σ V²)
binaria     = Σ_i w_i [logaddexp(0,F_i)-y_i F_i] + 0.5 l2 (Σ U² + Σ V²)
```

`l2>0`; i pesi sono finiti, non negativi e con somma positiva. Sono somme di loss,
quindi moltiplicare tutti i pesi modifica il rapporto fra fit e regolarizzazione.
L'intercetta iniziale è la media pesata, oppure il logit della frequenza pesata.
Codici e gruppi vengono inizializzati da un RNG locale; i punteggi iniziano a zero.
Due passaggi aggiornano i punteggi prima della prima ricerca dei codici. Con iterazioni
numerate da 1, l'adattamento avviene quando `iteration>2` e
`(iteration-3) % adapt_every == 0`: ai default nei passaggi 3, 5, 7, e così via.

Si visitano intercetta, effetti monovariati e interazioni mantenendo fissi gli altri
contributi. Per una tabella, `q=F_old-v_old[address_old]`:

| Task | `h_i` | `r_i` | Significato |
| --- | --- | --- | --- |
| Regressione | `w_i` | `y_i-q_i` | Quadratico esatto. |
| Binaria | `w_i/4` | `v_old[address_old_i]+4(y_i-sigmoid(F_old_i))` | Maggiorazione logistica con curvatura globale `1/4`. |

`h` e `r` rimangono congelati durante l'intera ottimizzazione del blocco, comprese
le mosse dei codici. Si ricalcolano entrando nel blocco seguente. La formula binaria
deriva da `sigmoid(F)(1-sigmoid(F)) <= 1/4`; non è l'Hessiano esatto.

Per ogni cella si aggregano in `float64`:

```text
A[m] = Σ_{i: address_i=m} h_i
B[m] = Σ_{i: address_i=m} h_i r_i
V[m] = B[m] / (A[m] + l2)
G = 0.5 Σ_m B[m]² / (A[m] + l2)
```

Le aggregazioni usano `np.bincount`. Massimizzare `G` minimizza il quadratico
regolarizzato a meno di una costante. Gli effetti monovariati hanno indirizzo uguale
al bucket e non adattano codici. L'intercetta usa l'aggiornamento scalare senza L2.
I valori della tabella vengono sostituiti, non aggiunti ripetutamente al vecchio stato.

## Riindirizzamento incrementale

Una coordinata `(t,j,b)` riguarda soltanto le righe con `z_j=b`. Per passare da `c`
a `c_new`, definisci `delta=(c_new-c) mod M`. Le righe del gruppo si spostano a
`(address_old+delta) mod M`. Una volta per coordinata:

```text
D[m] = Σ_{i nel gruppo, address_i=m} h_i
E[m] = Σ_{i nel gruppo, address_i=m} h_i r_i
A_new = A - D + roll(D, delta)
B_new = B - E + roll(E, delta)
gain = G(A_new, B_new) - G(A, B)
```

`roll(D, delta)[m]` porta nella cella `m` il contributo proveniente da
`(m-delta) mod M`. Gli indici dei gruppi sono preparati una volta e riutilizzati:
non si scansiona l'intero dataset per candidato. I candidati sono nuovi codici
distinti generati dal RNG del modello; lo stato invariato è sempre ammissibile.

Si accetta soltanto il candidato migliore quando
`G_new-G_old > 1e-12*max(1, abs(G_old))`. Nella sottrazione `A-D` si ammettono residui
negativi soltanto entro `64*eps*max(1, abs(A[m]), abs(D[m]))` per cella, con `eps` di
`float64`: questi residui sono azzerati; negatività significativa solleva
`FloatingPointError`. Non si corregge indiscriminatamente qualunque massa con clipping.

Una mossa accettata aggiorna codici, statistiche e indirizzi del gruppo. Le coordinate
seguenti vedono gli indirizzi aggiornati. Dopo mosse accettate si riaggregano `A,B`
una volta a fine blocco in `O(n)`, evitando deriva e mantenendo zero le celle vuote.
Alla fine del blocco si ricalcola `V` e
`F=q+V[address]` su tutte le righe: cambiare le medie delle celle può modificare anche
righe esterne al gruppo. Per la binaria il guadagno è quello del surrogato congelato,
non il miglioramento esatto della log-loss.

`max_code_updates` limita le **coordinate valutate per tabella e passaggio adattivo**,
non le mosse accettate. `min_code_count` conta righe a peso positivo, non la somma dei
pesi. La visita delle coordinate ammissibili è a rotazione riproducibile.

## Validation, arresto e persistenza

Con `eval_set` si usa la validation passata dall'utente; altrimenti l'early stopping
crea uno split riproducibile e stratificato per la classificazione. Dati insufficienti
producono un errore che indica come disabilitare lo split. Non si usa il training come
validation implicita. La validation non propone e non accetta mosse dei codici.

L'arresto usa MSE non pesata o log-loss non pesata, senza L2, e richiede miglioramento
assoluto superiore a `tol`. Con `early_stopping=False` ed `eval_set` la loss è registrata,
ma non si interrompe o ripristina lo stato sulla validation. Il miglior stato include
intercetta, tabelle monovariate, tabelle di interazione e codici. Dopo mosse dei codici
si ricomputano correttamente gli indirizzi di validation. `n_iter_` conta i passaggi
eseguiti; `best_iteration_` identifica lo stato selezionato. La cronologia non viene
troncata quando lo stato migliore viene ripristinato.

Alla fine vengono liberati target, bucket, indirizzi, indici dei gruppi e cache del
training. La previsione dipende dal modello e dal nuovo batch, non da righe conservate.
Vocabolari e soglie, in quanto parametri del preprocessing, rimangono nel modello.

## Costi dell'implementazione

Siano `n` righe, `p` feature, `T` tabelle, `s` feature per tabella, `M` celle, `U`
coordinate visitate per tabella/passaggio e `C` candidati per coordinata. Sia `K_j`
il numero di bucket della feature `j`.

| Operazione | Costo e componenti |
| --- | --- |
| Kernel di previsione | `O(n(p+T*s))`, più maschere di supporto; nessuna ricerca di codici. |
| Trasformazione numerica | Circa `O(n*p_num*log(n_bins))`, oltre a conversione e controlli. |
| Preparazione numerica | Quantili su un campione limitato per feature, soglie uniche e trasformazione del training. |
| Trasformazione categorica | Mappatura tramite strutture native/pandas; dipende anche da lunghezza delle stringhe e cardinalità. |
| Aggiornamenti dei punteggi | Circa `O(n(p+T)+Σ K_j+T*M)` per passaggio, oltre al calcolo degli indirizzi. |
| Ricerca dei candidati | `O(T*U*C*M)` per passaggio adattivo, oltre ad aggregazioni dei gruppi e aggiornamenti degli indirizzi. |
| Statistiche di un gruppo | `O(n_gruppo+M)` per coordinata; non viene ripetuta per ciascun candidato. |
| Memoria del modello | `O(Σ K_j+T*M+Σ_t Σ_{j in S_t} K_j)`, più soglie, vocabolari e cronologia. |
| Memoria temporanea di fit | Bucket `O(n*p)`, indirizzi e indici, vettori reali `O(n)` e statistiche `O(M)`; dipende dalle cache effettive. |

Le strutture dei gruppi e la gestione dei DataFrame hanno costi ulteriori. La memoria
dei vocabolari rari può dipendere dalle categorie osservate necessarie a distinguere
rare e sconosciute. Non è garantito che la ricerca discreta sia economica su tutti i
dataset. I limiti vengono verificati prima delle allocazioni principali. La stima
conservativa del fit viene rifiutata oltre 512 MiB; il limite della sola matrice bucket
è anch'esso 512 MiB. Questo non costituisce un limite rigido del picco RSS del processo,
perché interprete, input, vocabolari e temporanei introducono memoria aggiuntiva. Il
vocabolario di membership è limitato a un milione di categorie osservate per feature.

Queste formule non sono promesse di latenza costante. Il profilo separa preprocessing,
indici, punteggi, ricerca, validation, ripristino e `fit` completo. Per confronti
pratici usare latenza end-to-end, RSS e dimensione serializzata insieme alla qualità.
I riferimenti matematici brute-force nei test servono a verificare il percorso
incrementale su shift, collisioni, masse vuote, pesi e mosse successive.
