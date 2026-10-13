# Security Policy

The current prerelease candidate is CodAdapt 1.0.0rc1, not stable 1.0.0. Its Python requirement is
`>=3.10,<3.15`, with Python 3.10–3.14 in the qualified matrix. No support duration is promised.
Report suspected vulnerabilities privately to
the repository owner with the affected version, reproduction, impact, and suggested mitigation.
Do not open a public issue containing secrets or private data.

CodAdapt is not a security boundary. Treat external schemas and outputs as untrusted where
appropriate. Pickle and joblib can execute code while loading; load only trusted artifacts in
compatible environments. No remediation SLA is guaranteed for this experimental prerelease.

Native binary and multiclass training use explicit shared training functions and
fit-local caches. Training does not reconstruct or execute source text, and input
values, labels and categories are not interpreted as code. This does not change
the warning about loading untrusted pickle/joblib artifacts.

Native runtime does not launch subprocesses, execute user-supplied source, access
credentials or download models. Resource guards reject oversized controlled
allocations; they are not a security sandbox or hard process-RSS limit. Apply your
own input-size and process limits to untrusted workloads. Optional compilation
accepts fitted teacher objects, not an untrusted serialized interchange format.

Build and release qualification use read-only repository permissions and do not
publish. Audit archive contents and dependencies before installation/publication;
a local source review does not certify all transitive dependencies free of known
vulnerabilities. Report security issues with version/environment and a minimal
reproducer; never attach secrets or load an untrusted pickle to investigate it.
