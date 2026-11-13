# Judge quick start

TraceWeaver reads the included synthetic Relate graph without seeding or changing it.
The default explanation and tool rehearsal are deterministic and offline. No model, account,
API key, Docker or graph server is needed.

## Install and start

Install Python 3.11+, Node 24+ and Git first. Initial dependency downloads require internet.
The exploration below takes about two minutes **after** setup; installation time is separate.

```powershell
git clone https://github.com/HIZMALI/TraceWeaver.git
cd TraceWeaver
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock -e ".[dev]"
.\scripts\start-judge-demo.ps1 -Build
```

Open **http://127.0.0.1:8000/?incident=INC-001**. Stop with Ctrl+C.
Subsequent launch: `.\scripts\start-judge-demo.ps1`; another free port: `-Port 8001`.
The [root README](../README.md#quick-start) has the Linux command. Windows/Ubuntu Python 3.11
tests and the Ubuntu installed-wheel/browser flow run in [CI](https://github.com/HIZMALI/TraceWeaver/actions/workflows/ci.yml);
the PowerShell launcher was also exercised locally on Windows/Python 3.14.

After building, verify the intact bundle read-only:

```powershell
.\scripts\check-judge-demo.ps1
```

Expect 51 nodes / 67 relationships and two inspected incidents. A missing, corrupt or locked
bundle is an error; preserve it rather than reseeding or repairing. See [the manifest](../examples/judge-demo/MANIFEST.json)
and [bundle inspection guide](../examples/judge-demo/README.md).

## Two-minute route

1. **INC-001:** read synthetic/read-only notices, two candidate pairs and four evidence records.
2. Click **Explore the verified path**: Payment → Auth ← DEP-001 → CHG-001. TARGETS is stored
   deployment-to-service even though this path traverses it backwards. Compare competing DEP-002.
3. Select **DEPLOYMENT_BEFORE_ONSET** and inspect GRAPH_PATH and TEMPORAL citations.
   Precedence does not establish a cause.
4. **CASE-INC → Observations:** inspect one conflict and two UNDETERMINED comparisons.
   CASE-E-NAIVE remains unknown; **Gaps** exposes missing context.
5. Return to **INC-001 → Explore investigation steps → Rehearse graph investigation**.
   Expect four executed native tools, 23 queries, eight claims and eleven citations; both AI flags
   are false. Step 2 exposes reverse TARGETS traversal. Refresh clears transient execution state.

Optional AI actions require an installed local model and explicit confirmation. Historical
qwen3:8b source-service tool use succeeded; dependable current live-browser completion is
unverified. Model availability/latency failures do not make the offline route an AI run.

## Actual Relate proof

This parameterized Cypher matches the starting path in the intact judge store:

```cypher
MATCH (i:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
MATCH (s)-[:DEPENDS_ON]->(a:Service)<-[:TARGETS]-(d:Deployment)
MATCH (d)-[:INCLUDES_CHANGE]->(c:Change)
RETURN i.id, s.id, a.id, d.id, c.id LIMIT 10
```

Bind incident_id to INC-001 through the read-only GraphStore. It returns INC-001 / SVC-PAYMENT /
SVC-AUTH / DEP-001 / CHG-001. The UI shows the same stored direction; there is no arbitrary-query
HTTP endpoint. [Architecture](ARCHITECTURE.md) and [agent contract](AGENT_TOOL_CONTRACT.md) describe
native query execution and proof admission.

Representative paths and capped results are partial. TRACEABLE and matching digests do not
authenticate source truth. Causal conclusion remains NOT_ESTABLISHED; external verification
remains NOT_PERFORMED. The API is unauthenticated and must stay on numeric loopback.

For an independently installed wheel or compatible offline export, use [packaging](PACKAGING.md).
No prebuilt export, models or video are included in the source clone.
