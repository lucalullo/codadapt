# Historical predecessor report — not qualification of this new delivery

The following unabridged report belongs to the preceding local 2.1 review. Its LOCAL_READY/ENGINEERING_QUALIFIED states, wheels, tests and timings apply only to that recorded predecessor. See ../RAPPORTO_FINALE.md for current status.

# R3 private source proposal — HOLD

Linux defaultbuild changed; automatic Linux inference remains Python.
No nativeLinuxwheel or KaggleCpp execution is qualified yet. Historical results
below retain their originalscope. See [docs/R3_NATIVE_INTEGRATION.md](../docs/R3_NATIVE_INTEGRATION.md).

# CodAdapt 2.1.0 — consegna locale definitiva

Il repository è pronto per l'approvazione e il trasferimento manuale nel perimetro
qualificato. La pubblicazione e la sostituzione dell'originale non sono autorizzate.
Prima di applicare una copia sovrapposta, occorre approvare le 38 rimozioni proposte
e controllare i file presenti nella destinazione, soprattutto i quattro workflow.
Il backup fisicamente indipendente resta obbligatorio prima della sostituzione
o eliminazione dell'originale.

## Correzioni consegnate

- Generatore, verificatore e test delle ricevute condividono l'identità degli
  input. Le cache dei normali import non causano più ricevute incoerenti.
  Sorgenti, file non-cache e altri input vincolati continuano a essere verificati.
- Il runner copia e vincola tutti i 12 file radice e i due benchmark previsti
  nella build. Non include dataset estranei. Lo sdist finale contiene questi file.
- Tutti i 59 percorsi storici sono stati verificati individualmente. Le 38
  rimozioni proposte comprendono quattro workflow, 29 vecchi percorsi di test e
  cinque altre voci. Sono preservati 30 test/helper in `tests/legacy`: 28 identici
  e due con gli adattamenti già qualificati.
- La documentazione distingue C++ esplicito, selezione automatica, nuove prove
  e risultati precedenti. Il blocco pandas riguarda il profilo 3.12, non tutti
  i nuovi consumer.

I 41 file di prodotto Python/C++, incluso il contratto serving, sono identici
alla precedente candidata 2.1.0. Nessuna strategia predittiva, parametro predefinito,
formato o regola di compatibilità è stata modificata.

## Verifiche eseguite in questa revisione

| Verifica | Risultato |
|---|---|
| Ricevute prima degli import, Windows 3.14 | 26 PASS |
| Ricevute dopo import normale con cache reali, 3.14 | 17 PASS |
| Ricevute dopo import normale con cache reali, 3.10 | 26 PASS |
| Correzione finale degli input del runner e relative ricevute | 32 PASS |
| Nuove wheel native, 3.10 e 3.14 | 148 PASS, 1 SKIP per profilo, sui test strumenti e confine/dispatch |
| Nuova wheel pura, 3.10 e 3.14 | 47 PASS, 51 SKIP attesi per assenza nativa, per profilo |
| Controllo finale dei cinque artifact e dello sdist aggiornato | 4 PASS; 14 input del runner verificati nella build |
| Quattro consumer puliti | Installazione, pip check, import ed esempi binario/multiclasse/regressione PASS |
| Modelli G6-R1 salvati | 126 confronti esatti per consumer nativo, 84 per puro; nessun fit |
| Export della precedente candidata 2.1.0 | Accettati: 126 confronti esatti per consumer nativo, 63 per puro |

I casi e i modelli possono essere condivisi fra queste verifiche: i conteggi non
sono repliche scientifiche indipendenti. Le ricevute, gli hash e gli esiti sono in
[FINAL_CHECKS.json](../qualification/FINAL_CHECKS.json) e
[ARTIFACT_FINAL_CHECKS.json](../qualification/ARTIFACT_FINAL_CHECKS.json).

La suite completa precedente resta 1012 PASS, 3 SKIP e 4 XFAIL su Windows 3.14.
Su 3.10 resta 1002 PASS, 1 SKIP, 4 XFAIL e 12 ERROR del componente opzionale EBM,
la cui DLL è bloccata da App Control. Questi risultati ancora validi per il codice
immutato non sono presentati come nuove esecuzioni. Gli errori non sono stati
nascosti o convertiti in skip. Non sono stati ripetuti fit scientifici.

## Backend e prestazioni

Tre modelli ingegneristici salvati sono stati misurati con nove processi appaiati
per profilo, senza fit e senza altre build o benchmark concorrenti:

