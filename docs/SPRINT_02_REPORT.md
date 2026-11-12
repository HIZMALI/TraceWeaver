# Sprint 02 verification report

Date: 2026-11-13. Overall: **PARTIAL — local verification complete; final Git delivery pending**.
All implementation and verification below are actual local results, using embedded Relate.
Remote CI, Python 3.11 and Ubuntu runtime are **UNVERIFIED / NOT RUN**. External source truth
verification is **NOT_PERFORMED**. AI integration is **PLANNED**.

## Baseline and preservation

- Initial clean `main`: `eab9b308fc921ee5922449ebe73bd27e3d81d339`.
- Sprint 01 implementation `aec6d72017df8ae478ed0e06f495f80770771d59` remains in history.
- Baseline command results: **119 passed in 11.71s**, Ruff clean, pip check clean.
- All twelve original test files remain byte-equivalent after line-ending normalization. All
  119 original cases still pass; no old assertion, test, fixture, snapshot, or response contract
  was removed, skipped, or weakened.
- Existing API, investigation/model, temporal/provenance/comparison, queries, storage/seed/schema,
  baseline and Sprint 01 fixtures, pyproject, dependency lock, and CI workflow are unchanged.
- The ignored local audit records initial store names, sizes and hashes; it is outside Git.
  No existing store was opened for writing, seeded, reset, migrated, moved, or deleted.

| Existing store | Bytes before / after | SHA-256 before / after | Actual graph |
| --- | --- | --- | --- |
| data/traceweaver.rl | 73,728 / 73,728 | `3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3` / same | 21 nodes / 27 relationships |

Store immutability was checked by session-level regression guards and the final independent
audit, including another read-only real count query. No absolute private path is published here.

## Delivered architecture and files

| Area | Files and purpose |
| --- | --- |
| Ingestion | `ingestion_models.py`, `ingestion.py`: independent strict 1.0 contract, read-only compatibility preflight, explicit transactional apply |
| Local bytes/integrity | `local_files.py`, `source_integrity.py`, `tool_errors.py`: bounded regular local reads, raw SHA-256, safe structured errors |
| Evaluation | `evaluation_models.py`, `evaluation.py`, frozen `evaluation/cases.json`: unchanged investigation service over isolated real stores |
| Judge artifact | `judge_demo.py`, `examples/judge-demo/traceweaver-demo.rl`, manifest and rebuild README |
| CLI | Four new offline commands dispatched separately from existing Settings/error contracts |
| Synthetic resources | Ingestion example and separate .sha256; evaluation/cap fixtures and identical packaged copies |
| Regression checks | Four new test files, 85 additional cases, actual-engine transactions and graph paths |
| Documentation | Ingestion/source/signal/evaluation contracts, implementation note, walkthrough, this report, evaluation/bundle READMEs, root README and appended AGENTS rules |
| Git packaging | One exact .rl ignore exception and binary attribute; actual JSON/Markdown evaluation reports |

All module paths above are under `src/traceweaver` unless another directory is shown. No new
runtime dependency, network connector, HTTP write endpoint, AI model, or cause-scoring system
was introduced. Existing connection ownership and GraphStore.transaction are reused.

## Ingestion and actual end-to-end results

Contract 1.0 is distinct from fixture schema versions 1/2. Six labels and seven stored edge
directions are allowlisted; all imported values are Cypher parameters. Admission rejects unknown
fields/versions/types, duplicate keys/identities/edges, dangling or incorrectly directed endpoints,
dataset/demo inconsistencies, nested property values, and unapproved structured states.

Limits: **8 MiB**, **2,000 nodes**, **4,000 relationships**, eight JSON containers,
4,096 UTF-8 bytes/property string, 128 bytes/identity. Intake warnings are capped at 100 with
overflow; validation details at 20 with full error count and overflow. No silent batch truncation.
Event strings are preserved; missing/invalid/naive times remain unknown. No current-clock or
ingestion-time event fallback is inserted. Unknown/non-demo markers require --allow-non-demo,
including dry-run; source origin is an untrusted declaration, not authenticated identity.

