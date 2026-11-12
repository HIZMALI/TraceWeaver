# TraceWeaver synthetic judge bundle

**Synthetic demo data only. No real company, production incident, private source, or proven
root cause.** This persistent Relate 1.0.0 store is independent of the ignored application store.

Included: [traceweaver-demo.rl](traceweaver-demo.rl) and [MANIFEST.json](MANIFEST.json).
Actual Windows build: **51 nodes / 67 directed relationships**, **110,592 bytes**.

```text
SHA-256: 29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239
```

The manifest binds exact file bytes and published fixture hashes. A matching hash detects byte
differences; it does not establish factual truth or independent source authenticity.

## Two-minute inspection

Install in a virtual environment using the root README, then:

```powershell
$manifest = Get-Content ./examples/judge-demo/MANIFEST.json -Raw | ConvertFrom-Json
python -m traceweaver verify-source --input ./examples/judge-demo/traceweaver-demo.rl --expected-sha256 $manifest.artifact_sha256
python -m traceweaver stats --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver context --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver investigate --incident CASE-INC --database ./examples/judge-demo/traceweaver-demo.rl
```

All commands are read-only. INC-001 exposes the actual Payment API → Auth → deployment/change
path plus a competing direct deployment. CASE-INC has six candidates, eleven evidence records,
one comparable HEALTHY/FAILED conflict and two DEGRADED-related UNDETERMINED pairs. AFTER is
excluded only as a preceding trigger. Invalid/missing metadata remains visible. Causal conclusion
is always NOT_ESTABLISHED. Every shown dependency/path comes from real Cypher over this file.

## Reconstruction in a fresh directory

```powershell
$bundle = Join-Path $env:TEMP ('traceweaver-judge-' + [guid]::NewGuid().ToString('N'))
python -m traceweaver build-judge-demo --output-dir $bundle
```

The builder imports only the original Sprint 00 and explicit Sprint 01 synthetic fixtures into
a fresh temporary store. It closes writers, verifies exact logical contents and actual read-only
stats/context/investigate, then hashes and publishes the file and manifest. It checks every node/
edge demo marker, demo-only source references, credential/private-path patterns, and raw private
prefixes. These are limited checks, not a perfect secrets audit.

Existing outputs are refused. --force is allowed only for an intact recognized generated bundle
whose digest and exact graph still match the published synthetic fixtures; it cannot overwrite
a user store or a bundle containing independent changes. Use a quiescent, trusted local output
directory; this is not an adversarial concurrent-filesystem sandbox. Publication of two files
is not a cross-file atomic transaction; inspect/rebuild into a fresh directory after interruption.
README/other files in the output directory are never rewritten by the builder.

Logical graph equality is the reconstruction guarantee. Native binary bytes/hashes may vary by
build or platform, so always use the newly generated manifest. Local Windows inspection passed;
Linux/Python 3.11 runtime verification and remote CI remain UNVERIFIED. Only this exact generated
.rl has a Git ignore exception; user runtime databases remain ignored.
