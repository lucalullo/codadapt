"""Opt-in native wheel; the normal build uses Python inference."""
import os
import sys
from setuptools import setup

extensions = []
commands = {}
if os.environ.get("CODADAPT_BUILD_NATIVE") == "1":
    from pybind11.setup_helpers import Pybind11Extension, build_ext
    flags = ["/O2", "/fp:strict"] if sys.platform == "win32" else ["-O3", "-fno-fast-math", "-ffp-contract=off"]
    extensions = [Pybind11Extension("codadapt._native_kernel", ["native/memory_read.cpp"],
                                  cxx_std=17, extra_compile_args=flags)]
    commands = {"build_ext": build_ext}
setup(ext_modules=extensions, cmdclass=commands)
