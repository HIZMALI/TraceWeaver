# Offline synthetic evaluation method — version 1.0

Implemented and verified locally with real relate-db 1.0.0. These are deterministic synthetic
retrieval/path/state checks, **not root-cause accuracy, source truth, or a comparative benchmark**.
There is no vector-search, text-search, or LLM baseline and no claim of superiority over one.

## Frozen labels and execution

`evaluation/cases.json` contains 20 manually specified scenarios. Gold candidate/target IDs,
dependency depths, node sequences, stored edge directions, time classes/UTC values, evidence
membership/services, provenance/warning labels, conflicting/undetermined pairs, readiness, and
truncation flags were authored from topology and rule specifications before the runner executed.
They were not copied from runtime responses. The frozen suite SHA-256 is:

```text
6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8
```

The runner never rewrites labels. A test deliberately changes an expected time class in an
isolated suite copy and verifies exact expected/actual failures, a failed report, and exit 11.
This is not a statistically representative or independently adjudicated real incident dataset.

Each case gets a fresh OS temporary .rl, populated from curated packaged fixture profiles:
baseline (21/27), sprint01 (30/40), evaluation (50/58), or caps (307/408). Arbitrary file paths,
Cypher, callbacks, and fixture loader plugins are not accepted in a suite. The existing unchanged
investigate service runs read-only, on its owning thread. No default or public judge store is used
as evaluation scratch space. Source URLs remain opaque; outbound-socket guards are tested.

## Scenario coverage

| Cases | Controls |
| --- | --- |
| E01–E02 | Actual dependency/direct candidates, reverse TARGETS, change neighbors, incident isolation |
| E03–E05 | Structured conflicts/DEGRADED, incomplete metadata, missing onset, shared-service evidence isolation |
| E06 | Depth 3 included, depth 4 excluded, cycles and duplicate path handling |
| E07–E09 | Inclusive lower/upper boundaries, one-second negatives, zero windows, explicit offsets, short pre/post windows |
| E10–E12 | Invalid/naive incident anchors and missing evidence |
| E13 | Same-context conflict plus different service/environment/signal/disjoint-time negatives |
| E14–E15 | Real candidate/evidence/observation overflow, N+1 caps and incomplete returned scope |
| E16–E18 | Exactly-full caps without false truncation; narrow and zero-width legacy incident windows |
| E19–E20 | Opaque URL metadata, missing event time without ingestion fallback |

Every case asserts NOT_ESTABLISHED causality. Missing change neighbors and orphan evidence
remain visible. Runtime path layout is checked independently of gold equality; all distinct
returned stored edges are verified in one additional bounded real Cypher query.

## Metrics and denominators

Precision is TP / predicted count, recall TP / expected count. A zero denominator produces null,
not 1.0. Units are scenario-specific occurrences: an ID reused under another window is another
scenario occurrence, not another independent deployment/incident. No macro-average over empty
cases is substituted for the reported micro totals.

Gold-declared truncated candidate/evidence scenarios are excluded from the affected retrieval
metric. Evidence/observation/contradiction truncation excludes a case from full conflict-pair
retrieval metrics. Their cap behavior and returned-item field/path checks still gate PASS.
Exclusions use frozen gold, not a potentially incorrect runtime flag. This prevents scoring a
small capped subset as complete recall over all graph entities.

Actual committed-suite results:

| Metric | Actual numerator / denominator | Result and exclusions |
| --- | --- | --- |
| Candidate retrieval | TP 53; predicted 53; expected 53; FP/FN 0 | Precision/recall 1.0; 18 eligible cases, 2 truncated excluded; 5 eligible empty cases |
| Evidence scope/citation IDs | TP 61; predicted 61; expected 61; FP/FN 0 | Precision/recall 1.0; 18 eligible cases, 2 excluded; 1 empty case |
| Conflicting structured pairs | TP 3; predicted 3; expected 3; FP/FN 0 | Precision/recall 1.0; 18 eligible cases, 2 excluded; 15 empty cases |
| Temporal field agreement | 120 / 120 explicit candidate/evidence labels | 1.0, including returned-item checks in truncated scenarios |
| Provenance/verification/warnings | 64 / 64 returned evidence labels | 1.0; independent of external truth |
| Actual graph edge existence | 432 / 432 distinct per-case edge references | 1.0, plus direction/layout checks |

UNDETERMINED pairs are asserted separately and never counted as detected conflicts. Provenance
quality is separate from content integrity: the evaluation does not authenticate any source.
The report explicitly carries external_verification_status=NOT_PERFORMED and causal_conclusion=
NOT_ESTABLISHED. Repeated synthetic examples and simple rules limit the interpretation of perfect
agreement. These numbers establish consistency with this frozen suite, not production accuracy.

## Determinism, output, and limits

```powershell
python -m traceweaver evaluate --suite ./evaluation/cases.json --output ./reports/new-evaluation.json
```

Use a new output filename, or explicitly add --overwrite for an existing report. JSON and the
companion .md are both protected from implicit overwrite. Suite/output path equality and hard-link
aliasing are rejected. The committed `reports/sprint02-evaluation.json` and .md are actual outputs.

Canonical JSON is sorted/normalized and excludes clocks, durations, temp paths, random IDs and
local timestamps. Repeated runs produce byte-equal normalized results. Input digest and fixed
engine version are included. Diagnostics contain deterministic actual query/list counts only.
At most 64 cases, 100 gold candidates/evidence/comparison pairs per case, 100 failures displayed
per case with a full failure count/overflow flag, and 1,000 unique graph edges per validation batch
are admitted. Suite input is bounded to 8 MiB and 16 container levels (explicit graph paths need
more nesting than ingestion's eight). CLI exits 11 on expectation failure; invalid/unexecutable
suites return a safe nonzero error rather than a fabricated completed result.

## Diagnostic profiling and limitations

The actual local 20-case CLI execution took 2.201138 seconds on Windows 11 build 26200,
CPython 3.14.0, relate-db 1.0.0. This is a single diagnostic observation, not a gating speed target
or throughput claim; it includes process/report overhead and is kept outside canonical JSON.
Host CPU: Intel Core i9-11900K, eight cores / sixteen logical processors. The largest fixture
profile has 307 nodes / 408 relationships; these are small synthetic workloads.
Maximum investigation query count was six; the largest returned observed-service list was 100.
Seed writes and the independent edge-validation query are not included in that six-query count.

Row caps do not bound graph query cost, total persistent store size, or native working RAM.
High-degree graphs require future profiling/admission work. Windows/Ubuntu Python 3.11 native
regressions have run in hosted CI; consult the exact commit's Actions results for coverage.
Separate 19-case explanation and 35-case agent suites are documented in the
[evaluation guide](../evaluation/README.md). Independent real-incident cases and broader ingestion
evaluation remain future work; no external benchmark or paid model was used.
