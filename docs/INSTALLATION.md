# Install CodAdapt 2.1.0

No upload is performed by this repository. Use an owner-approved local artifact
and compare its SHA-256 with the supplied distribution manifest before installing.

## Exact verified native Kaggle profile

Linux x86-64, CPython 3.13.15, glibc 2.39; NumPy 2.5.4, pandas 3.1.0,
SciPy 1.18.1, scikit-learn 1.9.1. Full pins are requirements/external-current.txt.
The wheel's original SHA-256 is
`f038373275a7de9f5ca7e5e4ff7ecaef591b0507b7b4d52e7ffc21b0ac414d65`.

In a new authorized environment on that profile:

```text
python -m venv .venv
```

Use `.venv/bin/python` on Linux/macOS or `.venv\Scripts\python.exe` on Windows
for subsequent commands. Windows/macOS cannot install the supplied Linux wheel.
Install dependencies from a single authorized index or offline wheelhouse first:

```text
python -m pip install --index-url https://pypi.org/simple -r requirements/external-current.txt
python -m pip install --no-deps /path/to/codadapt-2.1.0-cp313-cp313-linux_x86_64.whl
python -c "import codadapt; print(codadapt.__version__)"
```

A matching prebuilt native wheel does not require a compiler. Ordinary Linux
calls use Python; explicit native use and a fail-visible diagnostic are in
[native usage](NATIVE_PROFILE_DECISION.md). The wheel is not manylinux and must
not be retagged. Other hosts need actual tests before being advertised.

## Pure Python wheel

Install the owner-selected `codadapt-2.1.0-py3-none-any.whl` with `--no-deps`
after installing the declared dependencies. It contains no CodAdapt C++ binary
and uses Python fallback. The universal wheel tag is not proof of functional
qualification on all platforms. Several artifacts share a version and filename;
select the exact directory and manifest hash, not a wildcard.

## Building from the source repository or sdist

```text
python -m pip install --index-url https://pypi.org/simple -r requirements/build.txt
python -m build --wheel --sdist --no-isolation
```

Default Linux builds request C++17. To build purely in Python, set the environment
variable `CODADAPT_BUILD_NATIVE=0` before the command. To explicitly request C++
on any target, set `CODADAPT_BUILD_NATIVE=1`; an authorized compiler/SDK is needed.
POSIX example: `CODADAPT_BUILD_NATIVE=0 python -m build --wheel --sdist --no-isolation`.
PowerShell example: `$env:CODADAPT_BUILD_NATIVE='0'` followed by the build command.
These settings do not change automatic inference dispatch or saved models.

Build in a new staging copy so egg-info/build output does not alter the reviewed
source tree. No global configuration or OS protections should be changed.
macOS requires real Apple hosts. A denied DLL must be resolved by an authorized
administrator/host, not relocated or stripped of metadata to bypass policy.

Run examples and tests using [qualification](QUALIFICATION.md). A metadata check,
source smoke with existing dependencies, or import without dependencies is not
a full clean-consumer qualification. TestPyPI/PyPI steps belong to the owner and
are in [RELEASE_210.md](RELEASE_210.md).
