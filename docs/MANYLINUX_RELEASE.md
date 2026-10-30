# Linux release build and exact-artifact qualification

State: prepared, NOT EXECUTED. The existing Kaggle wheel references GLIBC_2.34
and GLIBCXX_3.4.29; a manylinux_2_28 tag cannot be assigned just by renaming it.
Build the unchanged source on the chosen actual baseline instead.

Owner workflow .github/workflows/native-release-linux.yml uses only a real
ubuntu-24.04 runner and an approved digest of the official PyPA
quay.io/pypa/manylinux_2_28_x86_64 image. It mounts source read-only and a new
output directory writable, with no privileged mode, service setup, host policy
change or publication. The owner must verify image provenance/digest and
availability of the exact /opt/python/cp313-cp313 interpreter patch. Different
resolved Python patches are not silently substituted.

tools/manylinux_release.py creates isolated build tooling, builds sdist and a
native wheel from its restored contents, captures auditwheel 6.8.2 show/repair
logs, then tests the **repaired final wheel** in a clean consumer through the full
existing external chain. It preserves original/repaired hashes and returns one
ZIP on success or failure. Read-back import/calls/equality/persistence and actual
timings are distinct from auditwheel's symbol/library inspection. First qualify
on the real baseline, then run the exact repaired wheel on the intended
deployment/Kaggle host. A passed audit alone is not deployment qualification.

No Linux build was executed from this Windows PC: WSL permission and absent Docker
engine remain unchanged. The worker rejects a non-Linux/baseline invocation and
returns HOLD; this negative control is not a foreign-platform PASS. Missing
dependency wheels, compiler errors and failed checks remain real blockers.

Repair may bundle libraries: inspect LICENSE/dependency obligations and retain
auditwheel notices before admitting any wheel. Never use --plat to conceal newer
libc symbols. Changes in wheel or kernel SHA require new tests and, for the
proposed exact-binary auto guard, a separate approved profile/contract update.

Primary references checked 2026-10-29:
- https://pypi.org/project/auditwheel/
- https://cibuildwheel.pypa.io/en/stable/options/#manylinux-*-image-musllinux-*-image
- https://packaging.python.org/en/latest/guides/packaging-binary-extensions/
