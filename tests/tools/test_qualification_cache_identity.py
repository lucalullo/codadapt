"""Receipt input identities survive normal imports, but never ignore source drift."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tool(root, name):
    spec = importlib.util.spec_from_file_location(name, root / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def isolated_repository(tmp_path):
    root = tmp_path / "repository"
    for name in ("src", "native", "tools", "tests", "requirements", "benchmarks"):
        (root / name).mkdir(parents=True)
    for name in ("setup.py", "pyproject.toml", "README.md", "LICENSE", "MANIFEST.in",
                 "CHANGELOG.md", "RELEASE_NOTES.md", "SECURITY.md", "CONTRIBUTING.md",
                 "MIGRATION_PLAN.md", "ISTRUZIONI_TRASFERIMENTO_GITHUB.md", "GATES_REPORT.md"):
        (root / name).write_text("SYNTHETIC RECEIPT FIXTURE ONLY\n")
    (root / "src/cache_probe.py").write_text("VALUE = 42\n")
    (root / "native/kernel.cpp").write_text("// SYNTHETIC: not compiled\n")
    (root / "tests/example.py").write_text("# SYNTHETIC: not executed\n")
    (root / "requirements/example.txt").write_text("# SYNTHETIC: not installed\n")
    (root / "benchmarks/native_profile_benchmark.py").write_text("# SYNTHETIC: not executed\n")
    (root / "benchmarks/NATIVE_PROFILE_PROTOCOL.md").write_text("SYNTHETIC PROTOCOL ONLY\n")
    for name in ("qualification_identity", "qualification_process", "qualify_platform", "verify_qualification_receipt"):
        shutil.copyfile(ROOT / "tools" / (name + ".py"), root / "tools" / (name + ".py"))
    return root


def make_receipt(root, folder):
    identity = load_tool(root, "qualification_identity")
    producer = load_tool(root, "qualify_platform")
    (folder / "probe").mkdir(parents=True)
    (folder / "dist").mkdir()
    (folder / "junit.xml").write_text('<testsuites><testsuite><testcase name="SYNTHETIC_ONLY"/></testsuite></testsuites>')
    (folder / "probe/RESULT.json").write_text(json.dumps(dict(status="PASS_FINITE_ENGINEERING_PROBE", native_batch2048_10pct_guard=False)))
    for name in ("fake.whl", "fake.tar.gz"):
        (folder / "dist" / name).write_bytes(b"SYNTHETIC ONLY")
    assert producer.qualification_inputs(root) == identity.qualification_inputs(root)
    record = dict(
        schema=2, status="PASS_EXECUTED_PROFILE", backend="native", functional_qualification="PASS",
        performance_gate="HOLD", automatic_platform_promotion=False,
        system="TEST_ONLY", machine="TEST_ONLY", python="TEST_ONLY",
        steps=[dict(label=name, returncode=0) for name in (
            "create_build_env", "build_dependencies", "dependency_preflight", "build",
            "create_consumer", "install_consumer", "dependency_check", "engineering_probe", "suite")],
        source_SHA256=identity.source_identity(root),
        qualification_inputs_SHA256=producer.qualification_inputs(root),
        runner_SHA256=sha(root / "tools/qualify_platform.py"),
        artifacts_SHA256={p.relative_to(folder).as_posix(): sha(p) for p in (folder / "dist").iterdir()},
    )
    seal(folder, record)
    return record


def seal(folder, record):
    (folder / "RESULT.json").write_text(json.dumps(record))
    manifest = dict(schema=2, files={
        p.relative_to(folder).as_posix(): sha(p) for p in folder.rglob("*")
        if p.is_file() and p.name != "RECEIPT_MANIFEST.json"
    })
    (folder / "RECEIPT_MANIFEST.json").write_text(json.dumps(manifest))


def verify(root, folder):
    return subprocess.run(
        [sys.executable, "-I", "-B", str(root / "tools/verify_qualification_receipt.py"), str(folder)],
        capture_output=True, text=True, timeout=20,
    )


def test_receipt_before_and_after_normal_import(isolated_repository, tmp_path):
    root = isolated_repository
    folder = tmp_path / "before_import"
    before = make_receipt(root, folder)
    outcome = verify(root, folder)
    assert outcome.returncode == 0, outcome.stderr

    # No -B and no inherited bytecode suppression: this is a real normal import.
    env = dict(os.environ)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    code = "import sys; sys.path.insert(0, sys.argv[1]); import cache_probe; assert cache_probe.VALUE == 42"
    imported = subprocess.run([sys.executable, "-I", "-c", code, str(root / "src")],
                              env=env, capture_output=True, text=True, timeout=20)
    assert imported.returncode == 0, imported.stderr
    assert list((root / "src/__pycache__").glob("cache_probe.*.pyc"))
    # The exclusion is directory based, shared by production producer/verifier.
    for name in ("src", "native", "tools", "tests"):
        cache = root / name / "__pycache__"
        cache.mkdir(exist_ok=True)
        (cache / "generated.py").write_text("# ignored cache content\n")
    outcome = verify(root, folder)
    assert outcome.returncode == 0, outcome.stderr
    after = make_receipt(root, tmp_path / "after_import")
    assert before["source_SHA256"] == after["source_SHA256"]
    assert before["qualification_inputs_SHA256"] == after["qualification_inputs_SHA256"]
    assert all("__pycache__" not in name for name in after["source_SHA256"])
    outcome = verify(root, tmp_path / "after_import")
    assert outcome.returncode == 0, outcome.stderr


@pytest.mark.parametrize("relative", [
    "src/cache_probe.py", "src/unrecognized.txt", "src/legacy.pyc", "native/kernel.cpp",
    "tests/additional.py", "tools/additional.py", "requirements/additional.txt",
    "benchmarks/native_profile_benchmark.py", "benchmarks/NATIVE_PROFILE_PROTOCOL.md",
    "MIGRATION_PLAN.md", "ISTRUZIONI_TRASFERIMENTO_GITHUB.md", "GATES_REPORT.md",
])
def test_noncache_change_is_rejected(isolated_repository, tmp_path, relative):
    root = isolated_repository
    folder = tmp_path / "receipt"
    make_receipt(root, folder)
    (root / relative).write_bytes(b"changed or additional non-cache input")
    outcome = verify(root, folder)
    assert outcome.returncode != 0
    assert "product source identity" in outcome.stderr or "qualification inputs" in outcome.stderr


def test_runner_stages_only_bound_root_and_benchmark_inputs(isolated_repository, tmp_path):
    root = isolated_repository
    (root / "benchmarks/unrelated_dataset.npz").write_bytes(b"not a build input")
    producer = load_tool(root, "qualify_platform")
    destination = tmp_path / "build_source"
    producer.stage_build_inputs(destination, root)
    actual = {p.relative_to(destination).as_posix(): sha(p)
              for p in destination.rglob("*") if p.is_file()}
    expected = {name: sha(root / name) for name in (
        "setup.py", "pyproject.toml", "README.md", "LICENSE", "MANIFEST.in",
        "CHANGELOG.md", "RELEASE_NOTES.md", "SECURITY.md", "CONTRIBUTING.md",
        "MIGRATION_PLAN.md", "ISTRUZIONI_TRASFERIMENTO_GITHUB.md", "GATES_REPORT.md",
        "benchmarks/native_profile_benchmark.py", "benchmarks/NATIVE_PROFILE_PROTOCOL.md")}
    assert actual == expected
    inputs = producer.qualification_inputs(root)
    assert {name: inputs[name] for name in expected} == expected
    assert "benchmarks/unrelated_dataset.npz" not in inputs


def test_receipt_cannot_add_ignored_cache_to_identity(isolated_repository, tmp_path):
    root = isolated_repository
    folder = tmp_path / "receipt"
    record = make_receipt(root, folder)
    cache = root / "src/__pycache__/unexpected.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"cache")
    record["source_SHA256"]["src/__pycache__/unexpected.pyc"] = sha(cache)
    seal(folder, record)
    outcome = verify(root, folder)
    assert outcome.returncode != 0
    assert "product source identity" in outcome.stderr
