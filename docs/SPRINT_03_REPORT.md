# Sprint 03 verification report

Date: 2026-11-13. **Track A: PASS. Track B: PASS, including genuine local-model inference.**
Overall implementation/verification status: **PASS**, committed locally after the staged audit.
Remote CI/Python 3.11/Ubuntu are UNVERIFIED.
An example's PARTIAL_CONTEXT describes its incident evidence, not a failed sprint or model call.

## Baseline and preservation

Initial clean existing main: **20bf4edf3a8e22417dc578e7d2b2e70c00d028af**.
Sprint 02 implementation 5ad7b3eca706b9b12e33dcecb21169c53131bb70 remains in history.
Pre-change actual results: **204 passed in 22.42s**, Ruff clean, pip check clean.
The implementation note was recorded before substantive application code. Local ignored audit
records preserve initial hashes, model availability, collection/build checks and actual smoke
metadata without committing private paths, prompts, raw model responses or working databases.

All pre-existing workspace stores were inventoried and read only:

| Store | Bytes before / after | Real graph before / after | SHA-256 before / after |
| --- | --- | --- | --- |
| data/traceweaver.rl | 73,728 / 73,728 | 21 nodes / 27 relationships | `3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3` / same |
| examples/judge-demo/traceweaver-demo.rl | 110,592 / 110,592 | 51 nodes / 67 relationships | `29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239` / same |

The judge file was never rebuilt or reseeded. Its existing manifest remains unchanged,
SHA-256 `50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab`.
Existing source fixtures, packaged copies, legacy JSON snapshots, Sprint 02 gold/reports and
prior sprint documentation are retained. Sprint 02 gold SHA-256 remains
`6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8`.

All 204 earlier pytest cases remain present and pass. The sole existing-test edit adds exactly
the documented GET explanation route to the exact OpenAPI route set, as the brief permits.
No earlier assertion, fixture or failure was deleted, skipped or weakened. Existing Investigation,
temporal/provenance/comparison logic, graph queries, storage/seed/schema, dependency declarations,
lock file, Git ignore/binary rules and CI workflow remain unchanged.

## Implemented design and changed files

