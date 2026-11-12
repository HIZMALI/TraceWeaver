# Architecture — Sprints 00 and 01

## Scope and boundaries

TraceWeaver is a local Python application embedding Relate 1.0.0. It has a finite writer
(the seed command) and read-only CLI/HTTP consumers. No server-side Relate process, paid service,
secret, Docker daemon, or model API is necessary. The Relate CLI is optional tooling.

## Components and data flow

1. `Settings` resolves `TRACEWEAVER_DATABASE`, defaulting to `data/traceweaver.rl` relative to
   the working directory. CLI `--database` takes precedence. Persistent paths require `.rl`.
2. `seed.load_fixture` reads the bundled synthetic JSON or an explicitly selected fixture.
   Pydantic validates labels, entity properties, timezone-bearing timestamps, unique fixture
   IDs, demo ownership, valid relationship endpoints, directions, and duplicate edges.
3. `GraphStore(..., read_only=False)` opens/creates the store. A single explicit transaction
   includes schema constraints, node `MERGE`, property conflict checks, and relationship `MERGE`.
   Node properties are set only on creation; existing records are never silently rewritten.
   Schema or graph errors trigger rollback. Closing also rolls back any uncommitted transaction.
4. The seed command computes actual node/relationship counts, commits, closes, and exits.
   It never clears existing data. An existing empty file can remain after failed import; it
   contains no partial fixture. The application never automatically removes that file.
5. CLI `stats`/`context` and API handlers open the existing store with `read_only=True`.
   `queries.py` executes parameterized Cypher. `models.py` validates and serializes the response.
   Neither HTTP endpoint nor query assembly reads JSON fixture data.

`fixtures/demo_incidents.json` is the reviewable source. Its packaged copy under
`src/traceweaver/fixtures/` is byte-equivalent JSON and allows installed-wheel seeding without
a checkout. A real test checks equality. Update both together when intentionally revising
the demo, and consider a versioned migration if an already imported record must change.

## Ownership, transactions, and preservation

IDs are unique within each node label through engine-enforced constraints, and globally unique
inside this fixture. A matching ID with different expected properties aborts the entire seed.
Unrelated labels, nodes, relationships, and additional properties are preserved. Extra externally
added properties are allowed to remain in storage but may fail the strict HTTP model contract.
No delete/reset query is used. Tests use fresh OS temporary files, never the default store.

Transaction rollback is tested in two ways: a seed collision after earlier fixture inserts,
and a real uniqueness violation after creating both nodes and a relationship. Both leave the
prior committed graph unchanged, including after close/reopen.

## Single-writer and thread-affinity decisions

