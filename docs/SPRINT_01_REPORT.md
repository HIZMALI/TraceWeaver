# Sprint 01 Report — Evidence Intelligence & Temporal Investigation

Date: **2026-11-12**, Europe/Istanbul. Overall result: **PASS** for the acceptance criteria.
Remote CI and Python 3.11 runtime execution are **UNVERIFIED / NOT RUN**, not claimed as passed.

## 1. Baseline audit and preservation

- Repository root verified with `git rev-parse --show-toplevel`; branch `main`, baseline commit
  `e504012` (`sprint00: establish real Relate foundation and verified graph API`).
- Initial `git status --short --branch`: `## main`, with no changed/untracked user files.
- Read AGENTS, project/dependency metadata, README, architecture/schema/Sprint 00 report,
  source modules, both baseline fixture copies, all existing tests, and CI workflow.
- Windows x64, CPython **3.14.0**, `relate-db==1.0.0`, pytest 9.2.0, Ruff 0.17.4.
- Actual baseline commands: **37 passed in 5.33s**; Ruff **All checks passed!**;
  pip check **No broken requirements found.**
- Existing default store was inspected read-only and returned **21 nodes / 27 relationships**.
  Its before/after SHA-256 is unchanged:

```text
3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3
```

No seed, migration, write connection, reset, or deletion was run on an existing workspace store.
An autouse test-session guard also checks hashes of pre-existing workspace `data/*.rl` files.
Writes for new scenarios and verification used independent OS temporary stores.

The original fixture copies, legacy `models.py`, `storage.py`, `pyproject.toml`, dependency lock,
and CI workflow were compared with the baseline commit and remain unchanged. All 33 original
test functions / 37 parameterized cases remain. The exact OpenAPI route-set assertion was
extended to include the new fourth GET route; it was not weakened to a subset assertion.

## 2. Implementation and changed files

| File / artifact | Implemented change |
| --- | --- |
| `investigation_models.py` | Separate tolerant investigation response and strict bounded input models |
| `temporal.py` | Explicit-offset parsing, original/UTC values, exact window classes, no inferred time |
| `provenance.py` | Source/time/graph traceability, typed invalid metadata, independent verification dimension |
| `contradictions.py` | Same-context structured comparisons, interval overlap, explicit state matrix |
| `investigation.py` | Shared real-graph investigation, uncertainty/gaps, candidate paths, timeline, honest caps |
| `queries.py` | Added bounded parameterized candidate/change/evidence/observation queries; legacy queries unchanged |
| `api.py` | Added investigation GET route, validated options, generic logged unexpected-error handler |
| `cli.py` | Added investigate command with existing exit codes and the shared response model |
| `seed.py` | Explicit version-2 synthetic specimen format, preserving version-1 strictness and atomic conflict safety |
| `sprint01_cases.json` | Separate opt-in synthetic cases, plus identical packaged resource |
| New tests | Temporal, investigation, HTTP/CLI, exact legacy response contracts and store guards |
| Documentation | Updated README/AGENTS/architecture/schema; new contract, implementation note, full actual JSON example, this report |

No dependency was added or upgraded. No LLM, paid service, Docker, external source fetch,
causal score, root cause verdict, write endpoint, UI, remediation, or production access was added.
The optional Sprint 00 CLI skill issue was left outside this sprint's development work.

The pre-code contract decisions are in [the implementation note](SPRINT_01_IMPLEMENTATION_NOTE.md).
The [complete response contract](INVESTIGATION_CONTRACT.md) describes all fields and limits.

## 3. Real graph-path verification

The new candidate query was actually executed on Relate 1.0.0, including the path predicate,
list-valued reducing minimum, parameter binding, and LIMIT lookahead:

```cypher
MATCH p=(i:Incident {id: $incident_id})-[:AFFECTS]->(:Service)
        -[:DEPENDS_ON*0..3]->(target:Service)<-[:TARGETS]-(d:Deployment)
WHERE all(n IN nodes(p) WHERE single(m IN nodes(p) WHERE elementId(m) = elementId(n)))
WITH d, target, min([length(p), [n IN nodes(p) | n.id]]) AS chosen_path
RETURN properties(d) AS deployment, properties(target) AS target,
       chosen_path[0] - 2 AS dependency_depth, chosen_path[1] AS node_ids
ORDER BY deployment.id, target.id LIMIT $limit
```

