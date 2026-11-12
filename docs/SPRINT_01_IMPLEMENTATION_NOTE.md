# Sprint 01 implementation note

Recorded after the baseline audit and before implementation, 2026-11-12.

Baseline: clean `main` at `e504012`; Python 3.14.0, relate-db 1.0.0; 37 tests pass,
Ruff passes, pip check passes. Existing store counts are 21/27. Its SHA-256 is recorded
in the ignored local verification directory; all existing stores will remain read-only.

## Contract decisions

- Keep legacy context/entity models and the baseline fixture intact. Add tolerant investigation
  response models, without interpreting missing or malformed source timestamps as UTC.
- Map the existing documented `Incident.timestamp` to incident onset, `Deployment.timestamp`
  to rollout time, and `Evidence.timestamp` to observation time. Preserve raw values and expose
  normalized UTC separately. Explicit semantic fields, if present, take precedence even when
  invalid; never fall back to an ingestion timestamp.
- Discover deployment/target pairs through Cypher, bounded to three dependency hops. Select
  one deterministic shortest simple graph path per pair, retaining actual IDs and directions.
  Batch changes and incident-scoped evidence observations; retain orphan deployments/evidence.
- Apply integer window validation and closed/open boundaries exactly as requested. Only BEFORE
  deployments can have INVESTIGATE status; this conveys temporal suitability, not causation.
- Separate mutually exclusive provenance quality from unverified external-source metadata.
  Compare only structured, graph-grounded, same-incident/service/signal/environment observations
  with overlapping explicit intervals or equal observation instants.
- Use one read-only investigation service for API and CLI. Fixed list caps and N+1 lookahead
  detect truncation; report it alongside uncertainty and missing-data gaps.
- Extend the existing transactional conflict-safe importer with an explicit version-2 synthetic
  fixture format for malformed/missing metadata specimens. Version 1 remains strict. No migration,
  automatic additional seed, graph reset, new dependency, or existing-store write is planned.
- Preserve all 37 original tests. The exact OpenAPI route-set assertion must include the fourth
  GET route; retain all previous assertions and verify the expanded exact set.
- Verify new behavior on OS temporary real Relate stores, including cycles, truncation, unknown
  anchors, incomplete evidence, additive import rollback, CLI/HTTP parity, and byte immutability.

AI inference, root cause decisions, remediation, production access, and a UI remain planned.
