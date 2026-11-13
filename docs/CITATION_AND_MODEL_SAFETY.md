# Citation firewall and optional model safety

Implemented safeguards are tested locally on real Relate. Provider protocol fixtures are
explicit controlled transports; genuine local-model evidence is reported separately. These
are local development safeguards, not a complete production security boundary or source audit.

The protocol below describes opaque claim selection. The separate experimental
[agent orchestrator](AGENT_TOOL_CONTRACT.md) adds five allowlisted read-only tools with opaque
subjects and stricter per-round budgets, while retaining the same final semantic firewall.

## Trust boundaries

1. Existing bounded parameterized Cypher produces one graph-backed Investigation. No source text
   is executed, no URL is followed, and no alternate fake repository answers the query.
2. Catalog construction uses allowlisted types, stable IDs and typed times/statuses. Full
   Investigation plus effective options is canonically fingerprinted, including source text
   that is not displayed or sent to a model. The hash binds bytes; it does not authenticate them.
3. The validator owns independent deep copies of source and catalog. It checks semantic
   prerequisites, exact current paths, directions, HAS_EVIDENCE scope, normalized temporal
   classes, comparison pairs/services and provenance. Mutable caller lists cannot alter its copy.
4. The model receives opaque claim hashes, allowlisted kinds/statuses and citation-kind names.
   **No raw graph entity IDs, full properties, logs, summaries, descriptions, signal prose,
   source references, private paths or credentials are included.** Hashes are not reversible
   identifiers by design, but this is data minimization rather than a confidentiality proof.
5. Only a strictly admitted selection reaches the validator. Controlled deterministic templates
   render the accepted factual statements. The model cannot create narrative claims/citations,
   issue Cypher, read files, invoke tools, change graph records or prescribe shell remediation.

Display-safe entity IDs are limited to a conservative ASCII identifier alphabet/length and
exclude credential-shaped prefixes. Unsupported identities produce safe errors. All source refs
and free-form source prose are withheld from explanation output, regardless of their apparent
safety. The existing Investigation contract remains unchanged and may contain raw metadata;
this new explanation policy does not silently retrofit older API behavior.

## Semantic checks

- Claim IDs must belong to this incident, catalog and snapshot; duplicates/count overflows fail.
- Exact path layout and stored directions are checked. TARGETS remains deployment-to-target,
  even when traversed in reverse. Similar paths, names or URLs cannot substitute for proof.
- Candidate target/time/UTC/class must agree with the original response and existing temporal
  classifier. Missing/invalid/naive onset cannot produce BEFORE. No ingestion-time substitution.
- Evidence requires the current incident's HAS_EVIDENCE. Shared-service evidence stays scoped.
- Structured comparisons use the unchanged actual matching service/signal/environment/overlap
  rules. Comparison proof follows that actual service even when evidence has several links.
  UNDETERMINED cannot be relabelled as CONFLICTING_OBSERVATIONS.
- Provenance quality is separate from source authenticity. TRACEABLE, SYNTHETIC, hashes and
  present source references never become external VERIFIED. External truth stays NOT_PERFORMED.
- Source truncation, evidence gaps and unknown metadata remain visible independently of selected
  claims. No-evidence context abstains. Causal conclusion remains NOT_ESTABLISHED.
- Forged statements and citations are rejected, never silently repaired with a plausible ID.
  The mandatory concluding caution is a declared selection invariant for otherwise valid IDs.

## Fixed native Ollama protocol

The opt-in CLI adapter follows the official [chat API](https://docs.ollama.com/api/chat),
[installed-model listing](https://docs.ollama.com/api/tags), and
[structured-output format](https://docs.ollama.com/capabilities/structured-outputs).
It uses only GET /api/tags and POST /api/chat at **127.0.0.1:11434**. No user host/URL option,
redirect following, environment proxy, authorization header, pull/install route or cloud SDK.

Model IDs are bounded and validated; an explicit exact installed name with positive local size
is required. Obvious cloud names/remote metadata are refused. A trusted local Ollama server and
locally provisioned weights are assumed; an adversarial daemon or renamed cloud proxy is not
authenticated by this client. The two native calls do not prove model or machine supply-chain
integrity. Model availability may change between listing and chat; failures stay explicit.

Chat uses stream=false, a strict JSON Schema in format, think=false, temperature=0,
num_predict=512 and num_ctx=8192. Model selection can still vary; no model byte-determinism claim.
The server must report the selected model, assistant role, done=true and a completed response.
Tool calls, truncation by token limit, unexpected message fields and bad content fail closed.
Native bounded metadata is discarded; only selected accepted facts/model ID enter the report.

Limits are in the explanation contract. Connect timeout is two seconds; read inactivity is
30 seconds; a monotonic 45-second deadline applies to socket reads, including header/body
reads through a deadline reader. Response bodies are capped at 64 KiB even without Content-Length;
stdlib HTTP header line/count bounds also apply. No retries or streaming partial results.
Connection refusal/connect timeout is MODEL_UNAVAILABLE; read timeout/invalid response is
MODEL_OUTPUT_REJECTED. Prompts and raw responses are never logged or persisted.

HTTP GET explanation cannot enable Ollama. Claim selection requires explicit CLI --mode ollama
and --model, or a confirmed local console POST described in the [dashboard contract](DASHBOARD_CONTRACT.md).
No automatic deterministic fallback, model download, memory store or graph mutation.
An accepted provider response labels ai_generated_selection=true; it does not label the factual
renderer as model prose. Controlled pytest transports do not establish a live model run.

## Tested attacks and limitations

Tests execute actual isolated Relate graphs and synthetic attack metadata: instructions to
declare DEP-001 a confirmed root cause, private-looking paths, internal-looking URLs, fake
credential shapes, line breaks and control characters. None reaches model packets or rendered
explanations. Socket guards establish deterministic/offline operation. Controlled loopback tests
exercise redirects, proxies, refusal, read timeout, oversized/malformed/partial bodies, incorrect
native envelopes, unknown/duplicate/cross-snapshot selections, extra fields and attempted tools.

The citation firewall establishes support by returned context, not incident truth, completeness,
root cause or a fix. The local HTTP API remains unauthenticated and loopback-bound. Row limits
are not resource quotas. Single-writer locks/thread affinity remain engine constraints. Native
writer rollback byte behavior from Sprint 02 is unchanged; explanation opens no writers.
Broader privacy review, hostile local-server isolation, model scheduling/cancellation, native RAM
quotas, production authentication and independent real incident adjudication remain future work.
