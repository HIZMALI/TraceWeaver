# TraceWeaver development rules

- Work on the existing `main` branch unless the user explicitly requests another branch.
- Preserve all existing user changes when changing branches or checkouts.
- Complete every sprint with meaningful tests using the real Relate embedded engine.
- Keep Relate as the actual data engine; never substitute a fake graph repository.
- Never delete user data, reset a graph, or remove stores without explicit authorization.
- Keep seed commands idempotent and preserve unrelated and conflicting user records.
- Parameterize user values in Cypher. Only allowlisted schema identifiers may enter query text.
- Support critical findings with sources and actual relationship paths.
- Mark demo records explicitly and keep them distinct from real incidents.
- Never hide failed tests with skipped assertions, fake results, or unearned PASS claims.
- Never state conclusions more strongly than the evidence supports. Connected deployments are
  candidates for investigation, not proven causes.
- Leave large features outside the current sprint for later sprints.
- Write code names, comments, README, and technical documentation in English.
- Communicate with the user in Turkish.
- Run Ruff and pytest before finishing. Report remote CI as unverified unless it actually ran.
- Use project virtual environments. Keep local databases and secrets outside Git.
- Keep seed writes finite and transactional. API connections must be read-only and must open,
  execute, and close in the same worker thread; Relate connections are thread-affine.
- Do not add runtime dependencies on the Relate CLI, paid services, API keys, or Docker.
- Normalize explicit-offset event timestamps to UTC and preserve originals. Missing, naive,
  invalid, or ambiguous times remain UNKNOWN; never substitute ingestion time or guess onset.
- Keep provenance quality separate from source truth verification. TRACEABLE is not VERIFIED.
- Compare contradictions only in structured, graph-grounded matching contexts and time windows.
- Keep causal_conclusion NOT_ESTABLISHED until a separately scoped inference contract exists.
- Bound graph reads and output lists, detect actual truncation with lookahead, and report gaps.
- Preserve the legacy fixture, API/CLI contracts, and existing tests. Add synthetic cases only
  with explicit opt-in import into isolated stores; never seed or migrate an existing user store.

## Sprint 02 integrity and evaluation rules

- Keep ingestion contract versions separate from demo fixture schema versions. Validate complete
  bounded batches before a writer; default to read-only dry-run and require explicit --apply.
- Reject known conflicts with a read-only preflight, then recheck under the single transaction.
  Preserve extra properties and ownership markers. Never claim physical byte rewind after native
  rollback: committed graph equality and file-byte equality are different guarantees.
- Require --allow-non-demo for false or unknown demo markers. Never commit private input/stores.
- Hash raw local bytes before parsing. Expected hashes must be supplied separately by the operator;
  matching checksums establish byte equality only. External verification remains NOT_PERFORMED.
- Never fetch source references or accept URL, UNC, device, remote-drive, or symlink/reparse input.
  Do not expose imported values, private paths, or raw validation bodies in tool/API errors.
- Keep evaluation gold explicit and frozen before execution. Use the unchanged investigation
  service on isolated real Relate stores, honest null denominators, and visible truncation scope.
- Keep canonical reports deterministic. Obtain explicit overwrite opt-in for generated reports.
- Publish only the exact synthetic judge-store Git exception. Verify manifest bytes and logical
  graph; --force applies only to recognized intact generated bundles, never user stores.
- Preserve all 119 Sprint 01 cases and the Sprint 02 ingestion/integrity/evaluation regression
  cases. Keep Python 3.11, other operating systems, and remote CI unverified until actually run.

## Sprint 03 explanation and local selection rules

- Preserve all 204 earlier cases/contracts, immutable judge bytes/manifest, fixtures and frozen
  Sprint 02 gold/reports. Only add the documented GET route to the exact OpenAPI route assertion.
- Consume the existing real graph-backed Investigation; do not create a competing graph analyzer.
- Keep explanations read-only. Close the worker-local store before optional model requests.
- Bind catalog and proposal to canonical Investigation/options fingerprint. Validate semantic
  support, exact candidate/evidence scope, actual paths/directions, UTC and comparison classes.
- Render factual statements only through controlled templates after validation. Always conclude
  with NOT_ESTABLISHED; preserve gaps, source status, truncation and insufficient-evidence abstention.
- Deterministic mode is offline and explicitly not AI-generated. HTTP explanation is always
  deterministic; no query parameter may enable inference.
- Optional CLI Ollama selects opaque claim IDs only at fixed 127.0.0.1:11434. Never send source
  prose, graph properties, raw entity IDs, URLs, secrets or private paths to a model.
- Never accept model-authored facts, citations, tools or Cypher. Reject invalid/duplicate/excessive/
  cross-snapshot selections and extra fields; do not repair hallucinations or hide a fallback.
- Never pull/install models automatically. Separate controlled provider protocol tests from actual
  live-model runtime evidence. If no real invocation succeeds, report Track B BLOCKED/NOT RUN and
  overall PARTIAL, while completing the offline track.
- Never persist prompts/raw provider responses. Preserve the actual model/demo status and expose
  only bounded safe failure codes. Hashes and traceability never establish source truth.
- Keep explanation gold explicit and reviewed, separate from Sprint 02 labels. Disclose any label
  correction with its independent rule/fixture basis; never generate expectations from outputs.
