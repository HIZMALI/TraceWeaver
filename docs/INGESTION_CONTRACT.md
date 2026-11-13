# Local ingestion contract 1.0

Implemented with relate-db 1.0.0; native tests ran locally on Windows/Python 3.14 and in hosted
Windows/Ubuntu Python 3.11 CI. This is offline local tooling,
not an HTTP ingestion API, production connector, or source-authentication service.

## Entry points

```powershell
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database ./data/new-example.rl
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database ./data/new-example.rl --apply
```

Choose a new scratch path for examples. The first command is **DRY_RUN** and never creates a
store/directory. Only `--apply` writes. `--database` is required; there is no implicit default
target for ingestion. Existing fixture `seed` contracts (schema_version 1/2) are unchanged.

The complete valid [synthetic example](../fixtures/ingestion_example.json) has eight nodes and
nine relationships, including a four-edge incident/dependency/deployment/change path and two
explicitly conflicting structured observations. Its SHA-256 illustration is stored separately
in `fixtures/ingestion_example.sha256`. An adjacent checksum is not authenticated source identity.

## Document

The top-level fields are `contract_version: "1.0"`, `dataset_id`, `source`, `nodes`, and
`relationships`. Unknown fields, versions, duplicate JSON keys, and non-finite constants are
rejected. All identifiers and strings remain exact; the importer does not trim/coerce values.

`source` requires `source_id`, `kind: "LOCAL_EXPORT"`, `declared_origin`, `captured_at`, and
`description`. Origin is SYNTHETIC, NON_SYNTHETIC, or UNKNOWN: an input claim, not authenticated
identity. Capture time must be a valid explicit-offset timestamp; it is never used as event time.
The source envelope is returned as audit metadata, excluding free-form description. It is not a
persistent registry of intake claims and does not replace evidence source/source_ref properties.
Header-only changes do not rewrite graph records; independently pin the exact input digest when
byte identity matters.

Each node has `label`, stable `id`, and a `properties` object whose `id` must match. Each edge
has `type`, `source: {label,id}`, and `target: {label,id}`. All endpoints must be declared in the
same batch. Identity is `(label,id)`; duplicate identities and duplicate type/endpoint edges fail.

Only the existing six labels and seven directed relationship types are supported:

| Type | Stored direction |
| --- | --- |
| AFFECTS | Incident → Service |
| DEPENDS_ON | Service → Service |
| TARGETS | Deployment → Service |
| INCLUDES_CHANGE | Deployment → Change |
| HAS_EVIDENCE | Incident → Evidence |
| OBSERVED_ON | Evidence → Service |
| RAISED_FOR | Alert → Incident |

Names that affect Cypher syntax come only from these fixed mappings; all values, IDs, lists,
and properties are bound parameters. No imported content is executed as shell, Python, or Cypher.

## Properties and ownership

Common required fields: `id`, `dataset_id`, nonempty `environment`. `demo` is a strict boolean
or null/absent. Every node's dataset_id must equal the envelope dataset_id. IDs/dataset IDs are
nonempty, trimmed, without control characters, and at most 128 UTF-8 bytes.

| Label | Additional required display/source properties |
| --- | --- |
| Incident | title, summary, severity, status |
| Service | name, description |
| Deployment | name, description, source, source_ref |
| Change | name, description, source, source_ref |
| Evidence | summary, description |
| Alert | name, severity, source, source_ref |

Required display/source fields must be nonempty strings. Evidence source/source_ref may be
missing/null/empty so incomplete observations remain visible in investigation. Invalid property
types are rejected, rather than stringified into apparently valid metadata. Unknown properties,
including unapproved inferred-cause fields, are rejected. Property containers/arrays are not
accepted. Only strings, an optional boolean demo marker, and admitted null metadata are supported.

Allowed extras are existing per-label properties plus the documented Sprint 01 semantic time,
ingested_at, and Evidence structured-signal/window fields. `observed_state`, when present, is
HEALTHY/DEGRADED/FAILED/null. Supplied Evidence service_id must have a matching OBSERVED_ON edge
inside the batch. No numeric threshold, signal-name normalization, or unit inference is applied.

SYNTHETIC requires every node demo=true. NON_SYNTHETIC requires every node demo=false. UNKNOWN
does not silently assign a demo marker. Any false/missing/null demo marker requires the additional
`--allow-non-demo` flag, including dry-run. This is a local intent guard, not access control.
No actual private/non-demo dataset is needed or committed for tests.

Relationships receive dataset_id and a derived demo marker: false if either endpoint is false,
unknown if an endpoint is unknown, otherwise true. There is no arbitrary incoming edge-property
syntax. Existing extra user properties survive; conflicting expected values/types/ownership abort
the batch. In particular, integer 1 is not treated as boolean true for conflict checks.

