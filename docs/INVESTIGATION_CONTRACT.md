# Investigation contract

This is a deterministic graph/evidence review contract, not an AI or causal inference API.
All bundled records are synthetic demo data. `causal_conclusion` is always **NOT_ESTABLISHED**.

## Entry points and compatibility

```text
GET /incidents/{incident_id}/investigation
python -m traceweaver investigate --incident INC-001 --database ./data/traceweaver.rl
```

Both entry points use `investigation.investigate` and the same Pydantic `Investigation` model.
The original health, incidents, context, seed, and stats contracts are unchanged. Full legacy
JSON snapshots were captured from commit e504012's actual code and a real store.
Additional console routes are documented in the [dashboard contract](DASHBOARD_CONTRACT.md)
and [agent contract](AGENT_TOOL_CONTRACT.md); they do not broaden this response model.

| Option | Default | Accepted values |
| --- | ---: | --- |
| `pre_minutes` / `--pre-minutes` | 120 | Integer 0..1440 |
| `post_minutes` / `--post-minutes` | 30 | Integer 0..1440 |
| `max_candidates` / `--max-candidates` | 100 | Integer 1..100 |
| `max_evidence` / `--max-evidence` | 100 | Integer 1..100 |

Floating-point input, boolean values, and non-integer numeric strings are rejected. HTTP query
parameters use underscores; CLI flags use hyphens. IDs and graph limits are query parameters,
never concatenated into Cypher. There is no arbitrary-Cypher endpoint or write endpoint.

HTTP: 200 success (including partial review context), 404 unknown incident, 422 invalid request,
503 missing/corrupt/locked/unreadable store or structurally incompatible graph IDs. Unexpected
failures are logged on the server and return generic 500. Error responses omit internal paths
and tracebacks. The local CLI retains exit codes 0/1/2/3 and useful local error diagnostics.

## Top-level response fields

| Field | Meaning |
| --- | --- |
| `incident_id` | Stable string ID looked up in Relate |
| `is_demo` | Actual incident demo marker; null if no valid boolean exists |
| `incident` | Graph incident properties, not a fixture lookup |
| `incident_started_at` | Normalized UTC onset or null when unknown |
| `incident_time` | Original onset metadata, selected source field, UTC, warning code |
| `window` | Effective pre/post minute values |
| `limits` | Candidate/evidence caps, dependency depth 3, auxiliary list cap 100 |
| `affected_services` | Distinct graph AFFECTS neighbors, bounded to 100 |
| `candidates` | Deployment/target pairs found by bounded Cypher, with real paths |
| `evidence` | Incident HAS_EVIDENCE records, retaining incomplete observations |
| `provenance_audit` | Mutually exclusive quality counts over returned evidence, plus independent verification count |
| `contradictions` | Structured conflicting or UNDETERMINED pairs, at most 100 |
| `contradiction_audit` | Evaluable/not-evaluable evidence counts, comparable pair count, conflicts, undetermined pairs, warnings |
| `timeline` | Up to 100 selected incident/deployment/evidence events with their own actual observation/event times |
| `data_quality` | Time/source metadata status and explicit issue counts |
| `investigation_status` | READY_FOR_REVIEW, PARTIAL_CONTEXT, or INSUFFICIENT_EVIDENCE |
| `status_reasons` | Stable codes explaining gaps behind review status |
| `causal_conclusion` | Literal NOT_ESTABLISHED in every response |
| `limitations` | Referenced gaps plus unverified external-source limitation when applicable |
| `evidence_gaps` | Referenced, counted missing/inadequate evidence categories |
| `next_checks` | Deterministic checks derived only from current gaps/unverified references |
| `truncation` | Per-list actual truncation indicators |
| `results_may_be_truncated` | Logical OR of the per-list indicators |
| `interpretation` | Explicit temporal/provenance/causality caution |
| `demo_notice` | Synthetic-data disclosure, or honest unknown/non-synthetic source-status notice |

The [full actual baseline JSON example](examples/INC-001-investigation.json) was generated from
an isolated real Relate store. It is compared to actual service output by a regression assertion.
Selected real fields from that response:

