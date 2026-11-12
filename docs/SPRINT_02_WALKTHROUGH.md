# Sprint 02 synthetic end-to-end walkthrough

All steps below were executed locally using real Relate 1.0.0, with a fresh OS temporary store.
No existing workspace store was seeded or migrated. Activate the project virtual environment
as shown in the root README. All input is synthetic. Local Windows execution is verified;
Python 3.11/Ubuntu and remote CI are unverified.

## 1. Validate bytes and dry-run syntax/domain admission

```powershell
$scratchDir = Join-Path $env:TEMP ('traceweaver-ingest-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $scratchDir | Out-Null
$store = Join-Path $scratchDir 'scratch.rl'
$expected = ((Get-Content ./fixtures/ingestion_example.sha256 -Raw) -split '\s+')[0]
python -m traceweaver verify-source --input ./fixtures/ingestion_example.json --expected-sha256 $expected
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database $store
```

Observed: MATCH, external_verification_status=NOT_PERFORMED. Dry-run: mode DRY_RUN,
committed=false, graph_counts=null, nodes_would_create=8, relationships_would_create=9.
The .rl file did not exist afterwards. An adjacent expected checksum is an illustration of
byte comparison, not authenticated independent origin. Syntax/domain checks precede writer open.

## 2. Apply three times

```powershell
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database $store --expected-sha256 $expected --apply
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database $store --expected-sha256 $expected --apply
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database $store --expected-sha256 $expected --apply
```

| Apply | Created nodes / edges | Already present nodes / edges | Actual totals |
| --- | --- | --- | --- |
| 1 | 8 / 9 | 0 / 0 | 8 / 9 |
| 2 | 0 / 0 | 8 / 9 | 8 / 9 |
| 3 | 0 / 0 | 8 / 9 | 8 / 9 |

Each was COMMITTED with one finite native transaction and closed writer. Actual counts came
from Cypher. No current-clock event field was inserted, and no unrelated data was reset.

## 3. Inspect graph-backed context

```powershell
python -m traceweaver investigate --incident ING-INC-001 --database $store
```

Actual path: `ING-INC-001 -AFFECTS-> ING-API -DEPENDS_ON-> ING-AUTH <-TARGETS- ING-DEP-001
-INCLUDES_CHANGE-> ING-CHG-001`. Both explicit observations ING-E-HEALTHY / ING-E-FAILED
belong to the incident and service and form one comparable structured conflict. No source is
declared true/false, and causal_conclusion remains NOT_ESTABLISHED. This uses the investigation
contract, not the stricter legacy context model for structured/real-data imports.

## 4. Known conflict: reject before writer, preserve SHA-256

```powershell
$changed = Get-Content ./fixtures/ingestion_example.json -Raw | ConvertFrom-Json
$changed.nodes[0].properties.summary = 'Synthetic conflicting revision'
$conflictInput = Join-Path $scratchDir 'conflict.json'
[IO.File]::WriteAllText($conflictInput, ($changed | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))
$before = (Get-FileHash -LiteralPath $store -Algorithm SHA256).Hash
python -m traceweaver ingest --input $conflictInput --database $store --apply
$after = (Get-FileHash -LiteralPath $store -Algorithm SHA256).Hash
$before -eq $after
```

Observed: exit **5**, INGEST_CONFLICT, no committed import, SHA-256 comparison **True**;
counts remained 8/9. Known conflicts are now rejected read-only before writer acquisition.
No assertion was weakened to hide Relate's observed physical-byte behavior.

A separate real-engine race test changes a matching user node after preflight but before writer
open, observes the early incident insert inside the transaction, then verifies the late conflict
rolls back inserted nodes/relationships/constraints while preserving that committed user change.
Relate may change .rl bytes when closing a rolled-back writer; logical rollback is verified,
physical byte rewind after writer open is not promised. No file backup is silently restored.

## 5. Wrong independent expected digest

```powershell
$wrong = '0' * 64
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database $store --expected-sha256 $wrong --apply
```

Observed: exit **6**, SOURCE_DIGEST_MISMATCH, no writer opened, store SHA-256 unchanged.
Integrity MATCH would prove byte equality only, never source truth. Omitting a digest returns
NOT_CHECKED. A digest embedded in the JSON is not an independent expected value.

## 6. Reproduce evaluation

```powershell
$report = Join-Path $scratchDir 'evaluation.json'
python -m traceweaver evaluate --suite ./evaluation/cases.json --output $report
```

Observed **20 passed / 0 failed** with a canonical JSON and readable .md report. Actual eligible
candidate retrieval was 53/53, evidence IDs 61/61, conflicting pairs 3/3. Two truncated scenarios
were excluded from affected retrieval denominators and still passed cap assertions. Temporal
labels 120/120, provenance labels 64/64, actual graph edges 432/432. These are synthetic rule/
path checks, not root-cause accuracy or an LLM benchmark. Existing reports require --overwrite.
See [evaluation methodology](EVALUATION_METHOD.md) and the committed reports under `reports/`.

## 7. Inspect the actual packaged judge .rl

```powershell
$manifest = Get-Content ./examples/judge-demo/MANIFEST.json -Raw | ConvertFrom-Json
python -m traceweaver verify-source --input ./examples/judge-demo/traceweaver-demo.rl --expected-sha256 $manifest.artifact_sha256
python -m traceweaver stats --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver context --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver investigate --incident CASE-INC --database ./examples/judge-demo/traceweaver-demo.rl
```

All commands succeeded read-only after writer closure: **51 nodes / 67 relationships**,
**110,592 bytes**, CASE-INC six candidates, eleven evidence, one conflict/two undetermined.
Actual artifact SHA-256:

```text
29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239
```

The default user store remained 21/27 with its original SHA-256. Only the deliberate synthetic
judge artifact is versioned. To rebuild, select a fresh directory as documented in
[the judge bundle README](../examples/judge-demo/README.md); binary hashes may differ across builds,
but the exact published logical graph is checked. No existing user store is a build scratchpad.
