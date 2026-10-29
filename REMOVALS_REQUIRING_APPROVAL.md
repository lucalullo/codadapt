# Rimozioni proposte: approvazione del proprietario necessaria

Sono **38 percorsi**, non soltanto i sei esclusi per contenuto.
I 30 test/helper sono trasferiti in `tests/legacy/`; altre voci sono integrate in documenti o strumenti nuovi.
Nessuna rimozione è stata applicata o approvata. Gli originali restano nelle copie preservate.

La lista deriva dall'inventario storico verificato. Non costituisce una scansione del repository reale:
se un hash non corrisponde, esaminare la modifica intervenuta prima di decidere; non cancellare automaticamente.

## Quattro workflow che una semplice copia sovrapposta lascerebbe attivi

- `.github/workflows/tests.yml`: trigger `push`, `pull_request` e manuale; resterebbe eseguibile automaticamente.
- `.github/workflows/release-qualification.yml`: vecchia qualificazione manuale e vecchia matrice.
- `.github/workflows/publish-pypi.yml`: pubblicazione manuale, permesso `id-token: write` e trusted publishing.
- `.github/workflows/publish-testpypi.yml`: pubblicazione manuale su TestPyPI, stesso permesso.

La nuova copia contiene soltanto `.github/workflows/qualification.yml`, manuale, senza pubblicazione.
Omettere i vecchi file dalla consegna non li disattiva nel repository di destinazione.
L'utente deve approvare e gestire questi quattro percorsi prima di considerare il trasferimento coerente.

## Elenco completo e impronte storiche