```json
{
  "incident_id": "INC-001",
  "is_demo": true,
  "incident_started_at": "2026-11-10T10:05:00Z",
  "window": {"pre_minutes": 120, "post_minutes": 30},
  "investigation_status": "PARTIAL_CONTEXT",
  "causal_conclusion": "NOT_ESTABLISHED",
  "contradictions": [],
  "results_may_be_truncated": false
}
```

## Event times, normalization, and boundaries

The existing schema documents these meanings; no onset is guessed:

| Entity | Preferred field, if present | Backward-compatible semantic mapping |
| --- | --- | --- |
| Incident | `incident_started_at` | Existing `timestamp` is demo incident onset |
| Deployment | `deployment_occurred_at` | Existing `timestamp` is rollout occurrence |
| Evidence | `observed_at` | Existing `timestamp` is observation time |

`ingested_at`, if present among properties, remains ingestion metadata. It is never substituted.
An explicit preferred field takes precedence even when invalid. Relate null properties are
absent on retrieval; a genuinely absent preferred property uses the documented legacy mapping.
When both event fields are absent, the time is UNKNOWN.

Every `TimestampValue` contains `source_field`, `original`, `utc`, and `warning_code`.
Accepted text is `YYYY-MM-DDTHH:MM:SS[.ffffff]Z` or an explicit numeric `±HH:MM` offset.
Parsing checks the actual calendar, offset ranges, and up to six fractional digits. It preserves
the original string and normalizes to aware UTC. Naive values, date-only text, space separators,
unknown `-00:00` offsets, malformed values, non-string types, and higher-precision text are invalid;
precision is not silently discarded. Missing/null/empty values use MISSING_TIMESTAMP; malformed
ones use INVALID_TIMESTAMP. Non-JSON engine types are retained as explicit typed representations,
not silently converted into apparently valid strings. Such metadata remains invalid for this contract.

Let `t` be the normalized event time and `a` the known incident onset:

| Classification | Exact interval / condition |
| --- | --- |
| BEFORE | `a - pre_minutes <= t < a` |
| AT_ONSET | `t == a` |
| AFTER | `a < t <= a + post_minutes` |
| OUTSIDE_WINDOW | Valid times outside those intervals |
| UNKNOWN | Event time or incident anchor missing/invalid |

Zero-width windows admit only exact onset. Equal UTC instants with different explicit offsets
are AT_ONSET. Explicit DST offsets distinguish repeated local clock times. Window comparison
uses a signed delta, avoiding datetime boundary underflow/overflow when constructing endpoints.

An AFTER observation is shown at its actual observation time; it is never claimed to have been
available before onset. The response is not an as-of historical snapshot. Unknown-anchor records
stay visible as UNKNOWN rather than being filtered by a guessed time.

## Candidates and graph paths

Candidate discovery uses the real pattern:

```text
Incident -AFFECTS-> affected Service -DEPENDS_ON*0..3-> target Service <-TARGETS- Deployment
```

The reducing Cypher query returns distinct deployment/target pairs, their shortest dependency
depth, and a real simple node sequence. Repeated nodes/cyclic paths are excluded. One shortest
lexicographic representative is shown per pair; it is not an exhaustive path export. An
INCLUDES_CHANGE edge is optional. Changes are retrieved in one bounded batch and may be empty.
Unrelated service deployments are not discovered. Candidate services can be shared between
incidents; evidence membership still comes exclusively from each incident's HAS_EVIDENCE edges.

| Candidate field | Meaning |
| --- | --- |
| `deployment_id`, `target_service_id` | Actual stable graph IDs |
| `change_ids`, `changes` | Returned change neighbors, possibly empty |
| `dependency_depth` | 0 for affected service itself; otherwise 1..3 |
| `deployment_occurred_at` | Original/normalized occurrence time |
| `temporal_classification`, `temporal_reason` | Window class and plain explanation |
| `candidate_assessment`, `assessment_reason` | Review suitability, never a causal verdict |
| `graph_paths` | Actual representative incident-to-deployment path |
| `properties` | Deployment metadata as read from the graph |

