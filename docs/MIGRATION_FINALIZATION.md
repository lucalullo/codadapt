# Finalization of the 59 historical-file decisions

The review of all 59 paths is complete as a technical migration plan. The source
hashes, individual decisions and destinations are retained in
[HISTORICAL_MIGRATION.json](../HISTORICAL_MIGRATION.json) and the
[migration plan](../MIGRATION_PLAN.md). That completed review is not approval to
delete files from the real repository.

The plan records 10 updates, 5 files retained, 4 historical documents retained
with scope labels, 34 integrations and 6 proposed exclusions. Useful algorithm,
AUTO/memory, optional-component, stability, migration and example documentation
has been retained or restored. Thirty historical test/helper files are already
under tests/legacy; they should not be duplicated at their former paths.

The proposed exclusions are the two publication workflows, the obsolete agent
instruction file, the old official-candidate status page, and two detailed
scientific-memory documents. Their original bytes remain preserved separately.
Detailed internal research is not part of this public source candidate.
The only supplied CI is manual and has no publishing step.

The owner must approve every removal or path consolidation in the actual
repository, including removal of a former test path after its contents have
been integrated elsewhere. Preserve .git, version history and unrelated changes.
Do not replace the old repository by deleting it wholesale or infer a deletion
instruction from an absent file in this candidate.

The final file comparison, candidate manifest and [gate report](../GATES_REPORT.md)
must be reviewed alongside the plan before manual transfer. Version preparation
does not modify the original project, apply real-repository removals or grant
publication approval.