| Percorso proposto per rimozione | SHA-256 storico | Destinazione funzionale / motivo |
|---|---|---|
| `.github/workflows/publish-pypi.yml` | `7529237f991901358dd5f444a4caec1270ca52a30e460d8eb99da5ab15d6d4c2` | Nessun equivalente di pubblicazione |
| `.github/workflows/publish-testpypi.yml` | `a27ad36192a06b24fa189ac50bb1fd626ca77283f73d0cbf5e279d4131d583a2` | Nessun equivalente di pubblicazione |
| `.github/workflows/release-qualification.yml` | `111c5a2433f49b0e0261d2efe28a7994966a589b2649dc34cf0e566aae3b8ff7` | .github/workflows/qualification.yml; docs/QUALIFICATION.md |
| `.github/workflows/tests.yml` | `7a1b5fea7b8b383056e15dd8876f1976234cdad2258d3db9fd5efbd49d8b1b83` | .github/workflows/qualification.yml; docs/QUALIFICATION.md |
| `AGENTS.md` | `c4dfc6674bf1e7dac5fe00aaf26112aba0f6a20ba11a6f8a5b0848f2c36950aa` | Documentazione pubblica normale; memoria privata preservata separatamente |
| `docs/OFFICIAL_PRODUCT_CANDIDATE.md` | `771e658f0c85686128fc6a4ae2e24990855acaa8d144c9b15fb902d5e23236ba` | docs/HANDOFF_REPORT.md; RELEASE_NOTES.md |
| `docs/research/RESEARCH_MASTER.md` | `6d3aaf874c929fade2ba25c5d1a0e3ab199931cb667bcfe81388aeda88f1bd29` | docs/PERFORMANCE.md; docs/HANDOFF_REPORT.md solo sintesi verificata |
| `docs/research/RESEARCH_STATE.json` | `cd19e7531579badd666fa57b6d6c5d3b6921dc64a695408b11e6fa74c5059444` | Matrice/stati pubblici sintetici, memoria privata integra |
| `examples/release_smoke.py` | `8658331ff50b74732fc45dc761bd243bb8a97e6205a255b03313d504faffa493` | examples/basic_usage.py; tools/engineering_probe.py; optional smoke mirato |
| `tests/_binary_reference.py` | `5615ae561b25ca117943064fe3a996880b141026bfa5d9105daadb53edde9bae` | tests/legacy/_binary_reference.py |
| `tests/_multiclass_helpers.py` | `38275b31d970ea67b609983293efe17fddd36dc50d42216b07b7a5d0548b4874` | tests/legacy/_multiclass_helpers.py |
| `tests/test_adaptive_levels.py` | `31923b7f1136b1b80131aaa8231c5396b2fd6fde00198812aa80c9f6559b4d85` | tests/legacy/test_adaptive_levels.py |
| `tests/test_addressing.py` | `ab489530ef4027a28180f300f5fb20b8d2311c9813da16186d9af94976023783` | tests/legacy/test_addressing.py |
| `tests/test_auto_memory.py` | `33d5b59f722975290e72a6718cf2bc4d87ca8bd9e6f445709e83bdccbf97d5e4` | tests/legacy/test_auto_memory.py |
| `tests/test_auto_memory_cgroup.py` | `98a6f0a0e0cf40657bc605bc81f6a632cbc6e1ed62b88cf475888654e650ee32` | tests/legacy/test_auto_memory_cgroup.py |
| `tests/test_auto_memory_policy.py` | `e9116338d38665d86614ee314962980f626e25e14567abe6445754828f9b1ddf` | tests/legacy/test_auto_memory_policy.py |
| `tests/test_cardinality.py` | `d2761105870685498540a96212ba9b753cddc93b8e85d9ac7dcb764c3ce00f9e` | tests/legacy/test_cardinality.py |
| `tests/test_classifier.py` | `a78a917d5e3a4c07b0b60645da8cd37e0cb4ddd1a24ed86ba1066e980ec4b503` | tests/legacy/test_classifier.py |
| `tests/test_classifier_training.py` | `00653b82c247549b6678b42b30100545ca6a051c99c0e8005feee9b78498cd2d` | tests/legacy/test_classifier_training.py |
| `tests/test_coded_memory.py` | `ecc223e3a7a43ce9b01dffd02579fba7408c5a8e57c3f4519ed228a042172e94` | tests/legacy/test_coded_memory.py |
| `tests/test_default_api.py` | `9c19cb1adf4a2804fe255dc611f8e47b6a06acf8aafdfaa3a93daa0ddf4600b0` | tests/legacy/test_default_api.py |
| `tests/test_ebm_compiler.py` | `968246c24668291093a4b49b8d6e2639877d667a87125a032c0adcbaf7b3400d` | tests/legacy/test_ebm_compiler.py |
| `tests/test_incremental_gain.py` | `5e8e67272e93472079e2d9b0fba00a6d2a06fb43666c061109afdd422959caa0` | tests/legacy/test_incremental_gain.py |
| `tests/test_independence.py` | `ef21a3b05678fc8b53467f3b981908144108a7bf26a3158325be5fd86b455b53` | tests/legacy/test_independence.py |
| `tests/test_inference_metadata_exact.py` | `364f1979f80960f08e42a2cfb983484a36f133409d81f721f295da7940047944` | tests/legacy/test_inference_metadata_exact.py |
| `tests/test_memory_budget.py` | `1c25c840fda2b6a6c6d77916f545cc73b652a0e7c62672ac010a60195b4b8fde` | tests/legacy/test_memory_budget.py |
| `tests/test_multiclass.py` | `217856da731e8e76eef569c8ddae42c16b9deb8be45f3721c61a4e21b20c1221` | tests/legacy/test_multiclass.py |
| `tests/test_no_leakage.py` | `9593f4731cf99b65d4bcefbc273e39db690d64315055f0352d189402d27bbb86` | tests/legacy/test_no_leakage.py |
| `tests/test_packaging.py` | `ecdf9910b710f663b968511bad4b7780ff7b3cff86c40a2c977f46041b3452de` | tests/legacy/test_packaging.py |
| `tests/test_persistence.py` | `fc8b2e39b9ed1e3bfca2b98b982e7f4029cb795867b37bc043b13f7ffa89f2d2` | tests/legacy/test_persistence.py |
| `tests/test_pre_rc_api.py` | `91761901009f46458e189fd787d7ba42d46267c304bb1e19f0f2289b166a7d78` | tests/legacy/test_pre_rc_api.py |
| `tests/test_preprocessing.py` | `1bebe09011a23f87c0358e08dbce3cce95993ddb18b22925f3aedea2e6deb469` | tests/legacy/test_preprocessing.py |
| `tests/test_rational_callback.py` | `b4cb40633b011be4b7fe21d3a8ef3a622c5edc4c007bf154fc6294f7f56f5a56` | tests/legacy/test_rational_callback.py |
| `tests/test_regressor.py` | `7eaa2d404bc7a17882c8f8ca9186d20cf700456f574a4dd28ecee8f0b5f9cf60` | tests/legacy/test_regressor.py |
| `tests/test_release_contracts.py` | `b1f4ce03922029e5d6c45bfd6d0bbb4fafb72c785c6b10eaa05e1060a6ba1d9c` | tests/legacy/test_release_contracts.py |
| `tests/test_safe_blend.py` | `249b5d5b8fae14f2f6a297c91abf2fd64362fd9b4f5e4bff65e2ed784a225aeb` | tests/legacy/test_safe_blend.py |
| `tests/test_shared_encoder.py` | `3947ab50ff462c6ad703311b7d409cd19520866a2eb6f4e3099c9b35745c74d9` | tests/legacy/test_shared_encoder.py |
| `tests/test_sklearn_compat.py` | `daa03657f3f30818366c5e89fde42effda186504253af68e273ddc928bb5f6f5` | tests/legacy/test_sklearn_compat.py |

I motivi individuali completi e le dimensioni sono in [REMOVALS_REQUIRING_APPROVAL.json](REMOVALS_REQUIRING_APPROVAL.json).
Il confronto completo ADD / MODIFY / KEEP / REMOVE è in [FILE_COMPARISON.json](FILE_COMPARISON.json).
