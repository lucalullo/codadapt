# Trasferimento manuale — CodAdapt 2.1.0 proposta

Questa cartella contiene i file destinati alla revisione e al possibile trasferimento manuale.
La preparazione locale non autorizza pubblicazione, rimozioni o sostituzione dell'originale.
Il proprietario mantiene il controllo di ogni operazione sul proprio repository e sugli account.
Lo stato effettivo è in [GATES_REPORT.md](GATES_REPORT.md).

## Prima del trasferimento

1. Verificare la copia ricevuta con `python tools/verify_repository.py`, usando un Python autorizzato.
   Confrontare anche l'impronta del manifest con quella comunicata nella consegna: un manifest
   accompagnato ai file è una verifica d'integrità, non un'autenticazione indipendente della provenienza.
2. Leggere [MIGRATION_PLAN.md](MIGRATION_PLAN.md), [FILE_COMPARISON.json](FILE_COMPARISON.json)
   e [REMOVALS_REQUIRING_APPROVAL.md](REMOVALS_REQUIRING_APPROVAL.md).
3. Approvare personalmente i **38 REMOVE proposti** prima di applicarli. La lista usa l'inventario
   storico, non il repository reale corrente. Confrontare ogni file reale con lo SHA-256 elencato;
   un file modificato o aggiunto nel frattempo richiede una nuova valutazione, non la cancellazione automatica.
4. Completare il backup fisicamente indipendente e le qualificazioni necessarie prima di eliminare,
   sostituire o migrare l'originale. Conservare tutte le versioni precedenti e i relativi runtime.

## I quattro workflow precedenti richiedono una decisione esplicita

Una copia dei nuovi file sopra i vecchi **non rimuove**:

- `.github/workflows/tests.yml`, con trigger automatici `push` e `pull_request` oltre a quello manuale.
- `.github/workflows/release-qualification.yml`, vecchia qualificazione manuale.
- `.github/workflows/publish-pypi.yml`, pubblicazione manuale con `id-token: write`.
- `.github/workflows/publish-testpypi.yml`, pubblicazione manuale su TestPyPI con `id-token: write`.

La copia nuova contiene soltanto `.github/workflows/qualification.yml`: esecuzione manuale,
permessi di lettura e nessuna pubblicazione. I quattro vecchi file sono proposti per rimozione
dalla futura copia aggiornata. Il proprietario deve decidere e gestire questi file prima di
considerare il trasferimento coerente e prima di una propria futura operazione remota.
Non sono stati disattivati, rinominati o cancellati da Codex.

## Copia e controllo locale del proprietario

- Conservare `.git`, la cronologia, le personalizzazioni e i file estranei alla consegna.
  Non cancellare l'intera cartella di destinazione e non usare una sincronizzazione distruttiva.
- Applicare ADD e MODIFY soltanto dopo la verifica dei file correnti; KEEP resta invariato.
  Applicare REMOVE soltanto per le voci approvate, con l'hash atteso o una decisione personale
  sul file cambiato. Non duplicare i 29 vecchi percorsi di test ricollocati in `tests/legacy/`.
- Non trasferire ambienti virtuali, wheel/sdist, cache, log privati, backup o memoria scientifica
  insieme ai sorgenti. I pacchetti installabili vengono consegnati separatamente.
- Eseguire nuovamente `python tools/verify_repository.py` nella copia ottenuta. Tutti i file
  del manifest devono corrispondere; gli extra vanno esaminati personalmente. La sola scritta
  `integrity: PASS` non approva gli extra e non prova che un overlay sia completo.
- Installare una wheel coerente in un ambiente pulito autorizzato e seguire
  [INSTALLATION](docs/INSTALLATION.md) e [QUALIFICATION](docs/QUALIFICATION.md).
  Rieseguire sul risultato della copia i controlli pertinenti di import, API, binario,
  multiclasse, regressione, esempi, persistenza/export e integrità, registrando le ricevute.
  Un cambiamento ai sorgenti rispetto alla consegna invalida la precedente identità degli artifact.

## Persistenza, compatibilità e gate

Non cambiare o aggirare il contratto degli export precedenti. Conservare gli export serving
con il runtime compatibile: non è autorizzata una migrazione automatica. Le verifiche finite
su pickle/joblib non costituiscono una garanzia universale tra dipendenze o piattaforme.
Vedere [PERSISTENCE](docs/PERSISTENCE.md).

La qualifica nativa esplicita e l'accelerazione C++ automatica hanno perimetri distinti:
consultare [COMPATIBILITY](docs/COMPATIBILITY.md) e i risultati finali. Non dedurre supporto
Linux/macOS o di altre versioni Python da metadati, cross-compilazione o vecchi risultati.
Non aggirare App Control. Backup indipendente e altri gate esterni restano aperti ove indicato.

La copia è consegnata per approvazione e trasferimento manuale nel perimetro qualificato.
Il trasferimento non equivale a una release autorizzata. Pubblicazione e ogni operazione
sugli account restano esclusivamente del proprietario. **RELEASE = HOLD.**
