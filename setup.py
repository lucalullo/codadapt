"""R3 Linux native build by default; explicit pure build remains available.

Build inclusion and automatic inference dispatch are separate contracts.
Compiler failures are reported, never silently converted to pure-wheel success.
"""
import os
import sys
from setuptools import setup

extensions = []
commands = {}
requested = os.environ.get("CODADAPT_BUILD_NATIVE")
if requested not in (None, "0", "1"):
    raise ValueError("CODADAPT_BUILD_NATIVE must be 0 or 1")
native = (sys.platform.startswith("linux") if requested is None else requested == "1")
if native:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
    flags = ["/O2", "/fp:strict"] if sys.platform == "win32" else ["-O3", "-fno-fast-math", "-ffp-contract=off"]
    extensions = [Pybind11Extension("codadapt._native_kernel", ["native/memory_read.cpp"],
                                  cxx_std=17, extra_compile_args=flags)]
    commands = {"build_ext": build_ext}
setup(ext_modules=extensions, cmdclass=commands)
