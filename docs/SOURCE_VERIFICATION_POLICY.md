# Offline source integrity policy 1.0

No external authenticity service or remote source verification is implemented. Local byte checks
are independent of the unchanged investigation response and of application runtime/CI testing.

## Three independent questions

| Dimension | What is checked | What it does not prove |
| --- | --- | --- |
| Traceability | source/source_ref/time and actual incident-evidence-service graph edges | Factual truth, authenticity, or complete context |
| Content integrity | Exact local file bytes against an operator-supplied expected SHA-256 | Who authored the bytes or whether their claims are true |
| External truth/authenticity | NOT_PERFORMED | No authority, URL, account, certificate, or company has been consulted |

Matching an operator-provided checksum is **byte equality only**. A copied checksum inside an
untrusted JSON or beside an untrusted download is not an independently authenticated statement.
The operator must obtain the expected digest through an appropriate independent channel.
The bundled .sha256/manifest examples demonstrate reproducibility, not source authentication.

## Commands and output

```powershell
$expected = ((Get-Content ./fixtures/ingestion_example.sha256 -Raw) -split '\s+')[0]
python -m traceweaver verify-source --input ./fixtures/ingestion_example.json --expected-sha256 $expected
python -m traceweaver ingest --input ./fixtures/ingestion_example.json --database ./data/new-example.rl --expected-sha256 $expected --apply
```

Use a new scratch database for examples. Digest syntax is exactly 64 hexadecimal characters;
uppercase is accepted and normalized in the result. SHA-256 is calculated on raw bytes before
JSON decoding/parsing. Invalid JSON can still be byte-hashed; that is not valid ingestion.

Actual synthetic example, selected fields:

```json
{
  "integrity_contract_version":"1.0","algorithm":"SHA-256",
  "actual_sha256":"f8ffcadc2f56e6d5310efde8c764a46ebb400e5f90dd1d4b968332124c366303",
  "expected_sha256":"f8ffcadc2f56e6d5310efde8c764a46ebb400e5f90dd1d4b968332124c366303",
  "comparison_status":"MATCH","byte_equality_established":true,
  "external_verification_status":"NOT_PERFORMED"
}
```

Without an expected digest, comparison_status is NOT_CHECKED and byte_equality_established is
false; CLI exit 0 means hashing completed, not VERIFIED. Wrong digest is MISMATCH / exit 6.
Ingestion mismatch blocks before parsing or writer open. A digest inside the JSON is not read
as an expected digest; unknown contract fields are rejected.

## Local-file and privacy boundaries

- Only bounded regular local files are read. Inputs are at most 8 MiB.
- URLs, UNC/device paths, ambiguous drive-relative paths, alternate data streams, and symlink/
  reparse-point traversal are rejected. Windows supports local fixed drives; Linux supports
  recognized local mount types. Unknown filesystem classification fails closed.
- Files are checked before and after bounded descriptor reads for ordinary concurrent changes.
  This is a local operator boundary, not a sandbox against an adversary replacing filesystem
  components concurrently or forging filesystem metadata. Copy inputs to trusted local storage.
- HTTP/HTTPS/file source_ref strings are opaque graph metadata. They are never resolved, fetched,
  followed, or executed. No GitHub/cloud/network source connector or shell execution of payloads exists.
- Only Python JSON parsing and explicit typed admission are used; no pickle or executable object
  deserialization. Duplicate keys, non-finite constants, oversize/nested inputs are rejected.
- Structured error output contains safe codes/field locations and counts, never imported bodies,
  secrets, private paths, or tracebacks. There is no HTTP import route. Existing API errors stay safe.
- Non-demo/unknown-demo local data requires --allow-non-demo; this is intent, not authentication.
  Never commit such input files, audit records, or output stores to a public repository.

## Compatibility and generated artifacts

Sprint 01 provenance_status TRACEABLE/INCOMPLETE/INVALID and verification_status
SYNTHETIC/UNVERIFIED_EXTERNAL/NOT_AVAILABLE are unchanged. Import integrity lives in a separate
versioned result/manifest. It adds no fields to old investigation JSON and never promotes a graph
record to external VERIFIED. Envelope origin is a claim and cannot change a record's demo marker.

The judge bundle contains only the exact published synthetic fixture graph, with demo-only
references, bounded source/credential-pattern checks, and raw private-prefix checks. These are
limited checks, not a perfect secrets audit. Its file hash is recomputed after writers close.
Logical equality matters across rebuilds; native binary bytes need not match across platforms.
Future source access/authentication is **PLANNED**, requires a separate access policy and explicit
authorization, and must remain independent of content integrity and causal claims.
