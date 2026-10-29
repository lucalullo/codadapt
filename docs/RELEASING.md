# Manual release preparation remains gated

The source tree is a locally prepared 2.1.0 release candidate, not an
approved or published release. Version 2.1.0 and all distribution artifacts
require explicit maintainer approval. See [versioning](VERSIONING.md) for
copy-only version changes and regeneration of the source-bound serving contract.
Build native/pure wheels and sdist, qualify the exact artifacts and actual hosts,
retain old matching runtimes for old serving images, review all manifests and
complete the independent-backup/platform gates. Do not infer support from metadata.

Publication and all account/GitHub operations belong exclusively to the owner.
No publish workflow is supplied. Historical notes remain available in
[historical release notes](HISTORICAL_RELEASE_NOTES.md) and CHANGELOG history.
See [manual file transfer](../ISTRUZIONI_TRASFERIMENTO_GITHUB.md).
