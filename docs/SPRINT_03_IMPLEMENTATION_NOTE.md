# Sprint 03 implementation note

Recorded 2026-11-13 after the clean main audit and before substantive application code.
Baseline: 20bf4edf3a8e22417dc578e7d2b2e70c00d028af; 204 passed in 22.42s; Ruff/pip check clean.
Relate stays pinned to 1.0.0. Existing stores, judge bundle, fixtures, Sprint 02 gold/reports,
and test files are fingerprinted in an ignored local audit. Only the exact added OpenAPI route
assertion may change in an old test; no old assertion or behavior is weakened.

- Introduce strict explanation contract 1.0, independent of Investigation and ingestion schemas.
  Keep old investigation/query/temporal/provenance/contradiction code unchanged.
- Read one investigation using a single read-only worker-local connection, close it before any
  model request, then snapshot a deep copy. Fingerprint canonical full Investigation plus its
  effective options. Bind catalog/proposals to this fingerprint; claim IDs hash kind/stable
  entity identities, not iteration positions. IDs are stable but not authentication tokens.
- Build at most 128 admissible claims and render at most 10, with at most 12 citations per claim.
  Preserve catalog/selection/uncertainty/next-check omissions separately from graph truncation.
  Unsafe graph identifiers fail closed; source prose/properties and source references are withheld.
- A separate validator checks type-specific propositions, exact returned paths/edge directions,
  incident-scoped evidence, UTC/classes, comparison pairs and provenance. Controlled templates
  render only accepted facts. Caution is mandatory; no cause verdict or numerical confidence.
- Deterministic mode is entirely offline and explicitly not AI-generated. Insufficient evidence
  abstains while retaining scope and caveats. Missing onset prohibits before-onset claims.
- Ollama is CLI opt-in only. Fixed 127.0.0.1:11434 native tags/chat, no proxy/redirect/host option,
  no subprocess inference or download. Model sees opaque claim hashes and allowlisted metadata,
  never raw entity/source text, URLs, credentials, properties, or local paths. Strict bounded
  snapshot-bound JSON selection only; invalid output rejects, with no hidden fallback.
- Implement transport tests separately from genuine live-model evidence. Discover only existing
  local models. If none is available, finish Track A and adapter tests; Track B live inference is
  BLOCKED/NOT RUN and overall status PARTIAL. Do not install/pull a model without authorization.
- Author a separate frozen explanation suite from reviewed topology/rules before execution.
  Check semantic citations and adversarial rejection, actual Relate edges, no-cause/warning and
  abstention coverage, and honest truncation scope. Do not rewrite Sprint 02 gold or reports.
- Keep API deterministic-only and synchronous. Preserve numeric options, errors, thread affinity,
  existing JSON/exit codes. Add explicit model failure codes 12/13 and evaluation failure code 14.
- Use existing dependencies/stdlib; verify independent installed wheel and actual loopback HTTP.
  All evaluation writes go to new output paths; existing report overwrite needs explicit opt-in.

Official API references inspected before adapter implementation:
[Ollama chat](https://docs.ollama.com/api/chat), [installed models](https://docs.ollama.com/api/tags),
[structured outputs](https://docs.ollama.com/capabilities/structured-outputs).
The documented native chat request supports JSON-schema format and stream=false. Documentation
consultation is not external incident/source truth verification. Runtime remains local-only.