Actual CLI execution on a new OS temporary store, documented in the walkthrough:

| Operation | Result |
| --- | --- |
| verify-source with separate expected SHA-256 | MATCH; external NOT_PERFORMED; exit 0 |
| ingest without --apply | DRY_RUN, committed=false, would-create 8/9, totals null; no store/directory created |
| First --apply | Created 8 nodes / 9 edges; already present 0/0; actual totals 8/9 |
| Second --apply | Created 0/0; already present 8/9; totals 8/9 |
| Third --apply | Created 0/0; already present 8/9; totals 8/9 |
| investigate ING-INC-001 | Actual incident/API/dependency/deployment/change path; one structured conflict; NOT_ESTABLISHED |
| Changed duplicate summary in new input | INGEST_CONFLICT, exit 5; file hash and counts unchanged |
| Wrong expected digest | SOURCE_DIGEST_MISMATCH, exit 6; before parse/writer; hash unchanged |
| Locked scratch store | GRAPH_STORE_LOCKED, exit 10; no forced retry or lock deletion |

Actual source SHA-256:
`f8ffcadc2f56e6d5310efde8c764a46ebb400e5f90dd1d4b968332124c366303`.
NOT_CHECKED, MATCH and MISMATCH are separately tested. The CLI warns that matching an operator
digest proves byte equality only. The bundled separate checksum illustrates the argument channel;
being stored beside an example does not authenticate it. External references are never fetched.
Intake source claims are returned separately, not persisted as an authenticated source registry.

### Transaction finding and correction

The first run of new tests reported **2 failed / 198 passed**: Relate changed physical store
bytes when a rolled-back writer closed, although committed graph contents were unchanged.
Those two SHA assertions were retained. A read-only existing-store preflight now rejects known
conflicts before opening a writer; apply then rechecks under its transaction to handle races.

A separate real-engine controlled-race test commits a conflicting synthetic user node after
preflight, observes the early incident insertion in the actual transaction, and then verifies
full logical rollback of imported nodes/edges/constraints while the racing user change survives.
All graph operations execute on real Relate; no graph response is fabricated. Existing extra
properties, unrelated records, dataset ownership and exact demo types are preserved.

**Remaining engine limitation:** physical byte rewind after writer acquisition is not promised.
We do not restore backup bytes or replace user stores. Known conflicts and digest failures do
preserve SHA-256 without opening a writer. The user's pre-existing workspace store was untouched.

## Frozen evaluation and actual metrics

Gold was explicitly authored from topology and temporal/comparison rules before runner execution.
It has not been regenerated from runtime output. Frozen suite SHA-256:
`6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8`.

**20 executed / 20 PASS / 0 FAIL.** The actual canonical outputs are
[`reports/sprint02-evaluation.json`](../reports/sprint02-evaluation.json) and
[its Markdown report](../reports/sprint02-evaluation.md). Repeated service runs and the installed
wheel CLI produce byte-identical canonical reports; no clocks, temp paths, durations or random
IDs are included. Reports require a new filename or explicit --overwrite; suite and hard-link
alias overwrites are rejected. Deliberately false copied gold produces exact failures and exit 11.

| Metric | Actual result | Denominator/scope |
| --- | --- | --- |
| Candidate retrieval | TP 53; predicted 53; expected 53; FP/FN 0; precision/recall 1.0 | 18 eligible cases; 2 gold-declared truncated cases excluded; 5 empty cases |
| Evidence scope/IDs | TP 61; predicted 61; expected 61; FP/FN 0; precision/recall 1.0 | 18 eligible; 2 excluded; 1 empty case |
| Structured conflicting pairs | TP 3; predicted 3; expected 3; FP/FN 0; precision/recall 1.0 | 18 eligible; 2 excluded; 15 empty cases |
| Temporal field agreement | 120 / 120 | Explicit returned candidate/evidence classifications |
| Provenance agreement | 64 / 64 | Returned evidence provenance/verification/warning labels |
| Actual stored graph edges | 432 / 432 | Distinct per-case edge references; layout/direction independently checked |

