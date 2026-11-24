# License and attributions

The original CodAdapt components are licensed under MIT, Copyright (c) 2026
Luca Lullo. The author has identified himself as the original author and chosen
MIT for the components he has the right to distribute. [LICENSE](../LICENSE)
contains the operative grant. [The original 2.1.0 notice](CORE_210_MIT.txt) is
preserved unchanged. This is not a grant of rights in third-party components.

## Distribution boundary

The wheel includes CodAdapt Python source, its serving source-identity contract,
package metadata and license notices. It contains no vendored dependency
binaries, benchmark datasets, native extension binary or standalone lightweight
serving/trace companion. The sdist additionally includes documentation, aggregate
benchmark measurements, charts, tests, small synthetic snapshots and C++ sources
retained for reference.

[DEPENDENCY_NOTICE_INDEX.json](DEPENDENCY_NOTICE_INDEX.json) maps 67 preserved
notice texts to their upstream package, version and original wheel member, with
byte counts and SHA-256 digests. These notices include runtime, optional,
development and benchmark reference environments. They are not a list of
dependencies bundled into CodAdapt and do not imply that every package is needed
to run it. Third-party copyright, attribution, license conditions and disclaimers
are retained verbatim under `texts/`.

## Responsibilities

- Dependencies obtained separately retain their own license terms. Check the
  resolved environment, especially if redistributing dependency binaries.
- Optional EBM integration retains its pre-existing experimental status and
  upstream `interpret-core` terms. It is not a new CodAdapt predictive result.
- Benchmark tables and figures contain aggregate development measurements only.
  Dataset names identify sources; no original dataset is redistributed.
- Names of third parties do not imply endorsement. No third-party code is
  automatically relicensed as MIT.

No specific unresolved third-party code ownership issue was identified by the
source/notice inventory. The inventory is evidence of supplied material and
retained notices, not an independent attestation of every contributor's title or
clearance of patents, trademarks, or data rights for downstream uses.
