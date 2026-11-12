# Sprint 03 verified walkthrough

Verified locally on Windows x64 / CPython 3.14.0 / real relate-db 1.0.0. Default explanation is
offline and not AI-generated. The optional local model run below genuinely succeeded; it is
separate from controlled protocol tests. No existing database, judge artifact or source fixture
was written. Remote CI, Ubuntu and Python 3.11 remain UNVERIFIED.

## Setup and offline CLI

Use the existing project virtual environment, or install in a new one using the unchanged lock:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

These are setup instructions; actual independent verification used a separately created virtual
environment and a non-editable installed wheel, not a re-created user environment.

Actual executed CLI entry points against the existing synthetic judge file:

```powershell
python -m traceweaver explain --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver explain --incident CASE-INC --database ./examples/judge-demo/traceweaver-demo.rl
```

| Actual result | INC-001 | CASE-INC |
| --- | --- | --- |
| mode / AI selection | DETERMINISTIC / false | DETERMINISTIC / false |
| explanation status | PARTIAL_CONTEXT | PARTIAL_CONTEXT |
| returned candidate-target pairs | 2 | 6 |
| returned evidence | 4 | 11 |
| rendered validated claims / citations | 8 / 11 | 10 / 18 |
| structured conflicts / undetermined | 0 / 0 | 1 / 2 |
| causal conclusion | NOT_ESTABLISHED | NOT_ESTABLISHED |

Read the actual full [INC-001](examples/INC-001-explanation.json) and
[CASE-INC](examples/CASE-INC-explanation.json) canonical JSON examples. INC-001 includes both
DEP-001 → SVC-AUTH and DEP-002 → SVC-PAYMENT candidates; reverse TARGETS is explicit in ordered
proof paths. CASE-INC keeps invalid/missing metadata and uncertain comparisons visible. Source
prose/refs are withheld, never treated as instructions. No model or source network call occurs.

The status is intentionally partial because the source investigation has gaps. A successful
command does not mean that an incident is solved. A no-evidence case returns ABSTAINED.

## HTTP and CLI equality

Equivalent manual Windows commands after environment activation:

```powershell
$env:TRACEWEAVER_DATABASE = './examples/judge-demo/traceweaver-demo.rl'
python -m uvicorn traceweaver.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/incidents/INC-001/explanation'
Invoke-RestMethod 'http://127.0.0.1:8000/incidents/CASE-INC/explanation'
Invoke-RestMethod 'http://127.0.0.1:8000/incidents/INC-001/explanation?pre_minutes=60&post_minutes=5&max_candidates=2&max_evidence=4'
```

The observed smoke used actual Uvicorn subprocesses and native HTTP requests on ephemeral
127.0.0.1 ports outside the checkout, with the independently installed wheel. It did not use
TestClient as a substitute for live HTTP. Both default cases returned 200 and exactly matched
CLI/service examples; the nondefault request also matched CLI JSON. Unknown incident returned
404; fractional pre_minutes returned 422. A second real server pointing to a missing scratch
path returned safe 503 and did not create a file. Generic 500, writer lock, read-only/concurrent
behavior and strict errors were additionally exercised in actual-engine pytest tests.

HTTP is deterministic-only. Supplying mode=ollama does not enable a model. There is no write
route or model/provider query option. Keep Uvicorn on loopback; this is not a production auth layer.

## Genuine optional local model

Initial GET /api/tags found a running service and existing qwen3:8b. No installation or model
download was performed. This actual command succeeded, including from the installed wheel:

```powershell
python -m traceweaver explain --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl --mode ollama --model qwen3:8b
```

Observed: exit 0, mode_requested/executed OLLAMA, ai_generated_selection=true,
provider OLLAMA_LOCAL, model_id qwen3:8b, PARTIAL_CONTEXT, zero rejection codes.
The model-selected output validated **7 claims / 17 citations**, differed from the deterministic
8-claim selection/order, and retained the same investigation fingerprint and NOT_ESTABLISHED.
Only accepted claim IDs/facts and safe aggregate metadata were retained; no prompt/raw response.
See the report for the actual selected IDs. This is one inspected scenario, not AI accuracy.

Use an actual already-installed compatible local ID on another machine. Missing --model returns
MODEL_UNAVAILABLE / mode NONE / exit 12; malformed or invented selection returns
MODEL_OUTPUT_REJECTED / NONE / exit 13. No deterministic answer is silently labelled as AI.
No automatic pull, external source access, arbitrary host or cloud endpoint exists.

## Evaluation and regression reproduction

Use new filenames; these PowerShell commands reproduce the actual executed evaluations:

```powershell
$runDir = Join-Path $env:TEMP ('traceweaver-sprint03-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runDir | Out-Null
python -m traceweaver evaluate --suite ./evaluation/cases.json --output (Join-Path $runDir 'graph.json')
python -m traceweaver evaluate-explanations --suite ./evaluation/explanation_cases.json --output (Join-Path $runDir 'explanations.json')
python -m pytest -q
python -m ruff check .
python -m pip check
```

Actual results: old graph evaluation **20/20**; explanation evaluation **19/19**; pytest
**337 passed**, 0 failed/skipped. Both JSON/Markdown evaluations reproduced byte-identically
outside checkout from the installed wheel. Committed reports were not overwritten for reruns.
There are 231 generated/admitted/validated claims, 380 citations, 181/181 actual edge checks,
32/32 independently reviewed requirements, 133/133 rejected attacks, 10/10 mandatory warning
checks, 19/19 no-cause cautions and deterministic repeats, and 1/1 required abstention.

Metrics describe returned synthetic context, not root-cause accuracy/source truth. X12/X13 are
intentionally truncated and excluded from completeness claims; no whole-graph accuracy ratio
is calculated. A deliberately corrupted copied gold fails with CLI exit 14. Read the disclosed
[new-gold review correction](../evaluation/EXPLANATION_GOLD_REVIEW.md); Sprint 02 gold is unchanged.

## Verify preservation

```powershell
Get-FileHash ./data/traceweaver.rl -Algorithm SHA256
Get-FileHash ./examples/judge-demo/traceweaver-demo.rl -Algorithm SHA256
python -m traceweaver stats --database ./examples/judge-demo/traceweaver-demo.rl
```

Observed before/after hashes:

- data/traceweaver.rl: `3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3`; 73,728 bytes; 21/27.
- Judge .rl: `29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239`; 110,592 bytes; 51/67.

All existing fixtures, judge manifest, Sprint 02 evaluation/reports and legacy snapshots remained
unchanged. Only the exact added GET route was appended to the old OpenAPI route-set test.