Each change contains `change_id`, its `properties`, and the full `graph_path` extended with
INCLUDES_CHANGE. A graph path contains `node_ids` in traversal order and `edges`. Every edge
has `type`, stored `source_id`, stored `target_id`, and `traversal_direction` FORWARD or REVERSE.
For example, the dependency candidate DEP-001 has:

```json
{
  "node_ids": ["INC-001", "SVC-PAYMENT", "SVC-AUTH", "DEP-001"],
  "edges": [
    {"type":"AFFECTS","source_id":"INC-001","target_id":"SVC-PAYMENT","traversal_direction":"FORWARD"},
    {"type":"DEPENDS_ON","source_id":"SVC-PAYMENT","target_id":"SVC-AUTH","traversal_direction":"FORWARD"},
    {"type":"TARGETS","source_id":"DEP-001","target_id":"SVC-AUTH","traversal_direction":"REVERSE"}
  ]
}
```

BEFORE yields INVESTIGATE; this conveys temporal suitability only. UNKNOWN yields
INSUFFICIENT_DATA. AT_ONSET, AFTER, and OUTSIDE_WINDOW yield TEMPORALLY_EXCLUDED **only as
preceding triggers**, while remaining visible context. There is no probability, cause score,
root_cause field, caused_by relation, or automatic decision.

## Evidence provenance and source verification

Each evidence item exposes `evidence_id`, exact `source`/`source_ref` values, its original and
normalized `evidence_observed_at`, `observed_service_ids`, actual `graph_paths`, `is_demo`,
`provenance_status`, separate `verification_status`, temporal class/reason, warnings, and properties.
An orphan evidence node retains its actual Incident → Evidence path and a missing-service warning.
No URL is invented, resolved, contacted, or authenticated.

Primary metadata quality is mutually exclusive:

- TRACEABLE: nonempty string source/reference, valid observation timestamp, and actual returned
  Incident → Evidence → Service links, with a known boolean demo marker.
- INCOMPLETE: missing required metadata or grounding link, without an invalid field.
- INVALID: malformed timestamp or an invalid source/reference type. Invalid takes precedence
  over simultaneously missing fields.

Verification is an independent dimension: SYNTHETIC for marked demo references,
UNVERIFIED_EXTERNAL for non-demo/unknown-demo references, and NOT_AVAILABLE without a valid
reference. **TRACEABLE does not mean true or externally VERIFIED.** A duplicate source reference
produces a warning without implying misinformation or a contradiction.

The audit's `scope` is RETURNED_EVIDENCE and `total_evidence` is the number audited in this
response. `traceable_count + incomplete_count + invalid_count == total_evidence`.
`unverified_external_count` overlaps those quality categories and must not be added to that sum.
It is not the count of all unreturned graph evidence when evidence is truncated. Warnings expose
their own cap indicator. An absent observation caused by a capped batch remains explicitly
uncertain through `truncation.observations`; absence is never proof that the full graph has no link.

## Structured observation comparisons

No narrative text or keyword matching participates. A record is evaluable only when it has:

1. Nonempty string `signal_key`, `service_id`, `environment`, and an allowlisted `observed_state`.
2. A `service_id` matching an actual returned OBSERVED_ON service link.
3. A valid ordered explicit observation interval (both endpoints), or a valid observation instant
   when neither interval field exists. A partial/invalid interval does not fall back to a point.

Two evaluable records are compared only if the incident scope, service ID, signal key, and
environment match exactly and their **closed** intervals overlap (`max(start) <= min(end)`).
Instant observations are `[t,t]`; equal UTC instants match. Different services, environments,
signals, or non-overlapping times do not conflict automatically.

| States | Output |
| --- | --- |
| HEALTHY + FAILED | CONFLICTING_OBSERVATIONS |
| HEALTHY + DEGRADED | UNDETERMINED |
| FAILED + DEGRADED | UNDETERMINED |
| Equal states | No contradiction record |

