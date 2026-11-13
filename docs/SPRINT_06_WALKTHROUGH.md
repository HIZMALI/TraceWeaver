# Sprint 06 local walkthrough

Tested: Windows 11 x64, Python 3.14.0, Relate 1.0.0, Node 24.13.1 for frontend build,
Chromium 158.0.8127.18. Python 3.11+ is declared; other runtimes/platforms remain unverified.
No Docker, Relate CLI, API key, paid service or model is required for the primary demo.

## Source setup and one-command startup

From a checkout with Python and Node already installed, in PowerShell:

```powershell
Set-Location D:\Projects\TraceWeaver
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.lock
.\.venv\Scripts\python -m pip install --no-deps -e .
.\scripts\start-judge-demo.ps1 -Build
```

For an already prepared checkout, the last line is the one-command launch. It builds static
assets and opens the existing verified synthetic judge store read-only. It does not seed, reset,
migrate or replace any database. Visit `http://127.0.0.1:8000/?incident=INC-001`. Stop with Ctrl+C.
Subsequent launches can omit `-Build`; Node and Ollama are then unnecessary for the server.
Do not point a public listener/proxy at this unauthenticated single-user loopback console.

Use `scripts/check-judge-demo.ps1` or the following read-only check before recording:

```powershell
.\.venv\Scripts\python -m traceweaver.judge --bundle examples/judge-demo --check
```

Expected native counts are 51 nodes / 67 edges; INC-001 returns 2 candidate/target pairs and
4 evidence; CASE-INC returns 6 pairs / 11 evidence under default options. All are synthetic.

## Primary offline route

Select DEP-001 in “Why this graph matters”, inspect Payment → Auth ← DEP-001 and CHG-001,
then click “Explore investigation steps”. Default is offline and not AI-generated. Click
“Rehearse graph investigation”. The same genuine read-only native tools run in a fixed plan.
Click step 2 to focus its actual path/inspector. Expand admitted claim citations and choose a
statement. Tool execution is distinct from both the existing explanation and local claim selection.

Repeatable CLI, without changing any old command:

```powershell
.\.venv\Scripts\python -m traceweaver.agent_cli --database examples/judge-demo/traceweaver-demo.rl --incident INC-001 --intent TRACE_DEPENDENCY_PATH --rehearse
.\.venv\Scripts\python -m traceweaver.agent_cli --database examples/judge-demo/traceweaver-demo.rl --incident INC-001 --intent TRACE_DEPENDENCY_PATH --rehearse --canonical
```

The canonical projection excludes measured elapsed durations and its own digest, preserving
actual evidence timestamps. CLI exits 0 for completed/partial/abstained bounded review, 14 for
failed agent operations, 2 for invalid arguments. It never creates a missing database.

## Optional actual local model

Only if the owner already has a running eligible installed model: click “Agent investigation
(local)”, choose an actual listed model, confirm and run. No model is preselected or pulled.
The fixed provider is `127.0.0.1:11434`. Runtime evidence is intermittent: qwen3:8b selected a real
trace_deployment in this session, but its final ID proposal failed schema admission. Later service
checks refused connection. A complete accepted live AI result is BLOCKED, not promised.

```powershell
.\.venv\Scripts\python -m traceweaver.agent_cli --database examples/judge-demo/traceweaver-demo.rl --incident INC-001 --intent TRACE_DEPENDENCY_PATH --model qwen3:8b --confirm-local
```

No free-text prompt, arbitrary Cypher, remote model endpoint or GET inference switch exists.
Cancellation stops the client wait; native/daemon work can continue until finite server budgets.
Only one local action per server is allowed at a time. A changed source requires refresh.

## Fresh wheel, without Node on the server

After building the frontend, choose a new output directory:

```powershell
.\.venv\Scripts\python scripts/build_judge_wheel.py --output .verification/sprint06/owner-wheel
```

Install that wheel non-editably into a fresh environment outside the checkout using the lock as
constraints. Copy the intact `examples/judge-demo` directory to that environment and run
`python -m traceweaver.judge --bundle <copied-directory>`. The wheel contains assets/notices and
fixtures, no .rl file. The judge bundle must remain separate and manifest-verified.
The independently installed Sprint 06 wheel/server/browser gate passed; see the report for hash.

## Verification commands

```powershell
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m pip check
npm --prefix web run typecheck
npm --prefix web run lint
npm --prefix web test
npm --prefix web run build
npm --prefix web run test:e2e
.\.venv\Scripts\python -m traceweaver.agent_evaluation --suite evaluation/sprint06_agent_cases.json --output .verification/sprint06/owner-agent-evaluation.json
```

Choose new report names; existing output requires explicit overwrite. The browser wrapper sends
historical screenshot writes into an owned ignored directory and tests current source. Sprint 06
browser tests deliberately recapture only the new `docs/screenshots/sprint06` files.
