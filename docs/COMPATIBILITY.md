# Compatibility of CodAdapt 2.1.0

| Profile / exact artifact | Observed evidence | Scope/status |
|---|---|---|
| Kaggle Linux x86-64 / CPython 3.13.15 / glibc 2.39, original native wheel | 1079 PASS / 3 SKIP / 4 XFAIL; 200 C++ calls, 35 exact arrays; persistence and benchmark | PASS for that original host/wheel/pin set |
| Same host, original pure wheel | Separate clean consumer: 1029 PASS / 53 SKIP / 4 XFAIL | PASS for that original Python artifact/profile |
| Native manylinux wheel | No actual baseline build/repair and final consumer proof | HOLD; not provided as manylinux |
| New native Windows release distributions | Prior build/static checks do not establish execution of these bytes | Excluded from delivered qualified native artifacts |
| macOS Intel / Apple Silicon | No actual Mac execution | NOT TESTED; no qualified native wheel supplied |
| Historical Windows 3.10/3.12/3.14 source/runtime profiles | Earlier finite evidence is preserved with its identities | Historical scope only; not a new build/consumer PASS |

The native Linux wheel and kernel identities are in
[KAGGLE_NATIVE_20261029.json](../qualification/KAGGLE_NATIVE_20261029.json).
The kernel references GLIBC_2.34 and GLIBCXX_3.4.29; it was exercised on glibc 2.39.
This is not a manylinux certificate or a guarantee for all later glibc hosts.
See [MANYLINUX_RELEASE.md](MANYLINUX_RELEASE.md) for a real build/repair protocol.

Python metadata accepts >=3.10,<3.16; availability and execution of dependencies
must still be checked on each target. Older matrix/receipt files retained in
qualification/ are historical and do not supersede this declared scope.

Automatic dispatch is unchanged: native is eligible only on its exact historical
Windows CPython 3.12.10/dependency guard, if a valid module exists. Linux and other
profiles use Python by default. Advanced explicit native inference is documented
separately; no estimator parameter or serving identity migration is introduced.

SKIP and XFAIL remain separate from PASS. Four expected failures concern weighted
row-repetition invariance and mixed NumPy object matrices; use supported pandas
DataFrames for mixed data. Array-API tests not enabled are not claimed as passed.
