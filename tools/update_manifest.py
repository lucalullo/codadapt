"""Refresh source inventory hashes after intentional, reviewed edits.

Membership comes from the explicit source allowlist, never from a directory scan.
Updating checksums is not a qualification or distribution approval.
"""
from pathlib import Path
import hashlib
import json
from release_backend import source_names

ROOT = Path(__file__).resolve().parents[1]


def entry(name):
    data = (ROOT / name).read_bytes()
    return {"SHA256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def write_json(path, value):
    (ROOT / path).write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def refresh():
    excluded = {"release/MANIFEST.json", "release/SHA256SUMS.txt"}
    names = set(source_names())
    inventory = sorted(names - excluded)
    sbom_path = ROOT / "release/SBOM.json"
    sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
    sbom["source_files"] = [{"path": name, **entry(name)} for name in inventory if name != "release/SBOM.json"]
    write_json("release/SBOM.json", sbom)
    write_json("release/MANIFEST.json", {"scope": "Allowlisted source revision; manifest and digest exclude themselves", "files": {name: entry(name) for name in inventory}})
    (ROOT / "release/SHA256SUMS.txt").write_bytes((entry("release/MANIFEST.json")["SHA256"] + "  MANIFEST.json\n").encode())


if __name__ == "__main__":
    refresh()
