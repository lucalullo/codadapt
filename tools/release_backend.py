"""Deterministic, allowlisted pure-Python PEP 517 build backend (stdlib only)."""
from pathlib import Path, PurePosixPath
from email.parser import BytesParser
import base64
import csv
import gzip
import hashlib
import io
import tarfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = "codadapt-2.2.0.dist-info"
NAME = "codadapt-2.2.0-py3-none-any.whl"
SDIST = "codadapt-2.2.0"


def source_names():
    names = (ROOT / "release/SOURCE_MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    if not names or len(names) != len(set(names)):
        raise ValueError("Empty or duplicate source manifest")
    for name in names:
        posix = PurePosixPath(name)
        if not name or posix.is_absolute() or ".." in posix.parts or "\\" in name or ":" in name or posix.as_posix() != name:
            raise ValueError(f"Invalid source member: {name!r}")
        path = ROOT / name
        if not path.resolve().is_relative_to(ROOT) or not path.is_file() or any(p.is_symlink() for p in (path, *path.parents) if p != ROOT and p.is_relative_to(ROOT)):
            raise ValueError(f"Missing or unsafe source member: {name!r}")
    return sorted(names)


def metadata_bytes():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    if project["name"] != "codadapt" or project["version"] != "2.2.0":
        raise ValueError("Metadata identity mismatch")
    headers = [("Metadata-Version", "2.4"), ("Name", project["name"]),
               ("Version", project["version"]), ("Summary", project["description"]),
               ("Author", ", ".join(a["name"] for a in project["authors"])),
               ("Keywords", ",".join(project["keywords"])),
               ("Requires-Python", project["requires-python"])]
    if "license" in project:
        headers.append(("License-Expression", project["license"]))
    for label, url in project["urls"].items():
        headers.append(("Project-URL", f"{label}, {url}"))
    for classifier in project["classifiers"]:
        headers.append(("Classifier", classifier))
    names = set(source_names())
    license_files = set()
    for pattern in project["license-files"]:
        paths = {p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern) if p.is_file()}
        if not paths or not paths <= names:
            raise ValueError(f"Missing or unlisted license files for {pattern}")
        license_files.update(paths)
    headers.extend(("License-File", name) for name in sorted(license_files))
    headers.extend(("Requires-Dist", requirement) for requirement in project["dependencies"])
    for extra, requirements in project["optional-dependencies"].items():
        headers.append(("Provides-Extra", extra))
        headers.extend(("Requires-Dist", f'{requirement}; extra == "{extra}"') for requirement in requirements)
    headers.append(("Description-Content-Type", "text/markdown; charset=UTF-8"))
    if any("\n" in v or "\r" in v for _, v in headers):
        raise ValueError("Invalid metadata header")
    return ("\n".join(f"{k}: {v}" for k,v in headers)+"\n\n").encode("utf-8") + (ROOT/project["readme"]).read_bytes()


def wheel_payload():
    names = source_names()
    payload = {}
    for name in names:
        if name.startswith("src/codadapt/"):
            if Path(name).suffix not in {".py", ".json"}:
                raise ValueError(f"Unexpected runtime member: {name}")
            payload[name.removeprefix("src/")] = (ROOT / name).read_bytes()
    payload[f"{DIST}/METADATA"] = metadata_bytes()
    payload[f"{DIST}/WHEEL"] = b"Wheel-Version: 1.0\nGenerator: codadapt-release-backend\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    payload[f"{DIST}/top_level.txt"] = b"codadapt\n"
    metadata = BytesParser().parsebytes(payload[f"{DIST}/METADATA"])
    for name in metadata.get_all("License-File", []):
        if name not in names:
            raise ValueError(f"Invalid license file: {name}")
        payload[f"{DIST}/licenses/{name}"] = (ROOT / name).read_bytes()
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    for name, data in sorted(payload.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        writer.writerow([name, "sha256=" + digest, len(data)])
    writer.writerow([f"{DIST}/RECORD", "", ""])
    payload[f"{DIST}/RECORD"] = stream.getvalue().encode()
    return payload


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    dest = Path(wheel_directory)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest / NAME, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(wheel_payload().items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    return NAME


def get_requires_for_build_wheel(config_settings=None):
    return []


def get_requires_for_build_sdist(config_settings=None):
    return []


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    for name, data in wheel_payload().items():
        if name.startswith(DIST + "/") and name != f"{DIST}/RECORD":
            path = Path(metadata_directory) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return DIST


def build_sdist(sdist_directory, config_settings=None):
    dest = Path(sdist_directory)
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / (SDIST + ".tar.gz")
    with target.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=9) as compressed, tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as archive:
        for name in sorted([*source_names(), "PKG-INFO"]):
            data = metadata_bytes() if name == "PKG-INFO" else (ROOT / name).read_bytes()
            info = tarfile.TarInfo(SDIST + "/" + name)
            info.size = len(data)
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    return target.name


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel-dir", required=True)
    args = parser.parse_args()
    print(build_wheel(args.wheel_dir))