Undefined zero-denominator precision/recall/agreement is null, never automatic 1.0. Truncated
scenarios still gate cap/field/path correctness; exclusions come from gold, not runtime claims.
Units are scenario occurrences, not independent production incidents or root-cause accuracy.
UNDETERMINED is asserted separately and not counted as conflict detection. All cases assert
NOT_ESTABLISHED. See [the methodology](EVALUATION_METHOD.md) for E01–E20 coverage and exact limits.

Each case builds a fresh real .rl from curated packaged fixtures. Queries, path direction,
depth 0/3/4, cycles, shared-service isolation, event boundaries/offsets/unknowns, missing evidence,
provenance, structured negatives, orphan observations and truncation are checked. No default or
public judge store is used as evaluation scratch space. Investigation uses at most six graph
queries; an additional bounded batch checks returned edge existence without per-edge queries.

Diagnostic only: one 20-case CLI run took **2.201138 seconds**, Windows 11 build 26200,
CPython 3.14.0, Relate 1.0.0, Intel i9-11900K (8 cores / 16 logical processors). Largest fixture
profile: 307 nodes / 408 edges; max returned observed services: 100. This is not a speed gate or
production benchmark. High-degree graph cost and whole-store RAM remain unbounded by row caps.

## Published synthetic judge artifact

- File: [`examples/judge-demo/traceweaver-demo.rl`](../examples/judge-demo/traceweaver-demo.rl).
- Manifest: [`examples/judge-demo/MANIFEST.json`](../examples/judge-demo/MANIFEST.json).
- Actual bytes: **110,592**; Relate **1.0.0**; actual counts **51 nodes / 67 relationships**.
- SHA-256: `29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239`.
- Logical graph SHA-256: `1cc7f23c5bc9926d9aec9b5f6a91c32022a8a6e268d52bc6120b9d4411c6743d`.

Only the unchanged Sprint 00 and opt-in Sprint 01 synthetic fixtures are loaded. Exact logical
contents, every node/edge demo marker, demo-only references, credential/private-prefix patterns,
and raw UTF-8/UTF-16 private prefixes are checked. These are limited checks, not a perfect secrets
audit. The manifest records fixture versions/hashes, contract information, engine, bytes/counts,
synthetic declaration and external NOT_PERFORMED. Hashes are computed after writer closure.

Actual final-path CLI checks, also repeated using the installed wheel outside the checkout:

```powershell
python -m traceweaver stats --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver context --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver investigate --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver investigate --incident CASE-INC --database ./examples/judge-demo/traceweaver-demo.rl
```

All succeeded read-only; SHA-256 stayed unchanged. INC-001 has two candidates/four evidence;
CASE-INC has six candidates/eleven evidence, one conflict and two undetermined pairs. The legacy
context model intentionally remains too strict for CASE-INC's invalid/incomplete metadata; an
initial README example exposed this and was corrected to INC-001. No contract was broadened.

The builder defaults to no overwrite; --force requires the intact recognized generated bundle,
matching bytes and exact published graph. Tests reject edited manifests, user stores, and a
modified graph even with an updated forged hash. Rebuild in a new directory; logical equality
is verified, but native binary bytes may vary by platform/build. Multi-file publication is not
atomic; trusted/quiescent output directories are required.

## Quality, packaging and runtime matrix

Environment: Windows x64 build 26200; CPython **3.14.0**, pip **25.2**, relate-db **1.0.0**,
pytest **9.2.0**, Ruff **0.17.4**, FastAPI **0.162.5**, Pydantic **2.14.3**. Dependency declarations
and lock file are unchanged; no runtime dependency was added or upgraded.