A comparison result has `evidence_ids`, `signal_key`, `service_id`, `environment`,
`overlap_window` (UTC start/end), `observed_states`, `reason`, and `classification`.
UNDETERMINED entries are not counted as conflicts. This is inconsistency/uncertainty between
observations, not a finding that a source lied or a deployment caused an incident.

`contradiction_audit.not_evaluable_count` counts returned evidence that cannot form a valid
structured observation, with referenced warnings. `comparable_pair_count` also includes pairs
with equal states; conflict/undetermined counts cover all comparisons of the returned evidence,
even when the result list is truncated. The baseline has zero conflicts and four non-evaluable
records because it lacks structured signal fields; none are invented.

## Review status, quality, gaps, and determinism

`data_quality.status` describes time/source completeness: INVALID if malformed metadata is
present, otherwise INCOMPLETE if times/provenance are missing or lists truncated, else COMPLETE.
`unknown_timestamp_count`, `provenance_issue_count`, and `structured_evidence_not_evaluable_count`
are separate counts; candidate/time counts concern returned deployment/target pairs and evidence,
not all unreturned graph entities. COMPLETE metadata may still lack structured comparison data.

No returned evidence yields INSUFFICIENT_EVIDENCE. With evidence, any gap yields PARTIAL_CONTEXT;
otherwise status is READY_FOR_REVIEW. Gaps include missing/invalid onset, event times, source/
service provenance, structured observations, affected services, missing deployment changes,
observation reconciliation, and truncation. READY_FOR_REVIEW is never a causal conclusion.
Every Finding contains `code`, `message`, bounded `entity_ids`, and `count`. Counts can exceed
the displayed reference list length when a larger category is summarized.

The service does not read the clock, contact sources, run a model, or use randomness. The same
store snapshot and options give the same response. Cypher first selects candidates by deployment
ID and target ID, and evidence by ID, with lookahead. Within the selected candidate subset,
presentation sorts by temporal category (BEFORE, AT_ONSET, AFTER, OUTSIDE_WINDOW, UNKNOWN), then
depth, normalized timestamp, deployment ID, target ID. This is **not** a global causal ranking.
Timeline uses actual UTC instants (unknown last), kind, ID, and target ID. Evidence, links,
comparison pairs, and warnings follow stable ID/query order; findings sort by code.

## Caps, truncation, and limitations

All graph result lists use an extra row to detect actual truncation; exactly N results without
an extra row do not claim truncation. User caps are 1..100 candidates and evidence. Global
affected-service, change-link, and observation-link caps are 100 each. Each candidate exposes
one representative path and at most 100 returned changes. Each evidence has at most 100 returned
service links/paths. A path has at most seven nodes including its change. Timeline and comparison
results are capped at 100 after exact in-memory length/count checks. Warning/result lists are
bounded to 100. There is no pagination or continuation token in this sprint.

`truncation` names candidates, evidence, affected_services, changes, observations, timeline,
contradictions, and provenance_warnings. Its OR is `results_may_be_truncated`; a true value adds
TRUNCATED_CONTEXT and prevents READY_FOR_REVIEW. Complete metadata for a returned item does not
imply that omitted candidates/evidence or alternate graph paths were evaluated. Row caps are not
a database execution-time, memory, or raw-property byte limit; high-degree graphs still need
future query profiling and admission limits. Arbitrary property payloads are not a safe public
ingestion interface. The finite input cap bounds structured comparison work to at most 4,950 pairs.

## Agent and consumer boundaries

An agent may cite stable IDs, exact source references, original/UTC observation times, graph edge
directions, missing-data warnings, and explicitly comparable structured observations. It must
disclose synthetic data, caps, invalid/unknown times, unverified external sources, and gaps.
It cannot claim a source was contacted, a source was proven true/false, an AFTER event preceded
the incident, a partial result covered the whole graph, or a connected deployment caused an
incident. Implemented [local AI tools](AGENT_TOOL_CONTRACT.md), [ingestion](INGESTION_CONTRACT.md)
and [evaluation](../evaluation/README.md) have separate contracts. External truth verification
and causal inference remain outside the implemented scope.
