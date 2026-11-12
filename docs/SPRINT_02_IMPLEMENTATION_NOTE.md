# Sprint 02 implementation note

Recorded after baseline audit, before implementation, 2026-11-13.

Baseline: clean main at eab9b308fc921ee5922449ebe73bd27e3d81d339; 119 tests passed,
Ruff and pip check passed. Existing store names, sizes, and hashes are recorded only in
the ignored .verification/sprint02 directory. Existing stores remain read-only.

- Keep the Sprint 01 investigation implementation, models, API, fixtures, and snapshots unchanged.
- Add ingestion contract 1.0 independently of demo fixture versions 1/2. Use strict typed envelope,
  allowlisted scalar properties and directed endpoints; retain missing/invalid event time strings
  with warnings. No dynamic timestamps, metadata coercion, or implicit synthetic/real conversion.
- Admit at most 8 MiB, 2,000 nodes, 4,000 edges, eight JSON container levels, and 4,096 UTF-8 bytes
  per property string. Reject duplicate JSON keys, non-finite constants, nested property containers,
  unknown fields, invalid types, dangling/duplicate relationships, and ownership inconsistencies.
- Use bounded local regular-file reads with SHA-256 calculated before parsing. Reject URLs,
  UNC/device paths, remote drives/mounts, and symlink/reparse traversal. Never follow source URLs.
- Reuse GraphStore.transaction and ensure_schema. Dry-run only opens an existing store read-only;
  --apply owns one finite writer. Batch identity preflight reads; ON CREATE SET and explicit
  comparisons preserve extra user properties. Conflicts roll back the whole transaction.
- Keep content integrity separate from metadata provenance and external truth. An expected digest
  is an operator argument, never trusted from the JSON body. Mismatch blocks apply before a writer.
- Author frozen gold expectations from known topology and temporal rules before executing the
  evaluation harness. Use curated synthetic fixture profiles and the unchanged investigate service
  on isolated real stores. Report exact denominators and undefined ratios as null.
- Emit canonical evaluation JSON without clocks, temp paths, durations, or random IDs. Bound
  outputs, validate graph edges in one real batch, and refuse report overwrite without opt-in.
- Build the judge artifact only from existing synthetic fixtures in a fresh temporary store.
  Verify exact logical contents, source-reference restrictions, actual read-only queries, and the
  closed store's bytes/hash. Permit --force only for a recognized, unchanged generated bundle.
- Add exactly one Git ignore exception and a binary attribute for the published synthetic .rl.
- No new runtime dependency, network source access, HTTP write route, AI, or causal inference.

## Observed implementation adjustments

Two initial new hash-preservation assertions exposed a native engine behavior: closing a
rolled-back writer can change physical .rl bytes while preserving committed nodes, edges and
constraints. The assertions were retained. Apply now performs a read-only conflict preflight
before writer acquisition, then rechecks after acquisition. A separate real-engine race test
observes early inserts and verifies full logical rollback when a conflict arrives after preflight.
No store-file restoration, deletion, weakened assertion, or simulated graph was used.

Ingestion retains the original eight-container limit. Evaluation admits 16 containers because
explicit expected graph paths require deeper nesting; both retain the 8 MiB raw-byte limit.
Gold-declared truncated scenarios are excluded from affected full retrieval metrics while still
gating returned-item fields, graph paths, and cap assertions. This avoids claiming full recall
for capped results. Frozen gold is unchanged after authoring.
