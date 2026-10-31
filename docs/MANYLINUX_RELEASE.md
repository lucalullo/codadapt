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


## Exact interpreter/image alignment before a new release run

The owner reports that the prior attempt stopped because the pinned image had
CPython 3.13.18 while 3.13.15 was requested. This is a real version mismatch,
not a C++ defect or a manylinux qualification. Do not disable the patch check,
edit a wheel tag, or relabel that attempt PASS.

Before requesting `native-release-linux.yml`, an authorized Linux operator must
inspect the exact official image digest and its actual interpreter. Example
(replace the placeholders with the owner-approved digest and target ABI):

```text
docker run --rm quay.io/pypa/manylinux_2_28_x86_64@sha256:<approved-64-hex-digest> /opt/python/cp313-cp313/bin/python -I -B -c "import platform; print(platform.python_version()); print(platform.libc_ver())"
```

Only after recording that output, dispatch with that same digest and an exactly
matching `python` input. For a verified image reporting 3.13.18, explicitly choose
3.13.18 and qualify that profile; this does not prove 3.13.15 support. To require
3.13.15, obtain an authorized image whose actual interpreter is 3.13.15 instead.
Never infer a patch from the ABI directory `cp313-cp313` or a mutable image tag.
The workflow's default input is a proposal, not proof of image contents.

The existing worker must still enforce actual Linux x86-64, glibc 2.28,
AUDITWHEEL_PLAT, digest and exact Python equality, followed by audit/repair and
execution of the repaired wheel. Preserve the result ZIP even for a mismatch.
Owner-reported source workflow success cannot qualify new package hashes.

For macOS, use `native-complete.yml` independently on `macos-15` and
`macos-15-intel`, with the exact Python selected explicitly. Homebrew libomp
must be available to the LightGBM benchmark process. Each run must build and
install its final wheel, execute native calls/equality, persistence and suite,
and preserve hashes/receipts. A prepared workflow is not executed evidence.
