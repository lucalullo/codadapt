"""Canonical source and qualification-input identities for local receipts.

Only Python's ``__pycache__`` directories are excluded from these identities.
Unrecognized files, compiled extensions and bytecode outside that directory stay
bound as product inputs. Distribution identities are bound separately and are
never filtered by this module.
"""
from pathlib import Path
import hashlib

ROOT_BUILD_INPUTS = (
    "setup.py", "pyproject.toml", "README.md", "LICENSE", "MANIFEST.in",
    "CHANGELOG.md", "RELEASE_NOTES.md", "SECURITY.md", "CONTRIBUTING.md",
    "MIGRATION_PLAN.md", "ISTRUZIONI_TRASFERIMENTO_GITHUB.md", "GATES_REPORT.md",
)

BENCHMARK_BUILD_INPUTS = (
    "benchmarks/native_profile_benchmark.py",
    "benchmarks/NATIVE_PROFILE_PROTOCOL.md",
)


def _digest(paths, root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(set(paths))
        if path.is_file() and "__pycache__" not in path.relative_to(root).parts
    }


def source_identity(root):
    """Bind every non-cache file in the Python and native source directories."""
    root = Path(root)
    return _digest(
        (path for name in ("src", "native") for path in (root / name).rglob("*")),
        root,
    )


def qualification_inputs(root):
    """Bind tests, dependencies, root build documents and two benchmark files."""
    root = Path(root)
    paths = [root / name for name in ROOT_BUILD_INPUTS]
    for name, pattern in (("tools", "*.py"), ("tests", "*.py"), ("requirements", "*.txt")):
        paths.extend((root / name).rglob(pattern))
    paths.extend((root / "tests").rglob("*.npz"))
    paths.extend(root / name for name in BENCHMARK_BUILD_INPUTS)
    return _digest(paths, root)
