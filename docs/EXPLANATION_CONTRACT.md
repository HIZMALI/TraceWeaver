# Explanation contract 1.0

Implemented locally on real Relate 1.0.0. This adds a separate strict response; legacy context,
Investigation, ingestion, fixture and source-integrity contracts are unchanged. Native tests run
on Windows/Ubuntu Python 3.11 in [CI](https://github.com/HIZMALI/TraceWeaver/actions/workflows/ci.yml).
Controlled provider tests are separate from live-model evidence; the optional runtime is experimental.

## Entry points

```powershell
python -m traceweaver explain --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver explain --incident CASE-INC --database ./examples/judge-demo/traceweaver-demo.rl --mode deterministic
python -m traceweaver explain --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl --mode ollama --model qwen3:8b
```

The third command requires that exact model already installed in a running local Ollama service;
use an actual installed local model ID. It never downloads or installs one. Deterministic is
the default and is explicitly **not AI-generated**. Optional model mode selects/orders claim IDs;
it does not generate the displayed factual prose.

`GET /incidents/{incident_id}/explanation` is deterministic-only. Accepted numeric options match
Investigation exactly: pre_minutes/post_minutes integers 0..1440, defaults 120/30; max_candidates/
max_evidence integers 1..100, default 100. CLI uses equivalent hyphenated flags. HTTP has no
mode, provider, host or model parameter; supplying unrelated query keys cannot enable inference.
The shared service opens, queries and closes one read-only store in one synchronous worker.
The store is closed before any optional provider request.

## Response

ExplanationReport has strict types, extra=forbid and contract_version="1.0". Its execution
validator rejects contradictory provider labels, counts, missing final caution and invalid
provenance totals. Nested mutable input is deep-copied before selection/validation.

| Field | Meaning |
| --- | --- |
| incident_id / is_demo | Exact source identity and actual boolean/null demo status |
| mode_requested | DETERMINISTIC or OLLAMA |
| mode_executed | DETERMINISTIC, accepted OLLAMA, or NONE on model failure |
| ai_generated_selection | True only after a provider response is accepted; describes selection only |
| model | Accepted provider OLLAMA_LOCAL and actual model_id; otherwise null |
| explanation_status | EXPLAINED, PARTIAL_CONTEXT, ABSTAINED, MODEL_UNAVAILABLE, MODEL_OUTPUT_REJECTED |
| investigation_status | Unchanged READY_FOR_REVIEW / PARTIAL_CONTEXT / INSUFFICIENT_EVIDENCE |
| causal_conclusion | Literal NOT_ESTABLISHED, including failures |
| investigation_fingerprint | SHA-256 of canonical full returned Investigation plus effective window/caps |
| overview / claims | Controlled templates and semantically validated proof objects |
| evidence_summary | Counts from returned Investigation/audits, never global-graph totals |
| uncertainties | Actual gap/limitation/evidence warning codes, entity references and counts |
| next_checks | Safe bounded subset of actual Investigation.next_checks, without invented remediation |
| limitations / demo_notice | Source truth, scope/model constraints and actual synthetic/unknown/non-demo notice |
| truncation | Exact investigation flags plus independent explanation omission indicators |
| catalog_claim_count / generated_claim_count | Admitted bounded catalog versus total generated propositions |
| validated_claim_count / validated_citation_count | Actual rendered accepted items, enforced against lists |
| rejection_codes | Bounded safe reason codes, no raw model/source body or private path |
| external_verification_status | NOT_PERFORMED |

EXPLAINED means the source is READY_FOR_REVIEW and a useful selection was accepted. It is not
authentication or causal certainty. Source partial context maps to PARTIAL_CONTEXT. No returned
evidence causes ABSTAINED; accepted model abstention also causes ABSTAINED. Available scoped
facts/caution may remain, without inventing evidence. Model unavailable/rejected yields NONE,
no claims, no model metadata, and no disguised deterministic fallback.

Canonical actual complete examples:
[INC-001](examples/INC-001-explanation.json), [CASE-INC](examples/CASE-INC-explanation.json).
Both are generated through the actual read-only service and checked for exact equality in tests.
Their current source incidents are PARTIAL_CONTEXT; the no-evidence fixture abstains.
Uncertainties retain one actual source finding per code, prioritizing investigation gaps/
limitations over a repeated evidence warning. Each count belongs to that finding, not an
invented aggregate over repeated warning instances. Full evidence category totals are in
evidence_summary; per-record warning details remain in the unchanged Investigation contract.

## Claims and citation semantics

Each claim contains claim_id, claim_type, statement, referenced_entity_ids, citations, and
support_status=SUPPORTED_BY_RETURNED_CONTEXT. IDs are C- plus the first 24 SHA-256 hex characters
of canonical kind + stable entity identities + an optional gap-code qualifier. IDs remain stable
across iteration changes; the separate full snapshot fingerprint prevents cross-snapshot reuse.
Neither hash is an authentication credential.

Allowlisted types: INCIDENT_OBSERVED, SERVICE_AFFECTED, DEPLOYMENT_CONNECTED,
DEPLOYMENT_BEFORE_ONSET, DEPLOYMENT_NOT_PRECEDING, EVIDENCE_REPORTED, STRUCTURED_CONFLICT,
COMPARISON_UNDETERMINED, SOURCE_UNVERIFIED, CONTEXT_GAP, NO_CAUSAL_VERDICT.

- Connected claims require the exact candidate/target path. BEFORE requires actual normalized
  time and inclusive-window classification; AT_ONSET/AFTER cannot be a preceding trigger.
  UNKNOWN and OUTSIDE_WINDOW do not create a preceding-time proposition.
- Evidence must belong to this incident through HAS_EVIDENCE. Shared service, reference or text
  cannot import another incident's evidence. Orphans keep only their actual incident-evidence path.
- Conflicts/undetermined refer to an actual pair and exact classification/overlap. The proven
  comparison function independently rechecks structured comparability. Comparison citations also
  name the actual matching service and its OBSERVED_ON paths, including multi-service evidence.
- The final claim in every accepted explanation is NO_CAUSAL_VERDICT. A valid model can reorder
  optional IDs, but cannot remove that caution. This declared invariant is not hallucination repair.

Citation kinds are INCIDENT, EVIDENCE, GRAPH_PATH, TEMPORAL, PROVENANCE, CONTRADICTION and GAP.
Graph paths carry ordered node_ids and stored type/source_id/target_id/traversal_direction.
TARGETS is stored deployment-to-service and traversed REVERSE. A citation must exactly match
returned facts; existence of a similar ID is insufficient. Temporal citations retain normalized
UTC and class; provenance retains TRACEABLE/INCOMPLETE/INVALID independently of
SYNTHETIC/UNVERIFIED_EXTERNAL/NOT_AVAILABLE.

**All source references and source prose are withheld in version 1.0**, including safe demo refs.
Citation source_ref is always null; source_ref_withheld reports presence of a supplied value.
Stable evidence/path IDs provide proof without revealing source URLs, local paths or credentials.
No generated narrative is treated as corroborating evidence. Unsafe display identifiers fail
closed rather than being copied or silently renamed into invented graph identities.

## Bounds and deterministic scope

| Boundary | Limit |
| --- | ---: |
| Canonical input Investigation + effective options | 8 MiB |
| Admitted catalog | 128 claims, balanced round-robin by type; actual generated count retained |
| Rendered claims | 10 maximum, fewer when fewer admissible claims exist |
| Citations per claim | 12 maximum |
| IDs / path | 128 characters per safe ID, up to 7 path nodes / 6 edges |
| Statement / overview | 1,024 / 2,048 characters |
| Uncertainties | 20 entries; 12 entity refs each; actual count and omitted-reference flag |
| Next checks | 8 entries, 512 characters each; omissions/unsafe exclusions flagged |
| Limitations / rejection codes | 12 / 8 entries |
| Model proposal | 4,096 UTF-8 bytes, four JSON container levels, 8 selected IDs |
| Model packet / native request | 32 KiB canonical packet / 48 KiB request body |
| Native response body | 64 KiB; JSON depth eight |

Investigation has its exact original eight flags. Explanation adds catalog, selected_subset,
uncertainties, next_checks, model_offer. selected_subset means a curated subset was presented,
not that the graph query was truncated. A large model packet offers the first 64 balanced catalog
entries if needed and flags model_offer. No truncated report claims all candidates/evidence.
Row/output caps do not bound native store RAM, query work, or full-property materialization.
No clocks, randomness, machine paths, timing metrics or provider prose enter deterministic output.

## Errors and local model proposal

HTTP: 200 valid scoped/abstained report; 404 unknown incident; 422 invalid numeric arguments;
503 unavailable/locked/corrupt/incompatible context; unexpected 500 is generic. No write route.
Existing CLI codes are unchanged. New explain: 0 completed deterministic/accepted selection
(including explicit abstention), 1 safe storage/config failure, 2 argument syntax, 3 unknown
incident, 4 admission error, 12 model unavailable, 13 model output/selection rejected.
New evaluate-explanations exits 14 on false gold; malformed suite/report paths use safe ToolError.

The model proposal has exactly investigation_fingerprint, selected_claim_ids, focus and abstain.
focus is TIMELINE/DEPENDENCIES/EVIDENCE/GAPS/BALANCED. Non-abstention selects 3..8 offered IDs
(fewer only if fewer than three are available). Abstention selects none. Duplicate/unknown/excess
IDs, wrong snapshot, extra fields, causal verdicts, fabricated URLs/citations/tools and malformed
JSON are rejected. Raw output is never returned, logged or committed. See the
[safety policy](CITATION_AND_MODEL_SAFETY.md) for native provider transport and trust assumptions.
