# Source layout

| Path | Purpose |
|---|---|
| `src/codadapt/` | 2.2.0 Python estimators, encoding, learning, inference, serving and persistence |
| `native/` | Historical C++ source reference (not built by the 2.2.0 backend) |
| `tests/` | Release checks, synthetic regression tests and snapshot fixtures |
| `examples/` | Small, self-contained user examples (not executed as benchmarks) |
| `benchmarks/` | Current standalone evidence transcription, figures, aggregate data and historical panel |
| `docs/` | User and developer documentation |
| `qualification/` | Scope and review receipts |
| `release/` | Status, source manifest, integrity checks and SBOM |
| `licenses/` | MIT license for original components and preserved third-party notices |
| `tools/` | Local verification and conversion utilities |

The standard-library PEP 517 backend is in `tools/release_backend.py`; its source allowlist is `release/SOURCE_MANIFEST.txt`. `PKG-INFO` and wheel metadata are generated only when building distributions, not stored at the root. Historical workflow paths run Python-backend checks; the two publication workflows use manual Trusted Publishing without additional dispatch inputs. The previous native build system is not activated. This is a complete replacement source tree, not a merge overlay. See [release notes](../RELEASE_NOTES.md).
