"""R3 Linux native build by default; explicit pure build remains available.

Build inclusion and automatic inference dispatch are separate contracts.
Compiler failures are reported, never silently converted to pure-wheel success.
"""
import os
import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.egg_info import egg_info
from setuptools.command.sdist import sdist


def _preserve_readme_bytes(metadata_path):
    """Keep setuptools headers and the approved README's exact newline bytes.

    Windows text-mode metadata writers otherwise translate LF to CRLF. Perform
    this before archive creation, so wheel RECORD is generated from final bytes.
    Reject any difference beyond newline translation in the generated body.
    """
    path = Path(metadata_path)
    data = path.read_bytes()
    # Byte values avoid setup-script escape rewriting by the pinned backend.
    crlf, lf = bytes((13, 10)), bytes((10,))
    for separator in (crlf * 2, lf * 2):
        if separator in data:
            headers, body = data.split(separator, 1)
            break
    else:
        raise ValueError("Generated package metadata has no description body")
    approved = Path(__file__).with_name("README.md").read_bytes()
    if body.replace(crlf, lf) != approved.replace(crlf, lf):
        raise ValueError("Generated description does not match README.md")
    path.write_bytes(headers + separator + approved)


class ExactReadmeEggInfo(egg_info):
    def run(self):
        super().run()
        _preserve_readme_bytes(Path(self.egg_info) / "PKG-INFO")


class ExactReadmeSdist(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, files)
        _preserve_readme_bytes(Path(base_dir) / "PKG-INFO")

extensions = []
commands = {"egg_info": ExactReadmeEggInfo, "sdist": ExactReadmeSdist}
requested = os.environ.get("CODADAPT_BUILD_NATIVE")
if requested not in (None, "0", "1"):
    raise ValueError("CODADAPT_BUILD_NATIVE must be 0 or 1")
native = (sys.platform.startswith("linux") if requested is None else requested == "1")
if native:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
    flags = ["/O2", "/fp:strict"] if sys.platform == "win32" else ["-O3", "-fno-fast-math", "-ffp-contract=off"]
    extensions = [Pybind11Extension("codadapt._native_kernel", ["native/memory_read.cpp"],
                                  cxx_std=17, extra_compile_args=flags)]
    commands["build_ext"] = build_ext
setup(ext_modules=extensions, cmdclass=commands)
