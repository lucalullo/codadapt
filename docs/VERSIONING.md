# Version and serving-contract preparation

This copy prepares the proposed version `2.1.0` from the preserved
`2.0.0.dev0+lab.g6r1` source. The owner authorized preparation, not publication.
A version change, successful source check or build does not qualify a runtime.
The current executed results and remaining requirements are in
[GATES_REPORT.md](../GATES_REPORT.md).

## Check the current source identity

Run `python tools/prepare_version.py --check` from this repository. The tool
checks the project version, literal package version, Python-source fingerprints,
serving-source fingerprints and canonical combined hash. It imports no product
or model and executes no source from the repository.

The algorithm matches the serving exporter: SHA-256 of each `.py` byte stream,
with keys relative to the package prefixed by `codadapt/`, followed by SHA-256
of `json.dumps(native_sources, sort_keys=True, separators=(",", ":")).encode()`.
Native C++ binaries are not serialized in serving images; source, build flags
and ABI remain separately bound by artifact and qualification manifests.

## Prepare a new independent version

The copy-only tool requires an explicitly chosen new version and a new sibling
destination. It rejects an existing or overlapping destination and published
version `2.0.0`. It first validates its source, then copies regular files and
updates only `pyproject.toml`, `src/codadapt/_version.py` and
`src/codadapt/serving/source_contract.json`. The fingerprints are regenerated
from the destination's actual bytes. The source tree is never edited in place.

Old wheels, sdists, build caches, test receipts and integrity manifests are not
carried forward as evidence for the new identity. `VERSION_PREPARATION.json`
records exact changes and remaining references for review. The result remains
**UNQUALIFIED** with **RELEASE = HOLD** until the required new checks complete.

For a subsequent preparation, consult `python tools/prepare_version.py --help`
and supply both `--destination` and `--new-version`; do not request `2.1.0`
again from this already-versioned source. Each future number still requires the
owner's decision. A global string replacement must not rewrite dependency pins,
test fixtures, historical release entries or old experiment versions.

## Verify distributions and compatibility

Build native/pure wheels and sdist in isolated directories using the documented
build process. Check the exact version in METADATA, wheel tags, RECORD hashes,
the packaged source contract and all product payload bytes. Verify a native
build from the exact source distribution. Install final artifacts in clean
compatible consumer environments and execute the standard complete suite,
three-task examples, API/clone/Pipeline/weights, determinism, persistence/export
and fallback checks. Record failures rather than substituting an earlier
runtime's PASS for the new distribution's execution.

Reissue final manifests and receipts for the exact resulting files. Any
unavailable platform or OS-policy blocker remains open until real authorized
execution succeeds. Recheck performance where payload or runtime changes justify
it; version preparation alone does not produce a new speed or accuracy claim.

## Old models and producer contracts

Changing `_version.py` changes the source and contract hashes even when all
predictive arithmetic is unchanged. The loader still accepts only its exact
producer contract and declared runtime profile. G6-R1 serving images must stay
paired with the preserved G6-R1 runtime. The procedure never rewrites old images,
adds an unchecked predecessor allowlist or relaxes validation.

Raw pickle/joblib compatibility is a separate question and must be verified in
the exact declared environments. Cross-major NumPy/pandas loading is not
promised. Keep old matching environments available until an explicit migration
is independently qualified. A SHA-256 value checks consistency against a
trusted reference, not artifact origin or safe unpickling.
