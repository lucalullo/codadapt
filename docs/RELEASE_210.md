# Owner review and publication procedure for 2.1.0

This repository is prepared for manual review, not already published. No command
here has been run against an account. The owner decides and performs all GitHub,
TestPyPI and PyPI operations. Multiclass innovation is a separate research task
and is not a prerequisite for this engineering delivery.

## Review and transfer

Verify the repository ZIP and distribution hashes, approve the exact file list
and declared profile set, and review REMOVALS_REQUIRING_APPROVAL.json. Overlaying
new files does not remove obsolete workflows; they must not silently remain
active. Follow ISTRUZIONI_TRASFERIMENTO_GITHUB.md. No .git directory, private
research, credentials, environment or model bank is part of this source archive.

The owner has deferred a full independent project backup for space reasons.
The compact verified release ZIP preserves release inputs only. It is not a
complete scientific-memory backup and does not make BACKUP_A PASS. Do not replace
or delete the original implementation before the independent-backup gate passes.
That gate does not block preparing this review repository.

## Artifact selection

The original qualified Kaggle Linux wheel remains linux_x86_64, not manylinux;
do not retag it or treat it as a portable index binary. Keep its paired original
sdist and receipt. New pure builds carry the refreshed README/docs with unchanged
product code; they need their own final target/download qualification. Do not
mix two different codadapt-2.1.0.tar.gz files or same-named wheels from different
directories. The exact delivery manifest, not a dist/* wildcard, selects bytes.

## TestPyPI and PyPI — owner only

1. Approve the exact candidate wheel/sdist pair and SHA-256 after the report review.
2. Run `python -m twine check --strict <exact-wheel> <exact-sdist>` locally.
   This checks metadata, not runtime or platform portability.
3. Owner alone: `python -m twine upload --repository testpypi <exact-wheel> <exact-sdist>`.
   Do not include the raw linux_x86_64 diagnostic wheel in this upload selection.
4. Download from the TestPyPI index with --no-deps into a NEW folder, compare
   hashes with the approved manifest, install dependencies from one authorized
   source and install the downloaded local wheel with --no-deps in a clean
   consumer. Run three-task/API/persistence checks and the applicable full suite.
5. If source installation is offered, test the actual sdist build separately.
6. Only after those tests and final approval, owner alone uploads the exact same
   bytes to PyPI and repeats download/hash/install/runtime checks. Do not overwrite
   a pre-existing 2.1.0 file or silently change the version; stop for owner review.

No tokens, .pypirc files or credential instructions are embedded in this delivery.
Index availability and owner authorization are not inferred from passing metadata.

References: [PyPA TestPyPI guide](https://packaging.python.org/en/latest/guides/using-testpypi/),
[platform tags](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/).
