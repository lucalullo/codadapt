# CodAdapt agent instructions

Before research or architecture work, read:

1. `docs/research/RESEARCH_MASTER.md`
2. `docs/research/RESEARCH_STATE.json`

These two tracked files are the persistent research memory of the project. Treat their round index, rejected directions, evidence labels, reopen conditions, and next experiments as authoritative continuity context.

Rules:

- Do not repeat a closed experiment without a new falsifiable reason that satisfies its reopen condition.
- Development results are not confirmation; synthetic wins are not real-data wins.
- Do not change the public default/API based only on development evidence.
- Keep `research_private/` local and out of Git/distributions.
- After every completed research round, update both files under `docs/research/`, validate the JSON, and keep the round index continuous.
- Do not commit, push, tag, or publish automatically unless the user explicitly asks.
- If research-memory prose conflicts with current runtime code, inspect the code and document the discrepancy rather than silently changing behavior.