| Multiclasse, batch 2.048 | Python mediano | C++ esplicito mediano | Riduzione |
|---|---:|---:|---:|
| Windows x64 / Python 3.10.22 | 1,8830 ms | 1,1001 ms | 41,58% |
| Windows x64 / Python 3.14.10 | 1,6308 ms | 0,9593 ms | 41,18% |

Output esatti, stato immutato e limiti di latenza p95/RAM rispettati nel corpus
finito. I campioni completi, le altre dimensioni di batch e il protocollo sono
inclusi. Queste misure precedono la ricostruzione dei pacchetti: i sorgenti e la
sezione macchina `.text` dei nuovi moduli sono identici; gli hash dei binari
completi differiscono e sono registrati. Le nuove wheel sono state verificate
funzionalmente. Nessun nuovo speedup di training o miglioramento di accuratezza
multiclasse è dichiarato.

Il backend automatico resta **Python su 3.10 e 3.14**. Espandere il guard cambierebbe
l'identità sorgente e renderebbe incompatibili gli export 2.1.0 già prodotti,
senza una migrazione verificata e autorizzata. Il guard 3.12.10 conserva la prova
storica G6-R1; non certifica una nuova installazione 2.1.0/3.12. Il contesto nativo
esplicito è uno strumento privato di qualificazione, non un nuovo parametro API.
Vedere [NATIVE_PROFILE_DECISION.md](../docs/NATIVE_PROFILE_DECISION.md).

## Packaging e persistenza

Wheel cp310, cp312, cp314, wheel pura e sdist sono consegnati separatamente dai
sorgenti. Le wheel native sono state compilate da sdists verificati. Lo sdist
canonico finale aggiorna soltanto documentazione, strumenti delle ricevute e test:
tutti gli input che determinano codice e metadati delle wheel sono identici.
Non occorre ricompilare un motore che questi cambiamenti non invalidano.

[DISTRIBUTIONS.json](../qualification/DISTRIBUTIONS.json) identifica ogni artifact.
Il manifest del repository vincola i file della cartella; lo ZIP è verificato
contro tutti questi file. Rapporti e ricevute emessi dopo le esecuzioni sono
metadati di consegna esterni allo sdist, non risultati retroattivamente inseriti
in archivi precedenti. Una wheel precompilata non richiede un compilatore.

Il contratto serving 2.1.0 resta invariato. Gli export 2.1.0 precedenti sono stati
caricati realmente; quelli G6-R1 continuano a richiedere il loro runtime. Non è
introdotta una migrazione implicita o un'allowlist. La compatibilità finita di
pickle/joblib non garantisce portabilità universale fra versioni o dipendenze.

## Gate residui

| Stato | Valore e perimetro |
|---|---|
| LOCAL_READY | YES — Windows x64 / Python 3.14.10 con pin dichiarati; core 3.10.22 |
| ENGINEERING_QUALIFIED | YES — nello stesso perimetro, con EBM opzionale 3.10 in HOLD |
| MULTICLASS_IMPROVEMENT_QUALIFIED | NO |
| BINARY_REGRESSION_PRESERVED | YES — nei test, API e corpus verificati |
| CROSS_PLATFORM_QUALIFIED | NO |
| BACKUP_A | HOLD |
| RELEASE | HOLD |

Python 3.12.10 ha build ma non un nuovo runtime pulito qualificato; gli altri
profili Windows bloccati mantengono i limiti documentati. Linux e macOS richiedono
prove reali. Il backup indipendente non è ancora stato comunicato e verificato.
Nessuna protezione di Windows è stata aggirata.

## Trasferimento manuale

1. Confrontare lo SHA-256 del manifest con la consegna e verificare la copia con
   `python tools/verify_repository.py`.
2. Esaminare [FILE_COMPARISON.json](../FILE_COMPARISON.json) e approvare personalmente
   le [38 rimozioni proposte](../REMOVALS_REQUIRING_APPROVAL.md), confrontando gli hash
   correnti. Una copia sovrapposta non disattiva i quattro vecchi workflow.
3. Seguire [le istruzioni](../ISTRUZIONI_TRASFERIMENTO_GITHUB.md). Completare backup e
   qualificazioni necessarie prima di sostituire definitivamente l'originale.
4. Per l'uso locale, installare la wheel nel profilo autorizzato e seguire
   [LOCAL_USE.md](../LOCAL_USE.md). La pubblicazione resta una decisione dell'utente.

Originale, G5, G6-R1, C11, review precedenti e memoria scientifica sono preservati.
Nessuna operazione Git/GitHub, accesso ad account o pubblicazione è stata eseguita.
