# CodAdapt 2.2.0

This is a technical improvement release of the adaptive coded-memory learner.
The predictive learning algorithm is unchanged. Combined classifier outputs,
optional zlib snapshots and immutable-input reuse address specific inference and
storage workloads. The restricted snapshot reader includes a tested pandas
compatibility correction. The serving source contract matches the current code.

## Migration from 2.1.0 (breaking distribution changes)

- **Python:** this release requires Python >=3.12. Users of Python 3.10/3.11 must upgrade their environment or retain a compatible CodAdapt 2.1.0 release. The metadata constraint is not a guarantee of every later Python version or platform.
- **C++ inference:** this release deliberately ships a pure-Python wheel and does not build or distribute the optional C++ backend. Native-backend users should keep a previously qualified 2.1.0 wheel, or build the historical 2.1.0 source using its original native-build instructions. Building the current checkout does not enable C++. Whether the extension returns in a future release is undecided; no return date is promised.
- **Persistence:** keep the producer version and its environment for existing serving images, or re-export from a compatible native snapshot.

## Scope and compatibility

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
when replacing the old source files. The seven workflow filenames overwrite their previous versions. Six are
verification-only; the TestPyPI workflow permits a separate, explicitly
selected manual upload after verification, via Trusted Publishing. It cannot
publish to production PyPI or create a release or tag.

Publication remains a separate owner action after hosted checks and final hash
approval. No push or tag automatically publishes a package.
