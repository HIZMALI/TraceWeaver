# Sprint 00 Report — TraceWeaver

Verification date: **2026-11-12** (Europe/Istanbul).

Overall status: **PASS for the Sprint 00 acceptance criteria**. Optional Codex CLI skill
installation is **BLOCKED** on this Windows environment; remote GitHub Actions execution
is **BLOCKED / not run**, and neither is represented as a successful verification.

## A. Environment

| Item | Observed value |
| --- | --- |
| Operating system | Windows 11, build 10.0.26200, x64 / AMD64 |
| Python | CPython 3.14.0, existing discoverable interpreter |
| Virtual environments | Project `.venv`; independent clean `.venv-verify` |
| Relate Python distribution | `relate-db==1.0.0` |
| Python import | `import relate` succeeds |
| Relate CLI | `Relate v1.0.0`, official Windows amd64 release |
| Git | 2.51.0.windows.2; repository initialized on `main` |
| FastAPI / Starlette | 0.162.5 / 1.10.0 |
| Pydantic / Uvicorn | 2.14.3 / 0.54.0 |
| pytest / Ruff | 9.2.0 / 0.17.4 |
| Test HTTP client | httpx2 2.16.0 |
| pip | 25.2 |

Python 3.11/3.12 were preferred but not discoverable through the available Python commands;
`py` was unavailable. The existing supported interpreter installed the official
`cp39-abi3-win_amd64` wheel and passed actual engine tests, so no new Python was installed.
All project dependencies were installed in project virtual environments, not system Python.

### Official technology verification