The [official Python guide](https://relatedb.ai/docs/guides/embed/python/) specifies a
thread-affine connection (`threadsafety == 1`). A synchronous FastAPI handler creates,
executes, and closes its store inside one `with` block on one worker thread. There is no
shared global connection and no yielded dependency that could close on another worker.
Twelve concurrent requests across four callers are tested against the real engine.

The [two-process guide](https://relatedb.ai/docs/guides/operate/two-processes-one-store/)
distinguishes directory stores from `.rl` files. A `.rl` writer locks the entire file, blocking
readers in other processes too. The workflow is **seed to completion, then read**. API reads
are short-lived; stop API traffic before reseeding. The adapter does not hide lock errors,
delete lock files, or retry conflicting writes. A subprocess test checks the actual locked-store
failure. Read-only opens never create a missing store, checkpoint it, or modify file contents.

Each request opens a fresh read snapshot. Changes committed between requests can appear in
later responses; one response uses one connection. There is no live WAL following or write API.

## Query contracts

Statistics use real `count` aggregations. Incident lookup binds `$incident_id`. All list reads
use `LIMIT` (100 rows); dependency traversal uses `*1..3`, and deployment expansion uses
`*0..3` to include affected services themselves. The four-edge context query follows:

```text
Incident -AFFECTS-> Service -DEPENDS_ON-> Service <-TARGETS- Deployment -INCLUDES_CHANGE-> Change
```

The response includes stable IDs, source references, source names, timestamp strings, actual
dependency node sequences, relationship types, and bounds. `results_may_be_truncated` is true
when any context list reaches its limit, including the case of an exactly full list. This
conservative flag does not claim completeness. Incident listing is capped without pagination.

Context uses topology only. Deployments without changes and evidence without observed services
are outside the current retrieval shape. No time window, score, or causal assertion is inferred.
`TARGETS` remains directed Deployment → Service even when traversed backwards in a context path.

## Errors and security

`DatabaseUnavailable` wraps open, lock, read-only, and operational failures. `QueryError` wraps
query/constraint failures; chained causes retain diagnostics for terminal callers. The API
returns generic 503 messages for storage or incompatible graph data, and 404 for an unknown
incident. It does not expose a traceback, database path, or engine exception to an HTTP client.

All external values are parameters. Schema identifiers are interpolated only after validation
against fixed label/type mappings. API consumers cannot submit arbitrary Cypher. The CLI is a
local administrative tool, and error diagnostics can contain the path explicitly supplied by
its operator. There are no secrets in the fixture. `.rl`, `.env`, virtual environments, and
transient artifacts are ignored by Git. Keep Uvicorn bound to loopback: authentication and
production hardening are not implemented.

## Verification and evolution

Real-engine tests cover persistence in another process, idempotency, preservation, rollback,
constraints, topology, parameter attacks, HTTP failures, concurrent requests, and exact file
immutability after API reads. No mocked graph repository is used.

Sprint 01 adds the deterministic pipeline below. AI investigation remains planned. Keep the
real Relate engine and finite-writer/read-only-reader boundary until requirements justify changing it.

## Sprint 01 investigation pipeline

```text
API / CLI -> validated options -> one read-only worker-local GraphStore
  -> incident lookup + bounded candidate/evidence/affected-service Cypher
  -> batched change and observation edges (at most six queries)
  -> UTC classification + provenance audit + structured observation comparisons
  -> uncertainty/gaps, actual lookahead truncation, deterministic timeline
  -> shared Investigation Pydantic response -> JSON
```

`investigation_models.py` is separate from the original strict demo models. Invalid/missing
metadata can therefore be returned honestly without breaking legacy context validation.
`temporal.py` maps documented `timestamp` semantics to event times, preserves originals, and
normalizes explicit offsets to UTC. Explicit semantic fields override the legacy mapping;
`ingested_at` never supplies an event time. Comparisons use deltas to avoid date-boundary overflow.

Candidate discovery remains in Cypher: AFFECTS, zero to three DEPENDS_ON edges, then reverse
TARGETS. A simple-node-path predicate excludes cycles. A reducing minimum selects the shortest
lexicographically stable node sequence per deployment/target pair. Python formats that returned
sequence and the known matched edge directions; it does not traverse an in-memory adjacency map.
Change links and observations are fetched in two batches, not one query per candidate/evidence.
HAS_EVIDENCE always scopes observations, including when two incidents share a service.

All graph lists use LIMIT N+1. Candidate and evidence caps are user-configurable up to 100;
affected services, global change links, and global observation links have a cap of 100 each.
Timeline, findings, and contradictory/undetermined pairs are bounded separately. Missing auxiliary
links caused by truncation are not proof of absence, and their global truncation flags remain visible.
The legacy endpoint's original conservative limit behavior is unchanged.

`provenance.py` distinguishes TRACEABLE/INCOMPLETE/INVALID metadata from external truth verification.
Synthetic sources are SYNTHETIC; external references are UNVERIFIED_EXTERNAL. No links are fetched.
`contradictions.py` compares only valid structured same-service/signal/environment observations
with overlapping closed intervals. It never reads narrative keywords or infers a deployment cause.
At most 100 evidence records means at most 4,950 potential pairs; audit counts cover the returned
evidence even if only the first 100 matching pairs are returned.

The version-2 demo fixture deliberately permits malformed/missing metadata specimens while
enforcing labels, stable identity, demo ownership, directions, and relationship endpoint validity.
It uses the same transaction/conflict-safe importer. The original version-1 fixture remains strict
and unchanged. Additional cases are imported only through an explicit --fixture option into an
operator-selected store. No migration, startup seed, new dependency, or default-store write exists.

HTTP handlers remain synchronous. Expected store failures are generic 503, unknown incidents 404,
invalid request arguments 422, and unexpected errors generic 500 with server-side logging.
The same investigation function and response model serve CLI and HTTP; tests compare exact JSON.
Full legacy response snapshots were captured using real Relate and commit e504012's source.
