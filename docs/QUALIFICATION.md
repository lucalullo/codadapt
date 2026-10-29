# Reproducible qualification on a real target machine

Use an authorized Windows, Linux or real macOS host. An emulator or cross-build
alone does not qualify another OS. Install a C++17 compiler only through the
owner's normal authorized process. Do not change security policies.

First install psutil==7.2.2 in the authorized interpreter that launches the runner
(from official PyPI or an authorized offline wheelhouse). This is separate from
the clean consumers. From this folder, using that target CPython interpreter:
`python tools/qualify_platform.py --run-id host_python_native --backend native`
Then a separate pure run:
`python tools/qualify_platform.py --run-id host_python_pure --backend pure`.
Windows native builds require an authorized x64 MSVC development shell.
Optional `--wheelhouse /authorized/wheels` makes installs offline; it must
contain all pinned runtime/build/test wheels for that OS/ABI. Otherwise only
official PyPI is used, without credentials or user package configuration.
Both commands create new isolated build and consumer environments, capture
logs, compile the sdist/wheel, run three-task/persistence/determinism/engine
probes and the preserved suite. Existing run directories are never overwritten.

Outputs are under qualification_runs/<run-id>. Keep RESULT.json, all logs,
install-report.json, junit.xml, probe/RESULT.json, dist and RECEIPT_MANIFEST.json.
`python tools/verify_qualification_receipt.py qualification_runs/<run-id>`
verifies source/runner identity and recorded hashes without executing models
or commands from a receipt. This verifies consistency, not authenticity of an
unknown sender or automatic platform promotion. Review the actual host,
failures/skips, numerical equality, memory and timing results before promotion.

A PASS requires zero unexplained failures, declared expected failures/skips,
clean consumer installation and matching artifact/source hashes. Require exact
Python/native outputs within a runtime on the finite corpus. Record cross-OS
differences separately. The native median batch2048 performance guard is
<=1.10xPython on each engineering task; this does not replace independent
predictive evidence. Whole-process memory is not model-only RAM.

The old legacy packaging test uses host-path injection and is retained but
excluded from the standard command. It is not counted as PASS. This runner's
genuinely clean consumer install and end-to-end probe replace that harness.
No test failure is silently converted into a product PASS.

CI is provided as a manually triggered proposed matrix and has NOT been run
on GitHub. Its existence does not qualify Linux/macOS or any new runtime.

The default `python -m pytest` command selects native,legacy,tools. Build local
dist/ before artifact tests, or provide CODADAPT_TEST_DIST. No missing artifact
is silently declared PASS. The preserved path-injection packaging module is
explicitly excluded in pyproject; new distribution-content tests and genuine
clean consumers replace it. Historical XFAILs remain explicit.

Schema2 binds tools,tests,pins and build configuration as well as source identity.
The runner records 300second stage,1800second total and1.5GiB sampled owned-tree
budgets. It cleans recorded PID/birth-matched children. Performance HOLD does not
become automatic platform promotion. See CI_AND_RUNNER_REVIEW.md.

The final 2.1.0 wheels have been installed and executed in genuinely fresh
Windows x64 / CPython 3.14.10 and 3.10.22 native and pure consumers. The final
targeted regressions are recorded in [RAPPORTO_FINALE.md](../RAPPORTO_FINALE.md).
The earlier actual 2.1.0 full native suite on 3.14 passed 1012 tests, with
3 skips and 4 historical XFAILs; it is reused only for unchanged product code.
The full 3.10 optional profile still has 12 recorded EBM DLL policy errors,
while its independent core checks pass. The pandas prerequisite denial applies
to the fresh 3.12 runtime, not to every new wheel. Linux/macOS remain untested.
No previous run is relabelled as a newly executed final-artifact test.
