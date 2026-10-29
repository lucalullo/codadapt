# Test inputs
tests/data contains only the frozen synthetic numeric engineering arrays
(three tasks, 16,384 training rows and 2,048 query rows, 16 features).
Runtime-specific model fixtures are rebuilt in pytest temporary directories.
They test batching, copy/override semantics and persistence, not predictive
generalization. No protected scientific TEST, private model bank or original
research-memory file is distributed here.
