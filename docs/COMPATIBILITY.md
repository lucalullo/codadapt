# Compatibility and evidence categories

The owner reports green native-complete.yml source-workflow runs on Linux x86-64,
Windows, macOS 15 Apple Silicon and macOS 15 Intel, all Python 3.13.15. The owner
also reports successful Kaggle three-task/persistence/explicit C++ checks from
commit 1637747ab0fa4996ca180d3220053bab36b014ec. The local candidate was corrected
without fetching that commit. Source reports and local reproductions are distinct.
See qualification/OWNER_REPORTED_313.json; no run log or artifact was fetched.

The earlier original Kaggle artifacts have separately acquired hash-bound proof:
1079 PASS/3 SKIP/4 XFAIL, 200 C++ calls and 35 exact arrays for the native wheel;
1029 PASS/53 SKIP/4 XFAIL for pure. These apply to the exact original artifact and
profile in qualification/KAGGLE_NATIVE_20261029.json, not new package hashes.

The current delivery's local results bind each newly built artifact separately.
Unavailable Linux/manylinux/macOS final consumers are HOLD. Metadata accepts
Python >=3.10,<3.16 but does not certify all combinations. Broad dependency ranges
are resolver constraints; qualification uses exact requirements profiles.

Automatic dispatch is unchanged. Linux/macOS/Windows 3.13 are not added to the
automatic native guard. C++ inference is explicitly selectable through the
version-specific private context. Training/encoding remain Python/NumPy.

The source serving contract and old-image acceptance rules are unchanged. No
arbitrary cross-Python/NumPy/pandas pickle portability is claimed. SKIP/XFAIL are
not counted as PASS. No wheel is declared manylinux without actual audit/repair
and consumer execution. See BUILD_DISTRIBUTIONS.md and QUALIFICATION.md.
