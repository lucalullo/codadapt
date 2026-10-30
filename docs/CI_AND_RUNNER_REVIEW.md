# Qualification environment flow

native-complete.yml is manual, read-only and never publishes. It activates MSVC
plus Windows SDK before Python launches the build; setuptools uses that active
environment via DISTUTILS_USE_SDK. It installs Homebrew libomp on both macOS CPU
profiles before LightGBM benchmarks and verifies the dylib. tools/build_environment.py
forwards an explicit compiler/SDK/loader allowlist to child processes while
dropping unrelated Python paths and account credentials. LightGBM import is a
separate pre-benchmark stage. These are build/tooling fixes, not predictive changes.

The diagnostic manylinux test allocates an output outside the tested source tree
without relaxing tools/manylinux_release.py's safety guard. Local launchers place
all work/TEMP/cache roots in the authorized laboratory; CI uses its runner space.

Owner-reported green source jobs are recorded separately from the new artifact
results. The current workflows require new actual runs to qualify final bytes.
Raw receipts, stage errors, SKIPs/XFAILs, wheel/kernel hashes and actual compiler,
ABI and dependency versions must be retained. See BUILD_DISTRIBUTIONS.md.
