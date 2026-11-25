"""Stage authenticated public historical folds; no fit, network or dataset redistribution."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = (HERE / "FOLD_MANIFEST_210.json").read_bytes()
    records = json.loads(manifest)["records"]
    expected = {r["file"]: r["SHA256"] for r in records}
    if len(expected) != 15 or any(Path(name).name != name or not name.endswith(".npz") for name in expected):
        raise ValueError("Unexpected historical manifest")
    output = args.output.resolve()
    # Do not write inside the tracked source directories or overwrite existing work.
    if output.exists():
        raise FileExistsError(output)
    if args.source.is_dir():
        root = args.source / "benchmarks/data"
        if not root.is_dir():
            root = args.source / "codadapt/benchmarks/data"
        payload = {name: (root / name).read_bytes() for name in expected}
        original = (root / "MANIFEST.json").read_bytes()
        original_runner = (root.parent / "reproduce_classification.py").read_bytes()
    else:
        with zipfile.ZipFile(args.source) as archive:
            candidates = [n for n in archive.namelist() if n in ("benchmarks/data/MANIFEST.json", "codadapt/benchmarks/data/MANIFEST.json")]
            if len(candidates) != 1:
                raise ValueError("Expected original 2.1.0 fold manifest")
            prefix = candidates[0].removesuffix("MANIFEST.json")
            original = archive.read(candidates[0])
            original_runner = archive.read(prefix.removesuffix("data/") + "reproduce_classification.py")
            payload = {name: archive.read(prefix + name) for name in expected}
    runner = (HERE / "reproduce_classification.py").read_bytes()
    if original != manifest or original_runner != runner:
        raise ValueError("Historical manifest or runner does not match frozen evidence")
    for name, data in payload.items():
        if hashlib.sha256(data).hexdigest() != expected[name]:
            raise ValueError(f"Historical fold SHA-256 mismatch: {name}")
    output.mkdir(parents=True, exist_ok=False)
    try:
        (output / "data").mkdir()
        for name, data in payload.items():
            (output / "data" / name).write_bytes(data)
        (output / "data/MANIFEST.json").write_bytes(manifest)
        (output / "reproduce_classification.py").write_bytes(runner)
        (output / "DATA_LICENSE.md").write_bytes((HERE / "DATA_LICENSE.md").read_bytes())
        (output / "run.py").write_text('''from importlib.metadata import version
import runpy
from pathlib import Path
if version("codadapt") != "2.1.0":
    raise SystemExit("Use a separate environment with CodAdapt 2.1.0 installed")
runpy.run_path(str(Path(__file__).with_name("reproduce_classification.py")), run_name="__main__")
''', encoding="utf-8")
    except Exception:
        shutil.rmtree(output)
        raise
    print(json.dumps({"status": "PASS_STAGING_ONLY", "verified_folds": len(payload), "output": str(output), "new_fits": 0}, indent=2))


if __name__ == "__main__":
    main()