Actual baseline candidate paths, shortened from the graph-backed response:

```json
[
  {"deployment_id":"DEP-002","target_service_id":"SVC-PAYMENT","dependency_depth":0,
   "node_ids":["INC-001","SVC-PAYMENT","DEP-002"]},
  {"deployment_id":"DEP-001","target_service_id":"SVC-AUTH","dependency_depth":1,
   "node_ids":["INC-001","SVC-PAYMENT","SVC-AUTH","DEP-001"]}
]
```

DEP-001's full change path is INC-001 → SVC-PAYMENT → SVC-AUTH ← DEP-001 → CHG-001,
with stored TARGETS source DEP-001, target SVC-AUTH, and REVERSE traversal. Depth-3 targets
are included; depth-4 targets are excluded by an actual graph test. Cyclic paths do not
duplicate candidates. A deployment without INCLUDES_CHANGE remains a candidate with `changes: []`.

This is Cypher traversal, not fixture scanning, a Python adjacency walk, a text lookup, or a
prepared analysis answer. Up to six bounded graph queries fetch all candidate/evidence context;
a real 100-item integration test counted six actual adapter calls, not per-item query loops.

Reviewed the official [Cypher differences](https://relatedb.ai/docs/reference/cypher/differences-from-neo4j/)
and [tagged Relate 1.0.0 limitations](https://github.com/relatedb/relate/blob/v1.0.0/docs/limitations.md).
The former was read through its official HTTPS `index.md` representation after the browser fetch
failed. No APOC/GDS dependency was introduced. New query syntax was verified on the actual engine.

## 4. Temporal edge cases and scenario results

Anchor for the synthetic CASE-INC scenario is `2026-11-12T10:00:00Z`:

| Scenario / event | Actual result |
| --- | --- |
| C01 CASE-DEP-BEFORE, 09:30Z on dependency service | BEFORE, INVESTIGATE; not a cause verdict |
| C02 CASE-DEP-AFTER, 10:02Z | AFTER, TEMPORALLY_EXCLUDED only as a preceding trigger |
| C03 CASE-DEP-ONSET, 10:00Z | AT_ONSET; not marked before onset |
| C04 CASE-DEP-OFFSET, 13:00+03:00 | Same UTC instant, AT_ONSET; original string retained |
| C05 CASE-NO-TIME | null onset, candidates UNKNOWN, PARTIAL_CONTEXT |
| C06 CASE-E-NAIVE | INVALID_TIMESTAMP, UNKNOWN time, INVALID provenance |
| Lower boundary 08:00Z | BEFORE |
| One second below lower boundary 07:59:59Z | OUTSIDE_WINDOW |
| Upper boundary 10:30Z | AFTER |
| One second above upper boundary 10:30:01Z | OUTSIDE_WINDOW |
| Zero-minute windows | Only exact onset admitted |
| Repeated DST local 01:30 with -04:00 / -05:00 offsets | Distinct UTC 05:30 / 06:30 instants |
| Missing/invalid/naive anchor | UNKNOWN classifications; no timestamp guessing |
| Explicit invalid semantic field plus valid legacy/ingestion times | Invalid preferred field retained; no fallback to ingestion |

An early test failed because Python's `fromisoformat` normalizes an invalid `+00:60` offset.
Explicit offset component validation fixed the cause; the assertion remains and now passes.
No assertion, failure, warning, or engine result was bypassed. Temporal comparison uses signed
deltas, and a year-0001 boundary test passes without window arithmetic overflow.

## 5. Provenance and structured observations

Actual CASE-INC provenance audit:

```json
{
  "scope":"RETURNED_EVIDENCE","total_evidence":11,
  "traceable_count":6,"incomplete_count":4,"invalid_count":1,
  "unverified_external_count":0
}
```

- C10 CASE-E-MISSING-REF / CASE-E-MISSING-SOURCE remain INCOMPLETE, not silently dropped.
- CASE-E-NO-TIME remains INCOMPLETE with a missing observation-time warning.
- CASE-E-ORPHAN remains visible with its actual Incident → Evidence path and missing-service warning.
- CASE-E-NAIVE is INVALID and preserves the original naive value without guessing UTC.
- A test using an actual engine DATE source/timestamp retains an explicit typed invalid
  representation and does not turn an invalid type into apparently traceable string metadata.
- An isolated non-demo source-reference test returns TRACEABLE metadata and independently
  UNVERIFIED_EXTERNAL, preserving the exact URL and making no external request.
- Duplicate source references produce warnings without a misinformation or contradiction verdict.

Actual structured results for CASE-INC:

| Evidence IDs | Classification / reason |
| --- | --- |
| CASE-E-FAILED + CASE-E-HEALTHY | CONFLICTING_OBSERVATIONS; availability, CASE-API, demo, overlap 09:59Z..10:01Z |
| CASE-E-DEGRADED + CASE-E-FAILED | UNDETERMINED |
| CASE-E-DEGRADED + CASE-E-HEALTHY | UNDETERMINED |
| CASE-E-EARLY + CASE-E-LATE | No conflict: same latency signal but distinct 09:00Z/11:00Z observation instants |
| CASE-E-WRONG-SERVICE | Not evaluable: structured service does not match an actual observed-service link |
| CASE-E-OTHER | Not returned for CASE-INC; belongs to CASE-OTHER despite shared CASE-API |

Audit: **5 evaluable evidence**, **6 not evaluable**, **3 comparable pairs**, **1 conflict**,
**2 undetermined**. Separate tests verify different service, signal, environment, valid disjoint
intervals, and invalid states do not create false conflicts. Identical states have no conflict
record. The baseline incident has **0 contradictions / 4 not evaluable**, without invented signals.

Every result retains `causal_conclusion=NOT_ESTABLISHED`. Missing evidence is not interpreted as
proof that there is no problem. Readiness, data quality, and causality remain separate dimensions.

## 6. API and CLI execution

Actual loopback Uvicorn verification used a fresh temporary baseline-plus-cases store, a free
loopback port, and PowerShell `Invoke-RestMethod`. The owned verification server was stopped.
The store's SHA-256 was identical before and after all HTTP reads.

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/incidents/INC-001/investigation?pre_minutes=120&post_minutes=30'
```

The command above is the documented standard port example; the actual verification used an
available dynamically selected loopback port. Selected real baseline response fields:

```json
{
  "incident_id":"INC-001","is_demo":true,
  "incident_started_at":"2026-11-10T10:05:00Z",
  "investigation_status":"PARTIAL_CONTEXT",
  "causal_conclusion":"NOT_ESTABLISHED",
  "results_may_be_truncated":false
}
```

The [full actual response](examples/INC-001-investigation.json) is checked by a real-engine test.
CASE-INC over actual HTTP returned **6 candidates, 11 evidence, 1 conflict, 2 undetermined**.
CASE-NO-TIME returned 200/PARTIAL_CONTEXT with a null anchor. Unknown incident returned 404;
invalid negative pre-window returned 422. TestClient plus a separate-process real lock test
verified missing/corrupt/locked stores return generic 503. An intentional HTTP-only failing
route verified generic 500 with details confined to server logs; it is not an application route.

Actual final local read-only CLI commands all succeeded:

```powershell
python -m traceweaver stats --database ./data/traceweaver.rl
python -m traceweaver context --incident INC-001 --database ./data/traceweaver.rl
python -m traceweaver investigate --incident INC-001 --pre-minutes 120 --post-minutes 30 --database ./data/traceweaver.rl
```

Stats remained 21/27. Legacy context retained its four-edge CHG-001 path. Investigation returned
two BEFORE deployment candidates, four TRACEABLE synthetic evidence records, PARTIAL_CONTEXT
because structured observations are absent, and NOT_ESTABLISHED causality. CLI and HTTP JSON
are compared exactly with the same non-default options. CLI error codes 1/2/3 remain verified.

## 7. Fixture counts, boundedness, and data safety

| Dataset | Actual clean counts |
| --- | --- |
| Original Sprint 00 fixture/store | **21 nodes / 27 relationships**, 2 incidents |
| Additive Sprint 01 fixture only | **30 nodes / 40 relationships**, 3 distinct CASE incidents |
| Combined isolated store | **51 nodes / 67 relationships** |
| Combined isolated store plus user note | **52 nodes / 67 relationships**, unchanged after repeated additive seed |

The additive import has explicit schema_version 2, synthetic ownership, separate IDs, and identical
packaged JSON. It accepts intentionally malformed/missing metadata specimens without relaxing
version-1 fixtures. Import conflicts roll back earlier new inserts and preserve the prior user graph.
There is no automatic case import or migration. The default existing 21/27 store was never seeded.

Actual cap tests cover exactly-full versus overflowing candidate/evidence lists, over-100 graphs,
global change/observation link caps, timeline caps, and comparison caps. With 22 structured records
(11 HEALTHY / 11 FAILED), audit counts report **121 conflicts**, return **100**, and flag actual
contradiction truncation. All flags use N+1 or exact post-materialization counts, not equality to N.

## 8. Tests, installation, packaging, and CI

| Test group | Cases |
| --- | ---: |
| Preserved original tests | **37** |
| New graph/investigation integration tests | 31 |
| New HTTP/CLI tests | 20 |
| New complete legacy contract tests | 2 |
| New temporal/options tests | 29 |
| **New total** | **82** |
| **Overall total** | **119** |

Observed execution results:

| Check | Actual result |
| --- | --- |
| Baseline pytest | 37 passed in 5.33s |
| Development environment, expanded suite | 119 passed in 13.81s; 0 failed, 0 skipped |
| Final development-environment regression | 119 passed in 9.85s; Ruff, pip check, actionlint passed |
| Fresh independent `.venv-sprint01-verify` | 119 passed in 10.96s; 0 failed, 0 skipped |
| Non-editable installed wheel environment | 119 passed in 9.76s; 0 failed, 0 skipped |
| Ruff | All checks passed |
| pip check | No broken requirements found |
| Wheel build/install | PASS, both fixture resources present |
| Installed wheel outside checkout | Seed 21/27, stats/context/investigate, opt-in cases 51/67, CASE-INC investigation all passed |
| PowerShell + real Uvicorn HTTP | PASS; expected statuses and unchanged temporary-store hash |
| Workflow syntax | actionlint 1.7.12 passed; official release archive SHA-256 verified before use |
| Documented Cypher | All 11 README/schema/Sprint 01 report examples executed on a real temporary store |
| GitHub Actions remote run | **NOT RUN / UNVERIFIED**; no push |
| Python 3.11 Windows / Ubuntu runtime | **UNVERIFIED** locally; not discoverable as an installed Python command |

The fresh environment installed the unchanged `requirements-dev.lock` and editable project.
A regular wheel was then installed there and exercised from outside the checkout, followed by
the full test suite. No system Python or working dependency environment was upgraded. The
existing Windows/Ubuntu Python 3.11 workflow remains unchanged and passed local syntax validation.

Commands executed included:

```powershell
python -m pytest -q
python -m ruff check .
python -m pip check
python -m pip install -r requirements-dev.lock -e ".[dev]"
python -m pip wheel --no-deps --wheel-dir .verification/sprint01/wheels .
```

Every test uses real Relate where graph access is involved. No graph repository/mock, skipped
failure, assertion relaxation, generated fake result, or fixture-file analysis answer was used.

## 9. Limitations and Sprint 02 readiness

- Row limits bound returned data, not engine query time/RAM or raw metadata byte sizes. Relate
  keeps its working graph in memory. High-degree topology still warrants future profiling.
- One representative shortest simple path per deployment/target pair is exposed; other paths
  are not an exhaustive export. Candidate IDs are selected before temporal presentation sorting.
- Auxiliary change/observation lists are globally capped at 100; omissions remain explicit.
  There is no pagination. Evidence/provenance/comparison counts describe returned evidence only.
- Timestamp text is restricted to documented explicit-offset ISO forms with microsecond precision.
  Unsupported precision/types remain visibly invalid instead of being silently rounded or guessed.
- No external source is contacted or truth-verified. Metadata traceability is not causal evidence.
- Comparisons require structured values and matching graph context. Missing fields, differing
  contexts, or non-overlapping times do not justify a contradiction. DEGRADED remains undetermined.
- The legacy strict context model remains intentionally unchanged; malformed version-2 specimens
  belong to the investigation contract, not an automatic legacy schema migration.
- No AI agent, root cause inference, production authentication, dashboard, ingestion connector,
  remediation, or production change was added. These remain PLANNED and separately scoped.
- Python 3.11/Ubuntu runtime and remote CI have not been executed. No new Python was installed
  merely to replace the verified existing interpreter. The optional CLI skill limitation is unchanged.

Sprint 02 preparation: agree on a versioned real-data ingestion contract, external-source access
and verification policy, structured-signal taxonomy, pagination/profiling needs, and evaluation
cases for uncertainty and evidence citations before adding any AI investigation agent.

## 10. Acceptance criteria

| Criterion | Status | Actual evidence |
| --- | --- | --- |
| main/e504012 history and starting user data preserved | PASS | Initial clean main, original history retained, existing store hash unchanged |
| Real Relate 1.0.0 persistent store; no fake graph | PASS | Native queries/tests, actual .rl reopen and subprocess coverage |
| Baseline 21/27 fixture and two incidents preserved | PASS | Fixture comparison, original tests, final read-only counts |
| Old CLI/HTTP contracts preserved | PASS | All original cases plus full e504012-source response snapshots |
| UTC and five temporal classes work | PASS | Boundary, offset, DST, zero-window and graph scenario tests |
| Missing/naive times are not guessed | PASS | UNKNOWN plus explicit missing/invalid warnings; no ingestion fallback |
| DEPENDS_ON/TARGETS discover candidates through Cypher | PASS | Actual reducing path query, depth-3/depth-4 integration test |
| Deployment without INCLUDES_CHANGE retained | PASS | CASE-DEP-NOCHANGE with empty changes and real path |
| API/CLI candidate paths include actual IDs/directions | PASS | DEP-001 path and reverse TARGETS assertions; exact JSON parity |
| AFTER deployment is not a preceding cause candidate | PASS | CASE-DEP-AFTER remains AFTER/TEMPORALLY_EXCLUDED as preceding trigger |
| Provenance gaps and independent external verification | PASS | Actual audit 6/4/1; non-demo TRACEABLE + UNVERIFIED_EXTERNAL test |
| Contradictions only for comparable structured observations | PASS | One conflict, two undetermined; context/time false-positive tests |
| Other incident evidence does not leak | PASS | CASE-OTHER shares a service but its evidence stays scoped |
| NOT_ESTABLISHED, no invented confidence | PASS | Literal response model, all scenario/API/CLI assertions |
| Honest truncation and list limits | PASS | Exact-full vs overflow, auxiliary caps, 121-versus-100 conflict test |
| New endpoint real-engine 200/404/422/503 | PASS | TestClient, separate-process lock test, real loopback requests |
| CLI/HTTP use one investigation contract | PASS | Shared service/model and exact non-default JSON comparison |
| Read-only behavior and thread affinity | PASS | Store bytes/hash guards and concurrent new/legacy API reads |
| 37 preserved + at least 20 new tests; at least 57 PASS | PASS | **37 + 82 = 119 PASS**, no failed or skipped cases |
| Ruff and pip check | PASS | Both clean in development and independent environments |
| Packaging, clean install, PowerShell commands verified | PASS | Installed wheel outside checkout plus actual Invoke-RestMethod checks |
| Contract and Sprint 01 report complete | PASS | These documents and full actual JSON example |
| Unexecuted remote CI disclosed | PASS | Explicit NOT RUN/UNVERIFIED; local actionlint only |
| Demo labels and no automatic user-store import | PASS | Separate version-2 fixture, explicit --fixture, unchanged existing-store hash |
| Git diff, secret/private-path and ignored-store audit | PASS | Final review includes explicit staged-file and ignore checks; no database/secrets staged |

External verification items remain **BLOCKED / NOT RUN**: remote GitHub Actions and local
Python 3.11/Ubuntu execution. The criterion to disclose them is satisfied; their runtime success
is not asserted.

## 11. Git delivery

The implementation is committed locally on `main` with the requested subject:
`sprint01: add temporal and evidence-grounded incident investigation`.
Implementation commit: **`aec6d72017df8ae478ed0e06f495f80770771d59`**.

Observed immediately after that commit: `git status --short --branch` returned only `## main`.
A separate documentation-only commit records this actual implementation hash, avoiding a
self-referential report identity. It changes no application, test, fixture, dependency, or CI
code from the tested implementation. Inspect `git log -2 --oneline` for both local commits.
Final Git status is checked after the documentation update. No remote, new branch, force push,
database commit, or push was created.
