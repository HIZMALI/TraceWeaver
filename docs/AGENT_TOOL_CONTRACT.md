# Agent investigation 1.0

New strict DTOs leave Investigation, ExplanationReport and legacy CLI/API output unchanged.
Requests contain incident_id, exact options, source_fingerprint, one of four fixed intents,
confirmed=true and (AI only) an eligible installed model_id. No prompt/query/path/URL is accepted.

## Source and actual tools

Source creation runs unchanged investigate and native label audit in one worker-local read-only
connection, then closes. Canonical Investigation/options fingerprint and exact local file SHA-256
bind all steps. Existing regular-local-file guards and an 8 MiB digest cap fail closed. The cap
does not bound native whole-graph RAM/work. Before/after tools and final admission the digest
must match, or STALE_SNAPSHOT aborts without mixing proof.

| Fixed tool | Subject handle | Actual native operations |
| --- | --- | --- |
| get_incident_scope | I000 | Incident lookup and AFFECTS neighbors, directed paths and sanitized onset |
| trace_deployment | D000… | Exact admitted deployment/target pair; bounded AFFECTS/DEPENDS_ON*0..3/reverse TARGETS native query, INCLUDES_CHANGE and edge audit |
| inspect_evidence | E000… | Incident HAS_EVIDENCE and optional OBSERVED_ON neighbors; existing UTC/provenance rules; orphan path retained |
| compare_observations | P000… | Both native memberships/neighbors; existing service/signal/environment/window comparison rules; conflict and UNDETERMINED separate |
| inspect_gaps | I000 | Fresh native investigate with exact options; existing gap codes and bounded representative paths, no remediation inference |

Every tool executes fresh parameterized Cypher, not cached JSON indexing. Snapshot validates
subjects/equality; native queries supply result facts. Distinct edge type/source/target triples
are rechecked natively. Only returned source scope is exposed even if direct reads see more.
Arguments are strict `{"subject":"D001"}` opaque handles, never model-supplied schema identifiers.
Offers contain at most eight pairs, eight evidence and five comparison pairs, each fingerprint-
scoped. Provider messages use opaque node handles N000…; the public trace maps subjects to safe IDs.

Each tool admits at most eight queries, eight complete paths (six edges each), eight time/provenance
records, one comparison, twenty codes, 64 identities and 64 KiB. No raw source body/reference is
returned. DisplayTime retains safe originals or explicit withholding; provider packets use UTC/enums.

## Output and invariants

AgentInvestigationReport version 1.0 includes source/database fingerprints/options/intent, actual
requested/executed model, consecutive native trace, directed paths/time/provenance, existing typed
validated claims, exact citation count, caps/gaps, safe codes and real measured elapsed_ms.
NOT_ESTABLISHED / NOT_PERFORMED and a controlled no-cause statement are permanent. TRACEABLE and
digest equality are not source authentication. Unknown times remain unknown.

canonical_agent_payload explicitly excludes elapsed_ms and canonical_fingerprint recursively.
Evidence timestamps remain included. Rehearsal equality uses this projection; measured durations
are never fabricated as zero and the current clock never becomes evidence time.

## Orchestration boundary

At most four executed calls / five model chat interactions / one call per round, no retries.
No native connection survives a provider request or crosses threads. Fixed native Ollama
127.0.0.1:11434 only; no cloud/installation/pull. Model input is opaque handles/claim IDs, fixed
tool names and bounded enums/counts/UTC. No narrative source/model prose is accepted as fact.

Final claim IDs pass the existing semantic citation firewall plus actual retrieved-support
coverage. No-tool proposals are MODEL_SELECTION_ONLY, never AI-directed tool evidence. Provider
failures preserve offline usability without a hidden AI fallback. Controlled protocol tests are
separate from genuinely observed live-model calls.

Explicit local actions reuse exact Host/Origin/port and bounded-body checks plus one in-flight
lock. GET/load/refresh never infer. Offline DETERMINISTIC_TOOL_REHEARSAL uses the identical real
tools with both AI flags false. Client abort need not stop daemon computation. Final request/total
budgets and actual observed availability are documented with the orchestration gate and report.
