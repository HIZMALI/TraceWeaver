# Judge quick start

TraceWeaver is a read-only incident investigation console backed by real embedded Relate 1.0.0.
All distributed records are synthetic. No account, API key, Docker, hosted graph or model is needed.

## Public source checkout

Install existing prerequisites Python 3.11+ and Node 24+ first. Windows/Python 3.14 was verified
locally; check GITHUB_CI_REPORT.md for actual hosted Windows/Ubuntu Python 3.11 results.

```powershell
git clone https://github.com/HIZMALI/TraceWeaver.git
cd TraceWeaver
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock -e ".[dev]"
.\scripts\start-judge-demo.ps1 -Build
```

The source command builds its own frontend; ignored environments, assets and binary caches are
not provided by Git. Initial downloads require internet and are outside the 60-second tour.
After building, `.\scripts\check-judge-demo.ps1` verifies the published synthetic store read-only.
Open `http://127.0.0.1:8000/?incident=INC-001`. No seeding is needed and no user store is modified.

## Optional local offline export: about 60 seconds to explore after prerequisites

This session's local export is `.verification/sprint07/release-candidate` in the checkout.
It is local review material, absent from a public source clone and not an uploaded release.
An owner can create a new reviewed export with `scripts/build_judge_wheel.py` and
`scripts/stage_release.py` after building the frontend; never overwrite an existing bundle.
The runtime wheels in the historical Sprint 07 export were resolved
for **Windows x64 / Python 3.14**. Other Python/OS installations need compatible wheels; do not
interpret an ABI3 package listing as a tested platform. Existing Python must be installed first.
Network and Node are unnecessary for the exported folder's installation and server.

From that folder in PowerShell:

```powershell
.\RUN_JUDGE.ps1 -CheckOnly
.\RUN_JUDGE.ps1 -Port 8000
```

The launcher checks every exported artifact, creates a folder-local `.venv`, installs the included
runtime wheels offline, checks the intact bundle, then serves numeric loopback. Checksums establish
byte equality, not trusted authorship. It never seeds or repairs a store. A checksum, port or storage
error is a real error: stop and preserve the files. Ctrl+C stops the server.

Open `http://127.0.0.1:8000/?incident=INC-001`:

1. **0–15s:** read the synthetic/read-only/no-cause notices, two candidate pairs and four evidence.
2. **15–30s:** click **Explore the verified path**. Inspect Payment → Auth ← DEP-001 → CHG-001.
   “Verified” describes the stored path, not source truth. DEP-002 is a competing Payment candidate.
3. **30–45s:** select DEPLOYMENT_BEFORE_ONSET in the inspector; inspect GRAPH_PATH and TEMPORAL.
4. **45–60s:** choose CASE-INC → Observations: one conflict, two UNDETERMINED comparisons.
   Evidence CASE-E-NAIVE stays Unknown. Gaps disclose missing context.

For the actual offline tool trace, return to INC-001 → **Explore investigation steps** →
**Rehearse graph investigation**. Expect four executed native tools, 23 queries, eight admitted
claims and eleven citations, both AI flags false. Step 2 exposes reverse TARGETS traversal.
Refresh clears transient execution state. Optional AI is separate, opt-in and availability-dependent.

## Source checkout

Already installed prerequisites: Python 3.11+ and Node 24+; Windows/Python 3.14 was actually tested.
Initial package installation requires internet access and is not included in the exploration minute.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install -e .
.\scripts\start-judge-demo.ps1 -Build
```

Subsequent launch: `scripts/start-judge-demo.ps1`. Other free port: `-Port 8001`.
The source launcher uses PowerShell and npm; a non-editable wheel already contains the console.
Portable installed-wheel command (one line):

```text
python -m traceweaver.judge --bundle /path/to/intact/judge-demo --port 8000
```

## Why Relate matters

Relate is the actual **embedded, single-file persistent `.rl`** data engine, not an HTTP graph
service. Incident nodes AFFECTS Service; Service DEPENDS_ON Service; Deployment TARGETS Service
and INCLUDES_CHANGE Change; evidence has incident/service provenance relationships. Matching stored
direction makes candidate context and typed citations reproducible without treating connection as cause.

The read-only repository uses parameterized, bounded Cypher. A real INC-001 path is:

```cypher
MATCH (i:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
MATCH (s)-[:DEPENDS_ON]->(a:Service)<-[:TARGETS]-(d:Deployment)
MATCH (d)-[:INCLUDES_CHANGE]->(c:Change)
RETURN i.id, s.id, a.id, d.id, c.id LIMIT 10
```

Bind `incident_id` to `INC-001` in the project GraphStore, read-only; run it only against the intact
synthetic copy. It returns INC-001 / SVC-PAYMENT / SVC-AUTH / DEP-001 / CHG-001. The UI reproduces
the path via the starting action and exact direction list. There is no arbitrary-query HTTP endpoint.

Representative paths and returned context are partial. TRACEABLE is not VERIFIED. The conclusion
always remains NOT_ESTABLISHED and external verification NOT_PERFORMED. See the Sprint 07 report
in the checkout for tests, platform limits, video and owner-only publication decisions.