## Times and data quality

Event timestamp fields are optional strings/null. Explicit-offset valid text is preserved
verbatim. Missing/invalid/naive strings are retained, with bounded intake warnings, and the
unchanged investigation service classifies them UNKNOWN. Epoch numbers or other invalid property
types are rejected at admission. Partial/invalid observation windows remain non-evaluable in
structured comparisons. See [the investigation contract](INVESTIGATION_CONTRACT.md).

No event time is filled from `captured_at`, `ingested_at`, or the current clock. Ingested_at is
accepted only as explicitly supplied metadata; no dynamic wall-clock fields are generated.
COMMITTED/VALIDATED status means admission/commit state, not complete evidence or factual truth.

## Limits before writer admission

| Limit | Value |
| --- | ---: |
| Input bytes | 8 MiB, inclusive |
| Nodes | 1..2,000 |
| Relationships | 0..4,000 |
| JSON container depth | 8 levels |
| Property/source-description string | 4,096 UTF-8 bytes |
| Identity string | 128 UTF-8 bytes |
| Nested property containers | Not admitted |
| Returned intake warnings | 100, with actual overflow flag |
| Returned validation details | 20, with total error count and overflow flag |

Input is a UTF-8 JSON object without a BOM, pickle, executable callbacks, or raw unbounded log
bodies. Byte count, JSON admission, full model/domain validation, digest mismatch, and non-demo
guard all precede writer open. Input is never silently truncated.

## Dry-run, apply, and transactions

Dry-run validates the full file. If the target exists, it opens read-only and checks bounded
batch identities and compatibility. It never installs constraints, creates directories/stores,
checkpoints, or commits. An unavailable/locked existing store is an error, not a guessed preflight.

Apply first rejects known conflicts using read-only preflight. It then closes that reader,
opens one writer, starts an explicit transaction, installs existing ID constraints if needed,
reads current identities again, and uses parameterized MERGE/ON CREATE SET. Every matched node
and relationship is checked again. A late conflict or failure rolls back all transaction writes;
there is no overwrite, delete, reset, migration command, or lock removal. Unrelated data survives.

**Observed Relate limitation:** closing a writer after rollback can change physical .rl bytes
despite identical committed graph/constraints. The importer does not restore files manually.
Known conflicts are rejected before writer open, preserving their SHA-256. A controlled race test
commits a conflicting user change between preflight and writer acquisition, observes real early
inserts, then verifies those inserts/constraints roll back while that user change survives.
Logical atomicity is guaranteed by the tested engine transaction; physical byte rewind after
a writer has opened is not promised. Existing workspace stores were never written in development.

Reads are batched by label/type (at most 6+7 queries per preflight stage). Writes are finite and
per-record. Admission limits are not a total-store RAM cap or execution-time guarantee.

## Results and errors

Successful JSON includes version, dataset_id, source_claim, integrity, mode, status, committed,
preflight, input_counts, counts, actual graph_counts when available, warnings/overflow, and
external_verification_status=NOT_PERFORMED. No raw imported body or source description is logged.

Actual example counts:

```json
{
  "mode":"APPLY","committed":true,
  "counts":{"nodes_created":8,"relationships_created":9,"nodes_already_present":0,
            "relationships_already_present":0,"nodes_rejected":0,"relationships_rejected":0,
            "nodes_would_create":0,"relationships_would_create":0},
  "graph_counts":{"node_count":8,"relationship_count":9}
}
```

Second/third apply have created=0, already-present=8/9, totals=8/9. These are batch identity
counts verified inside the transaction, not guessed graph-engine mutation counters. Dry-run
created=0 and would-create counts are projections of its read snapshot. Missing-store totals
are null. Rejected counts describe the whole uncommitted batch where its size is known; unknown
totals are null. Commit acknowledgement is distinguished from a subsequent close/I/O failure.

| New command exit code | Meaning |
| --- | --- |
| 0 | Operation completed; NOT_CHECKED is still not a verified digest |
| 1 | Local/engine/report I/O or unexpected operation failure |
| 2 | CLI argument syntax |
| 4 | Contract/admission/report-path validation |
| 5 | Existing identity/property/ownership conflict |
| 6 | Expected SHA-256 mismatch |
| 7 | Non-demo/unknown-demo opt-in missing |
| 8 | Unsafe/unsupported local path or non-regular input |
| 9 | Missing input file |
| 10 | Locked Relate store |
| 11 | Evaluation expectations failed/case execution failure |

Old commands retain their original 0/1/2/3 semantics. New structured errors omit body values,
private paths, and tracebacks. There is no new HTTP endpoint or reinterpretation of Sprint 01
provenance/verification statuses. The strict legacy context model still rejects unsupported
new structured/real-data properties; use investigation for the richer ingestion contract.
