# Source and distribution layout

src/codadapt contains the Python API/training/encoding and serving runtime.
native/memory_read.cpp is the qualified strict-floating-point C++ inference kernel.
tests/native, tests/legacy and tests/tools are all selected by default pytest.
examples provide small synthetic binary/multiclass/regression and mixed-frame use.
benchmarks contain current fixed results and explicitly labeled historical data.

Generated wheel/sdist, build caches and qualification runs are excluded from
tracked source. Development artifacts remain available separately with hashes.
Build local dist/ before artifact tests or set CODADAPT_TEST_DIST to a matching
authorized artifact directory. No distribution is an approved release.
