# Local installation and source builds

This folder prepares the proposed 2.1.0 candidate for manual review. It is not
an approved new index release. Use an authorized local wheel or build from
source, and match OS, CPU architecture and CPython ABI exactly.

Create a new environment with `python -m venv .venv` and use its interpreter
for each command. Review [the gate report](../GATES_REPORT.md) before selecting
a platform or artifact. The requirements/windows310.txt, windows312.txt and
windows314.txt files describe exact dependency profiles; the current actually executed scope
is in COMPATIBILITY.md. A requirements file does not qualify a Python patch or OS. A permitted
metadata range is not a support matrix.

Install a matching wheel from the separate authorized artifact folder with
`python -m pip install <matching-local-wheel.whl>`. A prebuilt native wheel
needs no compiler, but still needs its ordinary C++ runtime and OS permission
to load. Pure wheels contain no native extension. Never weaken OS protections
or relocate blocked dependencies to obtain a PASS.

## Build from source

In a separate build environment install requirements/build.txt, then run
`python -m build --wheel --sdist --no-isolation`. The default produces a pure
wheel. For a native build, set the process-local `CODADAPT_BUILD_NATIVE=1` and
run the same command from an authorized compiler shell. C++17 MSVC and Windows
SDK, GCC/Clang, or Apple Clang are used on their respective systems. Native
wheels are ABI-specific, not abi3.

Generated dist/, wheel/sdist, caches and qualification outputs are not tracked
repository content. Build instructions for another OS do not demonstrate that
it has been tested. Build commands do not publish anything.

## Verify the installed candidate

Install requirements/qualification.txt in the consumer environment. Use the
installed package rather than source-path injection. Build local dist/ first
or set `CODADAPT_TEST_DIST` to a matching authorized artifact folder. Then run
`python -m pytest` from the repository root. It selects native, legacy and tools
suites, with the documented historical packaging-harness exclusion.

Run `python examples/basic_usage.py --output qualification_runs/example` for
the three tasks and persistence. The basic_classification.py,
basic_multiclass.py and basic_regression.py examples are self-contained synthetic
API demonstrations; they are not independent predictive benchmarks.

For a complete isolated build, consumer installation and evidence capture use
[QUALIFICATION.md](QUALIFICATION.md). It requires psutil in the authorized
interpreter that launches the bounded runner. If an OS policy blocks a required
library, retain the exact failure and use the preserved qualified candidate;
record the new version's gate as blocked until real authorized execution succeeds.
