# CodAdapt 2.1.0 — proposed candidate, publication not approved

Final technical correction: unify receipt identities across producer, verifier
and synthetic tests; exclude normal __pycache__ without ignoring other inputs.
Verify before/after ordinary imports. Finalize 38 manual removal proposals from
59 historical decisions, including 4 obsolete workflows. Preserve every 2.1.0
product byte and serving contract. Explicit native 3.10/3.14 measurements are
separate from automatic dispatch, which remains unchanged. See RAPPORTO_FINALE.md.

This is a locally prepared review candidate. The version number 2.1.0 identifies
the newly prepared source, contract and distributions; it does not authorize
publication or replacement of the preserved implementation.

The candidate carries forward the existing G6-R1 engineering work: ordered
C++17 inference with a Python fallback, bounded temporary allocations for large
numeric inference batches, guarded numeric DataFrame handling, optional internal
TRAIN-mass class balancing, and source-bound serving artifacts. No new strategy
of learning or multiclass prediction is introduced in this final preparation.

Repository preparation includes complete default test selection, version and
contract preparation tools, manual bounded CI, distribution checks, restored
useful documentation/examples and individual decisions for 59 historical paths.
Generated distributions remain separate from tracked repository source.

The version change regenerates `serving/source_contract.json` from actual source
bytes. A 2.1.0 runtime is not promised to load serving images produced by G6-R1
or other older source contracts. Preserve the old matching runtime and artifacts.
Raw pickle/joblib compatibility has a different contract and must be verified
in each declared dependency environment; cross-major NumPy/pandas portability
is not promised.

[GATES_REPORT.md](GATES_REPORT.md) is authoritative for tests actually executed
on this candidate and for remaining failures or blockers. Earlier numerical,
platform and benchmark observations retain their original version and scope;
they are not new 2.1.0 qualification results. No new accuracy, universal bitwise
portability or universal superiority claim is made.

Before publication or replacement, the owner must approve the final version
and migration decisions and satisfy all mandatory gates. Backup independence,
unexecuted platforms and OS-policy denials cannot be changed into PASS by
documentation. No publication workflow is included.
