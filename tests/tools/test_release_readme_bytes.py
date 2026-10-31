"""Verify exact approved description bytes in real built distributions."""
from email import policy
from email.parser import BytesParser
import os
from pathlib import Path
import tarfile
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_real_distribution_preserves_approved_readme_bytes(kind):
    location = os.environ.get("CODADAPT_TEST_DIST")
    if not location:
        pytest.skip("Requires the actual built package pair from the qualification runner")
    packages = Path(location)
    approved = (ROOT / "README.md").read_bytes()
    paths = list(packages.glob("*.whl" if kind == "wheel" else "*.tar.gz"))
    assert paths, "Actual distribution required, not a synthetic metadata fixture"
    for path in paths:
        if kind == "wheel":
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
                member, = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
                payloads = [archive.read(member)]
        else:
            with tarfile.open(path, "r:gz") as archive:
                readme, = [m for m in archive.getmembers()
                           if m.isfile() and m.name.count("/") == 1 and m.name.endswith("/README.md")]
                assert archive.extractfile(readme).read() == approved
                payloads = [archive.extractfile(m).read() for m in archive.getmembers()
                            if m.isfile() and m.name.endswith("/PKG-INFO")]
                assert payloads
        for raw in payloads:
            metadata = BytesParser(policy=policy.default).parsebytes(raw)
            assert metadata["Name"] == "codadapt"
            assert metadata["Version"] == "2.1.0"
            assert metadata.get_payload(decode=True) == approved