Reviewed the requested [documentation root](https://relatedb.ai/docs/),
[installation guide](https://relatedb.ai/docs/get-started/install/),
[Python embedding guide](https://relatedb.ai/docs/guides/embed/python/),
[Python API reference](https://relatedb.ai/docs/reference/api/python/),
[limitations](https://relatedb.ai/docs/reference/limitations/),
[two-process guidance](https://relatedb.ai/docs/guides/operate/two-processes-one-store/),
[official repository](https://github.com/relatedb/relate), and
[PyPI distribution](https://pypi.org/project/relate-db/1.0.0/).
The browser fetch tool could not retrieve several documentation pages; their official
`index.md` representations were successfully retrieved directly over HTTPS instead.

Before application implementation, actual calls verified `relate.connect`, parameterized
`execute`, `fetchall`/`single`, context-manager close, `:memory:`, `.rl` reopen, and read-only
access. A further probe verified unique constraints, `MERGE`, `ON CREATE SET`, property maps,
`autocommit=False`, `commit`, and `rollback` against the installed engine.

The official release CLI binary's SHA-256 matched its `SHA256SUMS` entry:

```text
c74b96bbbe10c7d7736c3e860c08b375a77ff55ce8c66ec0bf83a8ba60b225c0
```

The binary was stored in a per-user tools directory without editing system PATH. Its full-path
equivalents of `relate --version`, `relate --mode envelope "RETURN 1 AS ok"`, and
`relate agent-context` succeeded. The envelope contained `rows: [{"ok": 1}]`.
`relate skill install --agent codex` actually failed with:

```text
Error: skill: cannot resolve skills path for codex
```

No Codex skill installation success is claimed. The Python wheel's bundled
`.agents/skills/relate/SKILL.md` was read and its Python usage guidance checked. The CLI and
skill are not application runtime dependencies.

## B. Implementation

| Module / artifact | Implemented behavior |
| --- | --- |
| `config.py` | Environment/default path resolution and persistent `.rl` validation |
| `storage.py` | Real Relate adapter, explicit writable mode, safe close, transactions, error mapping, real counts |
| `schema.py` | Six allowlisted labels, seven directed relationship types, unique ID constraints |
| `seed.py` | Prevalidated demo import, parameterized `MERGE`, conflict detection, atomic rollback, no graph reset |
| `queries.py` | Incident lookup, affected services, dependency paths, deployment/change context, evidence, alerts, four-edge traversal |
| `models.py` | Pydantic entities, provenance/time validation, explicit JSON response models |
| `cli.py`, `__main__.py` | Seed, stats, context, meaningful exit codes |
| `api.py` | Read-only health, incident listing, graph context, 404/503, Swagger/OpenAPI |
| Fixtures | Reviewable JSON and matching packaged JSON: 21 nodes, 27 relationships |
| Tests | 37 real-engine test cases, including parameterized scenarios |
| Quality / CI | Ruff, exact verified development dependency snapshot, Windows/Ubuntu Python 3.11 workflow |
| Documentation | README, AGENTS, architecture, graph schema, this execution report |

Key decisions: one finite seed writer; read-only request-local connections; connection open/use/
close on the same thread; three-hop dependency expansion and 100-row list bounds; explicit
demo provenance; no causal labels or prepared analysis answer. The API reads all context
through Cypher and contains no fixture-file read path.

An early Cypher probe exposed an invalid `ORDER BY` reference after `DISTINCT`. Ordering now
uses projected aliases, and actual queries passed. The first Ruff run found seven long lines;
formatting resolved them. The first test run passed with a Starlette deprecation warning for
legacy httpx. Official Starlette release notes and the installed source confirmed httpx2 support;
the development dependency was updated. Subsequent test runs passed with no warning suppression.

## C. Graph verification

The actual local `data/traceweaver.rl` store returned:

| Label | Node count |
| --- | ---: |
| Incident | 2 |
| Service | 5 |
| Deployment | 3 |
| Change | 3 |
| Evidence | 6 |
| Alert | 2 |
| **Total** | **21** |

| Relationship | Count |
| --- | ---: |
| AFFECTS | 2 |
| DEPENDS_ON | 4 |
| TARGETS | 4 |
| INCLUDES_CHANGE | 3 |
| HAS_EVIDENCE | 6 |
| OBSERVED_ON | 6 |
| RAISED_FOR | 2 |
| **Total** | **27** |

Actual repeated final seed output:

```text
FINAL SEED 1 {'node_count': 21, 'relationship_count': 27}
FINAL SEED 2 {'node_count': 21, 'relationship_count': 27}
FINAL SEED 3 {'node_count': 21, 'relationship_count': 27}
FINAL REOPEN PASS {'node_count': 21, 'relationship_count': 27}
```

The multi-hop query binds `incident_id="INC-001"` and `limit=100`:

```cypher
MATCH (i:Incident {id: $incident_id})-[:AFFECTS]->(s:Service)
      -[:DEPENDS_ON]->(dependency:Service)<-[:TARGETS]-(d:Deployment)
      -[:INCLUDES_CHANGE]->(c:Change)
RETURN DISTINCT i.id AS incident_id, s.id AS affected_service_id,
       dependency.id AS dependency_service_id, d.id AS deployment_id, c.id AS change_id,
       ['AFFECTS', 'DEPENDS_ON', 'TARGETS', 'INCLUDES_CHANGE'] AS relationship_types
ORDER BY affected_service_id, dependency_service_id, deployment_id, change_id LIMIT $limit
```

Actual result:

```json
[{
  "incident_id": "INC-001",
  "affected_service_id": "SVC-PAYMENT",
  "dependency_service_id": "SVC-AUTH",
  "deployment_id": "DEP-001",
  "change_id": "CHG-001",
  "relationship_types": ["AFFECTS", "DEPENDS_ON", "TARGETS", "INCLUDES_CHANGE"]
}]
```

The query crosses four relationships; `TARGETS` is traversed backwards. A test changes the
Auth Service display name and still retrieves the same path, verifying topology rather than
name matching. Context also returns DEP-002 on Payment API as an alternative deployment
candidate. INC-002 returns DEP-003/CHG-003 and EVD-005/EVD-006 without INC-001's records.

Persistence **PASS**: a `.rl` smoke graph with two nodes and one relationship survived close/
reopen before implementation. Tests subsequently reopened the demo graph and retrieved its
four-edge path in a separate Python process. Read-only engine access and HTTP requests left
store bytes unchanged. A separate-process read while a writer held the `.rl` file was refused
with the real locked-store error.

## D. Test results

Commands executed inside `.venv` and/or the independent `.venv-verify`:

```powershell
python -m pip install -e ".[dev]"
python -m pip install -r requirements-dev.lock -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m pip check
python -m traceweaver seed --database ./data/traceweaver.rl
python -m traceweaver stats --database ./data/traceweaver.rl
python -m traceweaver context --incident INC-001 --database ./data/traceweaver.rl
python -m pip wheel --no-deps --wheel-dir .verification/wheels .
```

| Check | Actual result |
| --- | --- |
| In-memory engine and persistent smoke probes | PASS before application implementation |
| Development environment pytest | **37 passed**, 0 failed, 0 skipped |
| Clean independent environment pytest | **37 passed**, 0 failed, 0 skipped |
| Installed-wheel environment pytest | **37 passed in 5.90s**, 0 failed, 0 skipped |
| Ruff | **All checks passed!** |
| Dependency consistency | **No broken requirements found.** |
| Non-editable wheel build/install | PASS; fixture resource present |
| Installed wheel, working directory outside checkout | Seed/stats returned 21/27; context returned CHG-001 |
| Documented Cypher examples | All 10 executed on a real temporary store: README 2, graph schema 7, this report 1 |
| Final development-environment verification | 37 passed in 5.21s; Ruff and pip check passed |
| GitHub Actions workflow | Prepared and locally reviewed; install/lint/test commands run locally |
| Remote Actions and Linux execution | **BLOCKED / not run**; no push or remote execution performed |

The clean environment was newly created and installed from project metadata, then checked
with the recorded lock snapshot. A non-editable wheel was built and installed in that environment;
seed/stats/context ran from an OS temporary directory outside the repository. This verified
that fixture discovery does not rely on the checkout's current directory.

### Required scenario mapping

| Requirement | Verification |
| --- | --- |
| T01 embedded engine | `test_embedded_engine_smoke` |
| T02 database creation | `test_database_creation` |
| T03 fixture loading | `test_fixture_loading` |
| T04 idempotency | `test_idempotent_seed_three_runs` |
| T05 existing data preservation | `test_existing_data_preserved_and_no_accidental_reset` |
| T06 multi-hop traversal | `test_multi_hop_traversal` |
| T07 incident isolation | `test_incident_isolation` |
| T08 persistence | `test_persistence_across_reopening`, `test_persistence_in_separate_python_process` |
| T09 read-only | `test_read_only_rejects_writes_and_store_bytes_unchanged`, `test_api_requests_never_modify_store` |
| T10 health | `test_api_health` |
| T11 API context | `test_api_incident_context`, `test_api_reads_store_changes_instead_of_fixture` |
| T12 errors | Unknown incident, missing-store, corrupt-store, CLI exit-code tests |
| T13 parameter safety | Three lookup inputs plus HTTP injection-shaped input |
| T14 no reset | User nodes, property text, and relationship survive three seed runs |
| Additional atomicity | Seed collision rollback and real uniqueness-violation rollback |
| Additional concurrency | Twelve HTTP reads across four callers; real cross-process writer lock |

### Actual network HTTP verification

Started the actual command below as a subprocess, verified it over loopback with Python's
standard-library HTTP client, and stopped that verification process afterwards:

```powershell
python -m uvicorn traceweaver.api:app --host 127.0.0.1 --port 8000
```

| Request / condition | Observed result |
| --- | --- |
| `/health` | 200; engine relate, persistent true, 21 nodes, 27 relationships |
| `/incidents` | 200 |
| `/incidents/INC-001/context` | 200; four-edge path present |
| `/incidents/INC-002/context` | 200; independent scenario path present |
| `/docs`, `/openapi.json` | 200 |
| Unknown incident | 404 |
| Another process owns writable `.rl` store | 503; generic database-unavailable response |
| Writer closes, subsequent health request | 200 |

## E. Risks and limitations

- Relate is an experimental Neo4j Labs project. The working graph must fit in memory.
- One writer process owns a persistent store. `.rl` files block cross-process reads beside a
  writer. Stop API traffic before reseeding. The application does not remove locks or retry
  unsafe concurrent writes.
- The CLI skill installer could not resolve the Codex path on this Windows environment.
  CLI queries and the embedded Python engine are working; skill installation is optional.
- Verification used Windows/Python 3.14.0. Python 3.11 Windows/Ubuntu workflow execution has
  not occurred; no Linux runtime or remote CI success is claimed.
- Dependency expansion stops after three hops; list results stop at 100 rows. Context exposes
  a conservative truncation flag. Incident listing has no pagination.
- Deployment context requires a linked change, and evidence observations require a linked
  service. Time-aware filtering, ranking, schema migrations, ingestion, and arbitrary real
  incident payloads are not implemented. HTTP models reflect the strict demo schema.
- No authentication/authorization is implemented. The demonstrated server binds to loopback;
  exposing it to other networks requires a separately scoped security design.
- External values are query parameters. Schema identifiers use fixed allowlists. HTTP errors
  omit engine details, local paths, and tracebacks; local CLI errors retain useful diagnostics.
- Fixture references are synthetic `demo://` URLs. No API keys, production credentials, or
  private machine paths belong to tracked project content. Runtime databases and environments
  are excluded by `.gitignore`.
- No model call, causal inference, remediation, graph UI, multi-agent feature, or production
  change is included. Connected deployments must not be presented as proven causes.

## F. Sprint 01 readiness

Ready: actual embedded graph persistence; repeatable demo import; explicit graph schema;
source/time-bearing evidence; parameterized bounded traversals; read-only JSON contract;
meaningful integration tests; reproducible local installation; and prepared CI.

Recommended next work: define versioned investigation/ingestion contracts, add deployment-time
windows without causal assumptions, validate source/path provenance, and design uncertainty
and evaluation cases before adding an AI agent. Keep evidence-grounded claims and alternate
candidates visible.

Technical debt: remote Windows/Ubuntu Python 3.11 verification, the optional Windows skill
installer limitation, deliberate fixture migration/versioning, pagination, richer real-data
schemas, and retrieval of deployment/evidence records without their optional neighbors.

## G. Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Supported Python environment and virtual environment ready | PASS | Existing 3.14.0 x64; two local project environments verified |
| Real `relate-db==1.0.0` installed and import verified | PASS | Installed native Windows wheel and actual queries |
| In-memory Relate smoke test | PASS | Two nodes, one edge, asserted MATCH result |
| Persistent `.rl` store created | PASS | Actual local demo store and isolated test stores |
| At least 20 nodes / 25 relationships loaded through Cypher | PASS | Actual counts 21 / 27 |
| Repeated seed does not duplicate records | PASS | Three final seed runs stay 21 / 27; test coverage |
| Existing user data preserved | PASS | User nodes, text, and edge survive three imports |
| Meaningful traversal of at least three relationships | PASS | Four-edge Incident → Service → dependency ← Deployment → Change path |
| Persistence after close/reopen | PASS | Direct reopen and independent Python process |
| CLI seed, stats, context | PASS | Subprocess tests and installed wheel outside checkout |
| FastAPI queries real Relate | PASS | Database mutation reflected by endpoint; actual network HTTP checks |
| Unknown incident and unavailable-store handling | PASS | 404; missing/corrupt/locked store 503 |
| At least 10 real pytest tests pass | PASS | 37 passed, 0 failed, 0 skipped |
| Ruff succeeds | PASS | All checks passed |
| GitHub Actions workflow prepared | PASS | Windows/Ubuntu Python 3.11 matrix and real-engine commands |
| README and technical documentation complete | PASS | README, architecture, graph schema, AGENTS, this report |
| No fake graph repository or hard-coded analysis answer | PASS | Actual Relate storage and graph queries; topology/provenance tests |
| Report contains actual execution results | PASS | Observed commands, counts, query result, tests, and HTTP statuses recorded |

Optional / external checks are tracked separately: **Codex CLI skill installation — BLOCKED**
(installer cannot resolve path); **remote GitHub Actions — BLOCKED / not run** (no push
requested or performed). These do not substitute for any unverified acceptance criterion.

The local repository uses `main`. No remote was created and no push was performed. The delivery
commit is identified by `git log -1`; the working database remains local and excluded from Git.
