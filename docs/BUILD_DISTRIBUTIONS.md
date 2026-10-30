# Reproducible native distribution procedures

All targets retain version 2.1.0 and the frozen predictive/serving sources. New
artifact hashes need their own actual-target installation and execution evidence.
No workflow or cross-compilation alone qualifies another platform.

## Windows x64

Run native-complete.yml manually on windows-latest with the exact Python patch.
The MSVC development action exports compiler and SDK variables to subsequent
steps. The workflow requires cl, link, INCLUDE, LIB, LIBPATH and SDK/UCRT variables;
sets DISTUTILS_USE_SDK=1 and MSSdk=1; and the Python runner forwards these variables
to the build process. Merely discovering cl is not a build PASS. Compilation and
actual installed-extension execution remain mandatory. Do not change App Control.

## macOS 15 arm64 and x86-64

Use real macos-15 and macos-15-intel runners respectively. Install Homebrew libomp,
resolve brew --prefix libomp, verify lib/libomp.dylib, and propagate its actual
directory in DYLD_LIBRARY_PATH and DYLD_FALLBACK_LIBRARY_PATH to child consumers.
The runner imports LightGBM before the benchmark. This fixes a benchmark-library
prerequisite; it does not change CodAdapt's engine or add OpenMP to its C++ reader.
Record actual CPU, compiler, Python and wheel tags. Do not reuse the other CPU's
wheel. Audit/delocate only on real macOS where needed and test the resulting bytes.

## Linux manylinux

Use native-release-linux.yml on a real Linux runner with an owner-approved
digest of the official PyPA manylinux_2_28_x86_64 image and exact available Python
patch. tools/manylinux_release.py builds/restores sdist, builds the wheel, records
auditwheel show/repair and tests the repaired final artifact through the full
consumer chain. Qualify it on the baseline and then the intended deployment host.
An unavailable exact interpreter or failed baseline is HOLD, not permission to
retag a host wheel. The original Kaggle kernel references GLIBC_2.34 and cannot
simply be called manylinux_2_28. No manylinux build is claimed in this Windows run.

## Pure Python and sdist

Build in a new staging directory, using requirements/build.txt and the approved
README. Set CODADAPT_BUILD_NATIVE=0 before python -m build --wheel --sdist
--no-isolation. Request native with CODADAPT_BUILD_NATIVE=1 where appropriate.
Use a fixed SOURCE_DATE_EPOCH for reproducible archive timestamps. The optional
tools/reproducible_sdist.py normalizes metadata without changing file payloads.
Rebuild the wheel from the actual sdist, compare source/contract/README bytes,
and run python -m twine check --strict on exact files.

## Final qualification

Install exact wheels in new consumers; record pip check, actual import/kernel
path, binary/multiclass/regression, Python/C++ equality, persistence, full suite
and whole-process costs. Save errors, SKIPs, XFAILs and raw logs. Build PASS,
source-workflow green and installed-final-wheel PASS are separate states.
No publishing step or credential is included. Use docs/QUALIFICATION.md and the
owner's manual release checklist after the package hashes are approved.
