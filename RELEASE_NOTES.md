# CodAdapt 2.2.0

This is a technical improvement release of the adaptive coded-memory learner.
The predictive learning algorithm is unchanged. Combined classifier outputs,
optional zlib snapshots and immutable-input reuse address specific inference and
storage workloads. The restricted snapshot reader includes a tested pandas
compatibility correction. The serving source contract matches the current code.

## Scope and compatibility

- The wheel is pure Python. Historical optional C++ binaries are not built.
- Package metadata requires Python 3.12 or later. Python 3.10/3.11 users of 2.1.0
  must retain that release or migrate to an admitted environment.
- Native snapshot migration and producer-bound serving-image compatibility are
  different contracts. Preserve the original environment for rollback.
- The standalone lightweight serving/trace companion is not bundled. Its
  historical costs are documented separately.
- C60 remains not qualified. Independent Pareto remains not certified. No new
  predictive superiority is claimed.

The [benchmark suite](BENCHMARKS.md) includes all favorable, unfavorable,
inconclusive and missing outcomes. Competitive results measured on 2.1.0 are
separated from 2.2.0 technical measurements. See [compatibility](docs/COMPATIBILITY.md)
and [qualification](qualification/README.md) for the verified profile and checks.

## Safe repository replacement

Use the complete reviewed source tree rather than copying over stale generated
files. Keep the repository's `.git` directory and owner-managed configuration.
This archive contains the complete tracked source tree. Back up the previous
checkout and preserve `.git` and any required owner-managed local configuration
when replacing the old source files. The seven workflow filenames overwrite
their previous versions and perform checks only. They contain no publication,
registry upload, release, tag or credential-writing step.

Publication is a separate owner action after hosted checks and final hash
approval. Nothing in this archive performs it automatically.