| Component | Responsibility |
| --- | --- |
| explanation_models.py | Strict versioned proof/report contracts and coherent execution/count invariants |
| explanation_catalog.py | Stable typed admissible claims from one actual returned Investigation |
| citation_validator.py | Deep snapshot isolation, semantic support, scope, exact path/direction, time/source/pair checks |
| explanation_renderer.py | Controlled factual templates; no source/model prose as fact |
| explanation.py | Shared read-only orchestration, deterministic selection, honest abstention/model failures |
| model_selection.py | Bounded snapshot-bound proposal; opaque claim hashes and typed metadata only |
| ollama_local.py | Optional fixed-loopback native tags/chat with JSON schema, bounds and deadline |
| explanation_scenarios.py / explanation_evaluation.py | Curated synthetic real-store evaluation, reviewed gold, attacks and actual edge queries |
| api.py / cli.py | Add deterministic GET explanation, explain and evaluate-explanations; preserve prior behavior |
| tests/explanations | Six test modules plus scoped fixtures: 133 new cases |
| evaluation/explanation_cases.json | Separate reviewed 19-case gold; review correction disclosed separately |
| reports/sprint03-explanation-evaluation.json / .md | Actual canonical offline evaluation outputs |
| docs/examples/*-explanation.json | Actual canonical native-store output examples, exact-equality tested |
| README / AGENTS / ARCHITECTURE and new docs | Contracts, safety, instructions, limitations, audit and AI/synthetic disclosure |

Module paths above are under src/traceweaver. No graph schema migration, write HTTP endpoint,
cloud inference, provider SDK, new runtime dependency, UI, remediation or causal inference exists.

One synchronous read-only GraphStore creates the unchanged Investigation, then closes on the
same thread before any model call. Canonical full response plus effective options binds the
fingerprint. Catalog claims use hashes of kind/stable identities; both source and catalog are
deep-copied inside the firewall. Every proposition's prerequisites and citations are verified;
existence of an ID alone is insufficient. Graph path layout/directions, candidate target/time,
HAS_EVIDENCE incident scope, provenance and exact structured pair/service are checked. A
multi-service regression verifies comparison proof follows the actual comparable service.

Deterministic mode requires no network/model and says it is not AI-generated. Insufficient
evidence abstains; missing onset prevents preceding-time claims. Important gaps and exact source
truncation remain visible independently of the curated claim list. Every accepted explanation
concludes with NOT_ESTABLISHED. All source refs/prose are withheld; stable IDs carry proof.

## Actual offline CLI and HTTP results

```powershell
python -m traceweaver explain --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl
python -m traceweaver explain --incident CASE-INC --database ./examples/judge-demo/traceweaver-demo.rl
```

| Output | INC-001 | CASE-INC |
| --- | --- | --- |
| Mode / ai_generated_selection | DETERMINISTIC / false | DETERMINISTIC / false |
| Explanation status | PARTIAL_CONTEXT | PARTIAL_CONTEXT |
| Returned candidate-targets / evidence | 2 / 4 | 6 / 11 |
| Validated rendered claims / citations | 8 / 11 | 10 / 18 |
| Structured conflict / undetermined count | 0 / 0 | 1 / 2 |
| Cause | NOT_ESTABLISHED | NOT_ESTABLISHED |

Full actual [INC-001](examples/INC-001-explanation.json) and
[CASE-INC](examples/CASE-INC-explanation.json) JSON examples are byte-canonical and tested
against real service results. The installed wheel produced exactly the same bytes outside
checkout. Same source/options repeated output is deterministic; model output is not promised so.

Actual independent-wheel Uvicorn subprocess/native HTTP smoke, bound to ephemeral 127.0.0.1:

- INC-001 and CASE-INC explanation: **200**, exact CLI/example equality.
- Nondefault 60/5 minute window and 2/4 caps: **200**, exact CLI equality.
- Unknown incident: **404**. Fractional pre_minutes: **422**.
- Separate server with missing scratch path: **503**, generic body, no file created.
- Pytest additionally verifies actual native writer locks in another process, generic unexpected
  **500**, unsafe-ID errors, strict arguments, read-only file hashes and concurrent worker reads.

HTTP exposes no model/provider switch; malicious mode query keys cannot enable inference. New
CLI failure codes are 12 unavailable, 13 rejected selection/output, 14 evaluation gold mismatch;
old command codes/JSON remain unchanged. Missing model explicitly returns NONE without fallback.

## Citation evaluation and frozen gold

The 19 initial cases were authored before application output was available. The first run was
**18 PASS / 1 FAIL**: X19's authored PARTIAL_CONTEXT label was incorrect. Independent review
of the unchanged pre-existing Sprint 02 E19 gold (READY_FOR_REVIEW) and source contract required
EXPLAINED. The one label correction and first-run digest are disclosed in
[EXPLANATION_GOLD_REVIEW.md](../evaluation/EXPLANATION_GOLD_REVIEW.md). No runtime output was
dumped into expectations, no scenario/assertion was dropped, and production behavior was not
altered to fit an incorrect label. Reviewed gold is frozen at:

`e716b63860712d9aaef23ac2b8a61b2bb77c225ce0359d8a36749cd65d2224cb`.

Actual current result: **19 executed / 19 PASS / 0 FAIL**, on separate real transient stores.
The original graph evaluation also remains **20/20**, with byte-identical Sprint 02 reports
when reproduced to fresh temporary output. New report artifacts:
[JSON](../reports/sprint03-explanation-evaluation.json),
[Markdown](../reports/sprint03-explanation-evaluation.md).

| Metric | Actual numerator / denominator | Scope |
| --- | --- | --- |
| Generated / admitted / semantically validated claims | 231 / 231 / 231 | Returned admitted catalog, not whole graph |
| Validated citations | 380 entries | Within those accepted catalog claims |
| Actual stored edge agreement | 181 / 181 | Distinct per-case type/source/target identities queried from native Relate |
| Independently reviewed claim/proof requirements | 32 / 32 | Explicit gold IDs, paths, UTC/classes and statuses |
| Invalid/forged selections/citations rejected | 133 / 133 | Controlled adversarial operations; no live model accuracy claim |
| Required uncertainty code checks | 10 / 10 | Frozen mandatory-warning expectations |
| No-cause caution coverage | 19 / 19 | Literal NOT_ESTABLISHED and mandatory accepted caution |
| Required abstention | 1 / 1 | Zero-evidence scenario |
| Repeated deterministic report equality | 19 / 19 | Same source/options; also full canonical suite equality |

Cases cover competing deployments, direct/dependency/reverse TARGETS, depth 3/4 and cycles,
BEFORE/AT_ONSET/AFTER/OUTSIDE_WINDOW/UNKNOWN, offsets, missing/naive/invalid onset, orphan
observations, incomplete provenance, comparable HEALTHY/FAILED versus DEGRADED, shared-service
isolation, external unverified sources, no evidence, caps and prompt-injection metadata.
Typed source proof and a native bounded batch establish actual edges without per-edge queries.

X12/X13 intentionally truncate source context. Their returned-item validity is checked, but they
are explicitly excluded from completeness claims; whole_graph_completeness is null. These are
synthetic semantic regression counts, not statistical production accuracy, LLM accuracy,
root-cause accuracy or proof of source truth. Undefined completeness is not labelled 100%.
Deliberately corrupted copied gold fails and exits 14; original gold is never rewritten by runners.

## Track B: genuine native local Ollama verification

A real running 127.0.0.1:11434 service listed already-installed models. **qwen3:8b** was selected
explicitly. No model, Ollama binary, service or system component was installed/downloaded.

Actual source CLI probe and final installed-wheel CLI inference both succeeded:

```powershell
python -m traceweaver explain --incident INC-001 --database ./examples/judge-demo/traceweaver-demo.rl --mode ollama --model qwen3:8b
```

Final installed-wheel result: **exit 0**, mode_requested/executed OLLAMA,
ai_generated_selection=true, provider OLLAMA_LOCAL, actual model_id qwen3:8b,
PARTIAL_CONTEXT, zero rejection codes, **7 accepted claims / 17 citations**.
The fingerprint matched deterministic mode, selected IDs/order differed from its eight claims,
and causal_conclusion stayed NOT_ESTABLISHED. Actual accepted IDs:

```text
C-137d0d5cc03effe27c154b25  DEPLOYMENT_BEFORE_ONSET
C-5b118ea365ea35831a7f99ad  DEPLOYMENT_BEFORE_ONSET
C-54c4c370e92e2f2bc7f5d109  EVIDENCE_REPORTED
C-8cbec333b5a692766348f324  EVIDENCE_REPORTED
C-a44ded691c6db0b178ce1748  EVIDENCE_REPORTED
C-a5a7d81f08112511b9059000  EVIDENCE_REPORTED
C-02c51c9fdd50a9a03b37c175  NO_CAUSAL_VERDICT
```

This is actual local-model selection over one inspected incident snapshot, not a benchmark or
general diagnosis. Controlled tests never count as this live-model evidence. No prompt/raw
provider body was saved, logged or committed; accepted IDs and safe aggregate metadata suffice.
The model cannot create facts/URLs/tools/Cypher; deterministic templates render verified facts.

The native [chat](https://docs.ollama.com/api/chat),
[tags](https://docs.ollama.com/api/tags) and
[structured format](https://docs.ollama.com/capabilities/structured-outputs) documentation was
checked before adapter implementation. Runtime uses only fixed native tags/chat, stream=false,
JSON schema, temperature 0, think=false and a modest 512-token budget. No proxy, redirect,
arbitrary host, cloud SDK, credential forwarding, retry or download route. Read/body/depth/time
limits and exact proposal fields are tested; untrusted response prose never becomes a fact.

## Test, packaging and environment evidence

Environment: Windows 11 x64 build 26200, CPython 3.14.0, Relate 1.0.0, pytest 9.2.0,
Ruff 0.17.4, pip 25.2. No runtime/development dependency declaration or lock change.

| Actual execution | Result |
| --- | --- |
| Pre-change `.venv` full suite | 204 passed in 22.42s |
| Final source `.venv` full suite | **337 passed in 41.19s** |
| Fresh locked environment, non-editable current wheel, full suite | **337 passed in 42.14s** |
| Retained / new / total | **204 / 133 / 337**, 0 failed, 0 skipped |
| Ruff in development and independent environment | All checks passed |
| pip check, including independently installed wheel | No broken requirements found |
| pip wheel --no-deps . and isolated install | PASS; actual source/resources compared against wheel ZIP |
| Installed wheel outside checkout | Exact examples, original 20-case and new 19-case canonical JSON/Markdown equality |
| Actual native HTTP / CLI / live Ollama | PASS, detailed above; server processes terminated afterwards |
| actionlint 1.7.12 | Local PASS; unchanged workflow |
| Python 3.11 | UNVERIFIED; not found on PATH or inspected registered PythonCore installations |
| Ubuntu / remote GitHub Actions | UNVERIFIED / NOT RUN; no push |

Wheel: traceweaver-0.1.0-py3-none-any.whl, **78,707 bytes**, SHA-256
`d9290855c56cc4f0fae61b966d20abf13b1a094226cb73d2a75a275a9d03f71d`.
Every packaged source/JSON resource matches the tested checkout. Fresh .venv-sprint03-verify
uses unchanged requirements-dev.lock; outside-checkout commands use the installed distribution,
not an editable import. Temporary server/store/output paths never enter canonical public reports.

Actual new collection: catalog 15, firewall 17, service 17, API/CLI 21, Ollama/provider/selector
protocol and safety 40, evaluation 23 = **133**. Those 40 controlled tests include native local
transport and proposal tests, not 40 real LLM inferences. Offline tests block sockets and preserve
real graph calls; wrapper instrumentation forwards native calls rather than simulating rows.

Observed failures were corrected and rerun: an early comparison-helper return arity mismatch;
the disclosed gold label; initial new suite 124 passed / 1 failed because a Windows connect
timeout was classified like a read timeout; full-suite collection initially exposed a new test
filename collision. Connect refusal/timeout is now unavailable while read timeout rejects output;
the new test filename is unique. Assertions remain intact. Final source/wheel results above
passed after these corrections and additional contract/multi-service proof coverage.

## Network, security and limitations

- Application inference contacted only 127.0.0.1:11434. Actual HTTP/protocol verification used
  loopback ephemeral ports. Deterministic and offline evaluation modes make no network calls.
- Authoring consulted official Ollama documentation; environment/build setup used Python package
  infrastructure. These are separate from incident/source verification. No source URL, account,
  production log, cloud model, private repository or external incident truth was accessed.
- External source authenticity/truth: **NOT_PERFORMED**. Hashes and traceability do not prove it.
- Source prose/refs, credential-shaped metadata and private paths are withheld from model packets
  and rendered explanations. Stable graph IDs are validated; unsupported identifiers fail closed.
  New HTTP/tool errors are generic/bounded. Prompts/raw provider outputs are not persisted.
- Proposal bounds: 4 KiB, four containers, eight selected IDs. Packet 32 KiB, native request
  48 KiB, response body 64 KiB/depth eight. Connect two seconds, read inactivity 30 seconds,
  monotonic socket-read deadline 45 seconds. Catalog/render/uncertainty limits are separate and
  disclosed; no completeness claim is supported by capped context.
- The trusted local daemon/model supply chain is not authenticated here. Obvious remote/cloud
  configurations are refused; a hostile renamed local proxy is outside this boundary. A client
  deadline does not forcibly cancel backend computation. Model scheduling/cancellation is future work.
- Row/byte admission does not cap whole-store RAM, native query work or initial raw-property
  materialization. Relate remains single-writer and thread-affine. No explanation writer exists;
  the prior native physical rollback-byte limitation is unchanged.
- Explanations validate returned-context support, not real-world truth, exhaustive graph discovery,
  root cause or a definitive fix. Synthetic datasets and small gold limit interpretation.

The executed staged review covered **33 files**, checked **32 local documentation links** and
compared all **80 pre-existing tracked files** against the baseline. Only six intended existing
files changed: AGENTS, README, architecture, API, CLI and the exact OpenAPI route assertion.
It found zero matches for reviewed private-user/project paths, credential/key patterns or private
keys, and zero unexpected binaries/stores. No .rl, environment, verification record, model raw
output or private import was staged. Both original store hashes/counts remained unchanged.
This limited static pattern/content review is not a perfect security audit. Cached diff check
passed; post-implementation status was clean.

## Definition of Done

| ID | Track A criterion | Status | Actual evidence |
| --- | --- | --- | --- |
| A1 | Pre-change 204 cases; old cases preserved | PASS | 204 baseline; 337 final; only documented OpenAPI route assertion addition |
| A2 | Relate, user/judge stores, manifests, fixtures, old gold/reports preserved | PASS | Actual before/after hashes/counts and unchanged protected-file audit |
| A3 | Strict versioned ExplanationReport | PASS | Contract 1.0, extra forbid, execution/count checks, OpenAPI schema tests |
| A4 | Real Investigation-derived stable catalog | PASS | Native source queries; kind/entity ID hashes and canonical snapshot/options binding |
| A5 | Semantic citation firewall | PASS | Scope/target/path/direction/UTC/provenance/pair/multi-service and forged-proof tests |
| A6 | Controlled noncausal renderer/no false verification | PASS | NOT_ESTABLISHED, NOT_PERFORMED; no source/model factual prose |
| A7 | Honest gaps/truncation/conflict/unknown/abstention | PASS | 10/10 required-warning checks, source flags, 1/1 required abstention |
| A8 | Explain CLI and deterministic HTTP | PASS | Actual Uvicorn 200/404/422/503; exact default/nondefault CLI equality |
| A9 | Stable output and actual examples | PASS | Canonical repeats and exact source/wheel example tests |
| A10 | >=15 frozen cases and meaningful adversarial metrics | PASS | 19/19; 231 claims, 380 citations, 181 edges, 133/133 attacks; label review disclosed |
| A11 | >=40 new, >=244 total, clean Ruff/pip, no unearned skips | PASS | 133 new / 337 total; zero failures/skips; clean checks |
| A12 | Independent installed wheel and actual HTTP/CLI | PASS | Fresh locked non-editable install, outside-checkout commands and real native HTTP |
| A13 | Complete documentation/report | PASS | Required contracts, safety, walkthrough, examples, root/AGENTS/architecture updates and this report |

| ID | Track B criterion | Status | Actual evidence |
| --- | --- | --- | --- |
| B1 | Supported native Ollama adapter | PASS | Official tags/chat/structured format; actual qwen3:8b response |
| B2 | Loopback/bounds/no tools/download/strict schema | PASS | Fixed address/routes, byte/depth/deadline guards, sanitized opaque packet |
| B3 | Unsupported/hallucinated selections rejected | PASS | 133/133 evaluation attacks and provider/selector safety tests |
| B4 | Controlled provider protocol/security tests, distinct from live AI | PASS | 40 provider/selector tests; explicit controlled loopback fixtures |
| B5 | At least one genuine installed local-model inference | PASS | Actual final wheel qwen3:8b call; seven IDs / 17 citations accepted, no-cause invariant |

Remote runtime verification is explicitly **UNVERIFIED / NOT RUN**, not passed by inference.
Local Git/security criteria also passed: staged review, diff check, exact implementation subject,
existing main/history, clean post-implementation status, and no push.

## Sprint 04 recommendation — planned

Build a small read-only evidence/citation dashboard over the existing contracts: display
incident scope, actual directed paths, competing deployments/times, evidence provenance,
structured conflicts/undetermined pairs and gap/truncation badges. Keep deterministic offline
mode prominent, with an explicit local-only selector action if separately scoped. Prepare a
one-to-two minute judge demonstration using the immutable 51/67 synthetic store, one actual
Relate path, visible citation checks and optional genuine local model selection. No new causal
verdict, source-truth claim, model-written factual prose or autonomous remediation should appear.

## Git delivery

Implementation commit: **4810da83c2828a768106601df9c9d62c12a202e7** on existing main.
Exact subject:
`sprint03: add citation-verified incident explanations and local AI selector`.

Observed immediately after implementation commit: git status --short --branch returned only
`## main`. A separate report-only follow-up records this actual hash, staged review and observed
clean status. It changes no tested source, test, fixture, example, dependency, workflow or
evaluation artifact. Tests above refer to that unchanged implementation and installed wheel;
no claim is made that application tests needed to rerun after a report-only metadata update.
Final status is checked after the follow-up. Inspect git log -2 --oneline for both local commits.
No reset, rebase, new branch, remote modification, publication or push was performed.
