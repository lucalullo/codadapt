# Qualification scope

## Local evidence

The 143 tests supplied with the source archive all pass on Windows 11 x64,
CPython 3.12.10 with the pinned CI dependency profile. Restoring applicable 2.1.0
unit tests expands this to **861 passes and four original strict expected
failures**, including optional EBM integration, sklearn checks, isolation of
training/validation data, weights, memory policies, multiclass, persistence and
serving. The original test assertions were retained.

The four expected failures are two pre-existing scope exceptions for each
estimator: arbitrary NumPy object arrays are unsupported, and weighted fitting
does not reproduce row repetition because quantiles and support counts are
unweighted. Both checks still execute with `xfail(strict=True)`; an unexpected
pass fails the suite. These are limitations, not successful checks or new waivers.

On the newer Windows dependency profile, the supplied suite has 141 passes and
two version-specific skips for the pandas 2.2.3 migration test. The source's
earlier review reported 143 Linux passes; that supplied history is separate from
fresh local results and from future GitHub runner results.

Tests use generated data, scikit-learn's bundled toy datasets and three small
authenticated synthetic snapshots. They exercise software fitting and loading;
they are not new predictive research or benchmark experiments. No protected
dataset is required. The old native-binary and retired build-tool tests do not
qualify this pure-Python backend. Its source allowlist, archive contents,
metadata, licenses, RECORD, deterministic build, rebuild from sdist and installed
wheel are checked separately by the release tools.

## Historical performance boundaries

Archived-model prediction parity and timing/compression results apply to the
models, host and profiles originally measured. They are not automatically fresh
timings of this snapshot-reader revision. The default learner's core, training,
encoder, classifier, regressor and multiclass modules match the authenticated
published 2.1.0 implementation at the syntax-tree level.

The 14-origin competitive benchmark includes every recorded outcome. It is
development evidence, not independent confirmation. C60 is not qualified and
independent Pareto is not certified. Standalone serving/trace historical probes
do not qualify an attachment that is absent from the distributions.

## Hosted checks still required

All seven workflows validate only. Local `actionlint` and the workflow privilege
check do not execute GitHub-hosted jobs. Before publication, require successful
source, package, dependency, strict Twine and installed-wheel test jobs on the
declared Ubuntu/Windows Python matrix. Qualify macOS separately before claiming
it. No workflow uploads to PyPI, TestPyPI or a release registry.

See [release verification](../release/README.md), [compatibility](../docs/COMPATIBILITY.md)
and [status](../release/STATUS.json). Publication remains a separate owner action.
