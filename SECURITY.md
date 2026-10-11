# Security Policy

The current supported experimental prerelease is CodAdapt 0.2.0rc2. Its Python requirement is
`>=3.10,<3.15`, with Python 3.10–3.14 in the qualified matrix. No support duration is promised.
Report suspected vulnerabilities privately to
the repository owner with the affected version, reproduction, impact, and suggested mitigation.
Do not open a public issue containing secrets or private data.

CodAdapt is not a security boundary. Treat external schemas and outputs as untrusted where
appropriate. Pickle and joblib can execute code while loading; load only trusted artifacts in
compatible environments. No remediation SLA is guaranteed for this experimental prerelease.