| Actual command/context | Result |
| --- | --- |
| Baseline `.venv` pytest | 119 passed in 11.71s |
| Development full regression after conflict fix | 204 passed in 22.96s |
| Independent locked editable environment, full regression | 204 passed in 25.32s |
| Independently installed current wheel, full regression | **204 passed in 31.58s; 0 failed; 0 skipped** |
| Final collection | 204 tests collected; 119 retained + 85 new |
| `python -m ruff check .` | All checks passed |
| `python -m pip check` | No broken requirements found, including independent wheel environment |
| `python -m pip wheel --no-deps .` | Built 55,588-byte wheel using normal isolated build backend |
| `pip install --no-deps --force-reinstall` of wheel | Successful; imports resolve to site-packages |
| Outside-checkout wheel CLI flow | Packaged resources match; dry-run; three applies; graph path; conflict 5; digest 6; evaluation 20/20; new isolated judge build; final public read-only commands all pass |
| `actionlint` 1.7.12 | Passed locally; unchanged Windows/Ubuntu Python 3.11 workflow |
| `git diff --check` | Passed before staging; final staged check pending |
| Python 3.11, Ubuntu, GitHub Actions | **UNVERIFIED / NOT RUN** |

Wheel SHA-256: `53f0fe7bf913c59106a6000e8854d8539190d3adee8d60d7ada95a114d16e0d3`.
Every packaged .py/.json was compared against current source. New tests: ingestion 33,
source integrity 18, evaluation 26, judge artifact 8. Real engine calls are retained throughout.

The attempted no-build-isolation wheel invocation failed because the new environment did not
contain setuptools. Normal PEP 517 build isolation then built successfully; no application or
lock-file workaround was introduced. An initial external smoke script had an incorrect project
root and was corrected before the successful CLI run. Failed attempts are not counted as PASS.

## Security and remaining technical debt

- Local regular-file admission rejects URL/UNC/device/drive-relative/ADS/remote and symlink or
  reparse traversal. Windows fixed drives and recognized Linux local mounts are admitted;
  unknown filesystem classification fails closed. Descriptor changes are checked, but hostile
  concurrent filesystem replacement is outside this local-operator boundary.
- URL metadata is never followed. Actual socket guards cover opaque external refs/evaluation.
  No GitHub API, account, production log, credential, or real incident access was used. Package
  installation during environment setup is separate from offline source verification.
- New errors expose bounded safe codes/field locations/counts, not raw source bodies, private
  paths or tracebacks. Legacy HTTP error/route/read-only/thread-affinity tests remain unchanged.
- Store locks are surfaced without destructive retries. Native rollback can change physical
  bytes; known-conflict preflight mitigates routine failures without claiming byte rewind.
- Source envelopes are not persistent authenticated intake records. Operator opt-in is not auth;
  no external source truth is established. No raw log indexing or arbitrary executable format.
- High-degree cost, whole-store memory, adversarial filesystem races, cross-file publication
  atomicity, and broader platform verification remain technical work for later scopes.
- Synthetic gold is small and rule-authored, not statistically representative or externally
  adjudicated. No comparison to search/LLM systems or production accuracy is claimed.

## Sprint 03 proposal — planned

Add a read-only explanation assistant consuming only the existing versioned investigation JSON.
Keep graph querying, admission, temporal rules and conflict detection deterministic and separate.
An explanation must cite existing evidence IDs/source references and actual stored graph paths;
validate every citation against returned context. Preserve missing/truncated scope, conflicting
and undetermined observations, external verification statuses, and NOT_ESTABLISHED causality.
Do not invent sources, declare a deployment the cause, or turn the assistant into remediation.
Evaluate unsupported-claim/citation rejection, abstention under missing evidence, adversarial
source text and repeatability against frozen cases before adding an optional model adapter.
No AI adapter, account, paid service, key, UI or connector is implemented in this sprint.

