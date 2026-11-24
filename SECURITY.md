# Security

Load only trusted model files and authenticate their digests independently. A restricted reconstruction whitelist or integrity check does not turn arbitrary pickle/joblib data into trusted input. Keep the original model/environment for rollback. Do not expose private model/data artifacts or secrets in reports. Use a private channel agreed with the project owner for vulnerabilities; do not publish protected evidence. This review is not a full security audit. See [persistence](docs/PERSISTENCE.md).
