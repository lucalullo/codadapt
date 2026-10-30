# Trasferimento manuale senza perdere la cronologia

La copia interna aggiornata è la fonte dei file del nuovo repository; lo ZIP
include gli stessi file pubblici e il manifest SHA-256. Non contiene .git.
Non sostituire la cartella .git del repository reale e non inizializzare un altro
repository al suo posto. Il proprietario gestisce GitHub Desktop e ogni operazione
Git/pubblicazione; nessuna è stata eseguita durante questa preparazione.

1. Verificare ZIP e manifest, estrarre in una cartella nuova e leggere il rapporto.
2. Prima della copia, il proprietario riesamina i vecchi workflow: un overlay non
   elimina publish-pypi.yml, publish-testpypi.yml, release-qualification.yml o
   tests.yml. Disabilitare la loro esecuzione nel proprio ambiente se necessario,
   senza attribuire alla nuova copia un'autorizzazione a pubblicare.
3. Copiare manualmente i soli file elencati nel manifest, preservando .git,
   originali, baseline e materiale privato fuori dalla distribuzione.
4. Esaminare le 38 esclusioni storiche esatte in REMOVALS_REQUIRING_APPROVAL.json.
   Nessuna eliminazione è stata eseguita o approvata automaticamente. Conservare
   i contenuti precedenti prima di decidere come gestirli nel repository attivo.
   Non caricare ricerche/dati privati per rendere identiche due cartelle.
5. Confrontare manualmente file e differenze. Eseguire il verificatore nella
   copia pubblica, riesaminare eventuali file extra e lanciare i test applicabili.
6. Solo dopo approvazione, il proprietario gestisce cronologia/commit/upload e
   le prove TestPyPI/PyPI secondo docs/RELEASE_210.md.

La ricerca multiclasse è separata. Il backup integrale è rinviato dal proprietario;
lo ZIP compatto non sostituisce il backup fisicamente indipendente richiesto prima
della sostituzione o eliminazione dell'implementazione originale.
