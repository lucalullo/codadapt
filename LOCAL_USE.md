# Use the proposed local candidate

Use the exact tested Windowsx64 Python3.14.10 pins in requirements/windows314.txt.
Install the matching proposed development wheel from the separately supplied
artifact folder into a new authorized venv. No compiler is needed for a wheel.
Use the pure wheel for Python-only inference. On314the automatic backend remains
Python even when a native wheel is installed. Private explicit-native contexts
are qualification tools, not a new public parameter.

From this source folder run:
`python examples/basic_usage.py --output qualification_runs/example`.
The3basic_*.py scripts give additional synthetic mixed-frame examples.
For complete tests, install requirements/qualification.txt and provide matching
dist/ or CODADAPT_TEST_DIST, then run `python -m pytest`.
The3.10optional EBM component and3.12fresh runtime remain environment-gated;
do not weaken Windows protections. See GATES_REPORT.md before interpreting PASS.

See docs/NATIVE_PROFILE_DECISION.md for the measured explicit-native path;
installing a native wheel on310/314 does not activate it automatically. The
current final artifact identities and new checks are in RAPPORTO_FINALE.md.
