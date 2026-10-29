"""Prepare an UNQUALIFIED version copy; never edit the source tree or publish.

No product module is imported or executed. Existing artifacts/receipts are not
carried into the new candidate as if they qualified the new producer contract.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import shutil

FORMAT = "INTEGRATED_NATIVE_SERVING_ENVELOPE_4_PREVIEW"
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:(?:a|b|rc)(?:0|[1-9][0-9]*))?\Z")
EXCLUDED_DIRS = {".git", "dist", "qualification", "qualification_runs", "benchmark_runs",
                 "build", "__pycache__", ".pytest_cache", ".ruff_cache"}
EXCLUDED_FILES = {"MANIFEST_SHA256.json", "FILE_COMPARISON.json", "VERSION_PREPARATION.json"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_version(root):
    tree = ast.parse((root / "src/codadapt/_version.py").read_text(encoding="utf-8"))
    matches = [ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)]
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise ValueError("Expected one literal __version__")
    return matches[0]


def project_version(root):
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[project\]\s*\n(?P<body>.*?)(?=^\[|\Z)", text, re.M | re.S)
    if section is None:
        raise ValueError("Missing [project] section")
    matches = list(re.finditer(r'^version[ \t]*=[ \t]*"([^"]+)"[ \t]*$', section["body"], re.M))
    if len(matches) != 1:
        raise ValueError("Expected one literal project version")
    return matches[0].group(1)


def sources(root):
    package = root / "src/codadapt"
    native = {"codadapt/" + path.relative_to(package).as_posix(): sha(path)
              for path in sorted(package.rglob("*.py"))}
    serving = {path.name: sha(path) for path in sorted((package / "serving").glob("*.py"))}
    if not native or not serving:
        raise ValueError("Incomplete product sources")
    combined = hashlib.sha256(json.dumps(native, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return native, serving, combined


def validate(root):
    root = Path(root).resolve()
    selected_files(root)  # Reject linked entries before reading product source.
    version = package_version(root)
    if project_version(root) != version:
        raise ValueError("Project/package version mismatch")
    path = root / "src/codadapt/serving/source_contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    native, serving, combined = sources(root)
    if contract.get("format") != FORMAT:
        raise ValueError("Unsupported source-contract format")
    if contract.get("native_version") != version:
        raise ValueError("Version/source-contract mismatch")
    if contract.get("native_sources") != native or contract.get("serving_sources") != serving:
        raise ValueError("Source fingerprint mismatch")
    if contract.get("native_source_sha256") != combined:
        raise ValueError("Combined source fingerprint mismatch")
    return dict(version=version, contract_SHA256=sha(path), source_files=len(native), native_source_sha256=combined)


def selected_files(source):
    selected = []
    def visit(folder):
        for path in sorted(folder.iterdir()):
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ValueError("Linked source entries are not allowed")
            if path.is_dir():
                if path.name not in EXCLUDED_DIRS and not path.name.startswith((".venv", ".local_")) and not path.name.endswith(".egg-info"):
                    visit(path)
            elif path.is_file() and path.name not in EXCLUDED_FILES and path.suffix not in {".pyc", ".pyd", ".so", ".dll", ".pdb", ".obj"}:
                selected.append(path)
    visit(source)
    return selected


def references(root):
    """Inventory remaining historical/proposed version references for review."""
    output = []
    expression = re.compile(r"\b\d+\.\d+\.\d+(?:(?:a|b|rc|\.dev)\d+)?(?:\+[A-Za-z0-9.]+)?\b")
    for path in selected_files(root):
        if path.suffix not in {".md", ".py", ".toml", ".json", ".txt", ".yml"}:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            versions = expression.findall(line)
            if versions:
                output.append(dict(path=path.relative_to(root).as_posix(), line=number, values=versions))
    return output


def prepare(source, destination, new_version):
    source = Path(source).resolve()
    destination_input = Path(destination)
    destination = destination_input.resolve()
    if not VERSION.fullmatch(new_version) or new_version == "2.0.0":
        raise ValueError("Use a canonical new X.Y.Z or prerelease version; published 2.0.0 is forbidden")
    if destination.exists() or destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Destination must be new and non-overlapping")
    current = validate(source)
    if new_version == current["version"]:
        raise ValueError("New version must differ")
    files = selected_files(source)
    before = {path.relative_to(source).as_posix(): sha(path) for path in files}
    destination.mkdir(parents=True, exist_ok=False)
    for path in files:
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    path = destination / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    section = re.search(r"^\[project\]\s*\n(?P<body>.*?)(?=^\[|\Z)", text, re.M | re.S)
    body = re.sub(r'^version[ \t]*=[ \t]*"[^"]+"[ \t]*$', f'version = "{new_version}"', section["body"], count=1, flags=re.M)
    text = text[:section.start("body")] + body + text[section.end("body"):]
    path.write_bytes(text.encode("utf-8"))
    (destination / "src/codadapt/_version.py").write_bytes(f'__version__ = "{new_version}"\n'.encode())
    contract_path = destination / "src/codadapt/serving/source_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    native, serving, combined = sources(destination)
    contract.update(native_version=new_version, native_sources=native,
                    serving_sources=serving, native_source_sha256=combined, public_release=False)
    contract_path.write_bytes((json.dumps(contract, indent=2, ensure_ascii=False) + "\n").encode())
    new = validate(destination)
    assert {path.relative_to(source).as_posix(): sha(path) for path in files} == before
    changed = [rel for rel, digest in before.items() if sha(destination / rel) != digest]
    expected = {"pyproject.toml", "src/codadapt/_version.py", "src/codadapt/serving/source_contract.json"}
    if set(changed) != expected:
        raise ValueError("Unexpected package change")
    report = dict(schema=1, status="UNQUALIFIED_VERSION_COPY", RELEASE="HOLD", public_release=False,
                  before=current, after=new, changed_files=sorted(changed), source_unchanged=True,
                  copied_file_hashes=before, excluded_distribution_and_qualification_evidence=True,
                  old_serving_images_readable_by_new_contract=False,
                  compatibility="Preserve old matching runtime; no migration or cross-contract loading promised",
                  remaining_reference_inventory=references(destination),
                  required_before_promotion=["Review historical/current version references without blind replacement",
                    "Approve public version explicitly", "Build native/pure wheels and sdist", "Verify exact metadata/contract/payload identities",
                    "Clean consumer install, API, three tasks, persistence/export/fallback", "Run complete standard suite and applicable platform gates",
                    "Compare frozen predictions and retain prior runtime for old serving images", "Reissue manifests, benchmark scope and manual handoff report"])
    (destination / "VERSION_PREPARATION.json").write_bytes((json.dumps(report, indent=2) + "\n").encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--new-version")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if args.destination or args.new_version:
            parser.error("--check does not accept destination/version")
        print(json.dumps(validate(args.source), indent=2))
    else:
        if args.destination is None or args.new_version is None:
            parser.error("New destination and version are both required")
        report = prepare(args.source, args.destination, args.new_version)
        print(json.dumps({key: report[key] for key in ("status", "RELEASE", "before", "after", "changed_files")}, indent=2))


if __name__ == "__main__":
    main()