## Definition of Done

PASS below means locally verified within its stated scope, not remote runtime success.

| # | Acceptance criterion | Status | Actual evidence |
| --- | --- | --- | --- |
| 1 | Clean beginning audit and hashes | PASS | Clean main/eab9b30, baseline 119, ignored baseline record and final hash audit |
| 2 | All 119 prior cases retained/pass | PASS | Twelve unchanged original test files; full 204 passed |
| 3 | Real Relate 1.0.0 | PASS | Pinned dependency, native persistent-store transactions and queries |
| 4 | Versioned ingestion contract | PASS | Independent 1.0 models, valid 8/9 fixture, INGESTION_CONTRACT.md |
| 5 | Strict validation/bounds/safe errors | PASS | 33 ingestion / 18 source tests, admission/UTF-8/depth/count/size guards |
| 6 | Default dry-run/no creation | PASS | Fresh directory absent after default CLI; existing SHA unchanged |
| 7 | Transactional/idempotent/conflict-safe apply | PASS | Three applies; known-conflict SHA; actual race early inserts logically rolled back |
| 8 | Non-demo guard/dataset ownership | PASS | Explicit opt-in tests and strict ownership/demo conflict checks |
| 9 | Original local stores byte-identical | PASS | Before/after 3bdf4ffa…; 73,728 bytes; 21/27; never a writer |
| 10 | Independent expected digest/mismatch gate | PASS | MATCH/NOT_CHECKED/MISMATCH tests; mismatch exit 6 before parse/writer |
| 11 | Integrity/traceability/truth separate | PASS | Separate versioned output; byte-only warning; external NOT_PERFORMED |
| 12 | No source URL fetching/production/secrets needed | PASS | Socket-guarded tests, local synthetic resources, no connector/dependency |
| 13 | Structured taxonomy/rules preserved | PASS | SIGNAL_TAXONOMY.md, unchanged comparisons, CASE-INC one conflict/two undetermined |
| 14 | At least 18 frozen real-engine scenarios | PASS | 20 frozen E01–E20 cases, unchanged gold digest, 20/20 |
| 15 | Path/time/provenance/conflict/truncation assertions | PASS | Actual 432 edge checks, 120 temporal/64 provenance labels, positive/negative controls |
| 16 | Deterministic honest reports/no causal claims | PASS | Canonical byte equality, null denominators, gold truncation exclusions, NOT_ESTABLISHED |
| 17 | Synthetic persistent judge artifact/manifest | PASS | 110,592-byte committed candidate, exact synthetic graph 51/67, manifest |
| 18 | Read-only judge/hash verification | PASS | Final-path stats/context/investigate via installed wheel; hash unchanged |
| 19 | New commands/legacy contracts | PASS | All four new commands; old API/CLI exact regression tests; no write routes |
| 20 | >=30 new / >=149 total / no skips | PASS | 85 new; 119 retained; 204 passed, 0 failed, 0 skipped |
| 21 | Ruff/pip/dependency/build/wheel | PASS | Clean checks, unchanged lock, independent environment and external wheel CLI |
| 22 | Workflow lint/honest remote disclosure | PASS | Local actionlint passes; Python 3.11/Ubuntu/remote CI UNVERIFIED |
| 23 | English docs/complete report | PASS | All required docs, root/bundle walkthroughs, AI/synthetic disclosures |
| 24 | Staged security audit/clean final Git | BLOCKED | Final staging and commit checks pending; no verification claimed yet |
| 25 | Verified local commit/no push | BLOCKED | Commit deliberately pending final staged audit |

## Git delivery

Implementation commit and final clean status will be recorded after the scoped staged audit
and successful local commit. No push, new branch, history rewrite, or remote modification is
authorized or performed. A documentation-only follow-up may record the implementation hash;
it will change no tested source, test, fixture, dependency, or workflow.
