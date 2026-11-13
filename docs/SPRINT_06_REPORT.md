# SPRINT 06 — RESULT

**Overall: PARTIAL.** Proje: `D:\Projects\TraceWeaver`, dal: mevcut `main`.
Başlangıç: `a8f4ac502c8bb4eaefce8d6e448a273aa133a73e`.
Test edilmiş son uygulama commit'i: `6ef7def`.

Türkçe sonuç: Beş gerçek, salt okunur Relate aracı; sınırlı model yönlendirme denetleyicisi;
çevrimdışı gerçek araç provası; güvenli arayüz ve citation bağlantıları uygulandı. Son tam
koşuda **518 Python, 80 frontend, 49 Playwright testi geçti**. Mevcut 420/58/36 test korundu.
Yeni bağımsız değerlendirme 35/35 geçti; bozuk gold kontrolü gerçekten başarısız oldu.
Gerçek qwen3:8b, trace_deployment aracını seçip native sorguyu çalıştırdı; fakat son claim-ID
çıktısı AGENT_FINISH_SCHEMA ile reddedildi, kabul edilmiş canlı claim/citation sayısı sıfırdır.
Sonraki denemelerde Ollama erişilemedi. Bu nedenle tam canlı AI akışı BLOCKED, genel sonuç
PARTIAL'dır. Firewall gevşetilmedi; sonuç veya model başarısı uydurulmadı.

Bağımsız wheel kurulumu, Node'suz sunucu ve gerçek tarayıcı provası geçti. Altı gerçek ekran
görüntüsü ve incelenmiş 7,28 saniyelik sessiz kayıt hazırdır; bu kayıt bitmiş yarışma videosu
değildir. Public repo, LICENSE seçimi ve 1–2 dakikalık son video sahibinin kalan işleridir.
Push, Devpost gönderimi, veritabanı sıfırlama, model indirme veya sistem kurulumu yapılmadı.

Technical evidence below is English in accordance with project documentation rules.

## Gate acceptance

| Gate | Result | Actual evidence / limitation |
| --- | --- | --- |
| G0 | PASS | Read mission/AGENTS/source/history; clean existing main; original native stores/manifest/fixtures/gold/report/image hashes recorded; 420/58/36 baseline actually ran |
| G1 | PASS | Native proof summary, competing pair buttons, readable core viewport, selected/hover edge labels, full counts/arrows/path list retained; actual 1440×900 capture |
| G2 | PASS | Separate strict AgentInvestigationReport 1.0; five real fresh parameterized native tools; exact directed edges rechecked; source/digest/opaque-ID and bounded result contracts |
| G3 | BLOCKED for accepted live final | Finite real controller/protocol tests PASS. Genuine qwen3 selected/executed trace_deployment, but final schema rejected; latest service refused connection. No successful accepted live multi-step/final AI result claimed |
| G4 | PASS | Identical native tools in fixed offline plans for all four intents; both AI flags false; separate CLI; canonical repeatability preserves event times |
| G5 | PASS | Explicit expansion, offline default, separate actual capabilities/model/confirmation POST; trace-to-path/inspector/claim focus, late/cancel/stale guards, legacy selection preserved |
| G6 | PASS | New 115-second click story, six genuine inspected captures; candidate comparison/native tool/citation/conflict/gap route works without model |
| G7 | PASS | New independently authored frozen A01–A35 expectations; 18 native + 17 controlled cases passed; independent corrupted expectation returned exit 15 |
| G8 | PASS, limitations track | Historical graph/flat source, gold, both raw outputs and R13 erratum unchanged; rigorous new limitations/future-design note; no new fair-comparison or superiority claim |
| G9 | PASS on exercised local platform | 518 pytest / 80 frontend / 49 actual native browser; Ruff/pip/type/lint/build/actionlint; byte guards; native microprofile; external installed wheel/Node-free server/browser/CLI. Python 3.11/Ubuntu/remote CI remain UNVERIFIED |
| G10 | PASS for authorized local artifacts | Report/walkthrough/contracts/story/readiness/fact check/draft/video plan, six screenshots and genuine short clip. Public repository/license/final presentation video are owner-pending, not silently published |
| G11 | PASS with disclosed G3 blocker | Final protected audit, ancestor/main checks, local tested milestone commits, append-only continuation and retained known limitations; no remote/push. Documentation closure is the commit containing this report; final SHA and clean-status observation are in the final chat response |

## Implementation and data boundaries

`agent_tools.py` uses the existing Investigation as the authoritative snapshot, not a second graph
analyzer. Every step opens a worker-local read-only native connection, executes fixed parameterized
Cypher and closes before any model HTTP request. Tools are get_incident_scope, trace_deployment,
inspect_evidence, compare_observations, inspect_gaps. Native edge audit checks exact stored
type/source/target triples. TARGETS reversal is a traversal annotation, never a reversed stored edge.

Agent requests accept exact incident/options/fingerprint/intent and explicit true confirmation;
AI additionally requires an eligible actual installed model. Provider sees only scoped opaque
subjects/node/claim IDs, fixed enums/counts/UTC. No source prose, raw entity IDs, URLs, private
paths, arbitrary prompts, tools, Cypher or model-authored facts cross the factual boundary.
Source references are never fetched. Existing external verification remains NOT_PERFORMED.

Budget: four executed tools, five chat interactions, one executed tool per round; at most four
parallel proposals validated as a whole then only the first executed with an explicit warning.
Invalid/duplicate/out-of-scope tails reject the whole batch. Eight native queries/paths/records
per step, one comparison, twenty codes, 64 IDs, 64 KiB tool result, 512 KiB report. Digest reads
cap local files at 8 MiB. Request body is 2048 bytes/depth four/two-second read, duplicate fields
rejected. Provider request/response bounds are 48/64 KiB, round deadline 20s, total 90s; offline
plan has a 30s between-tool guard. No retry/pull/cloud endpoints or recursive tool invocation.
These guards cannot preempt already running native Cypher or guarantee daemon cancellation.
Row caps are not RAM/query-cost bounds. One server worker / one shared local-action lock applies.

New POST routes are `/console/agent/rehearse` and `/console/agent/investigate`; exact numeric
loopback Host/client and Origin/port required. Initial source mismatch returns 409, unknown
incident 404, incompatible graph 503, concurrent action 429. Old GETs and CLI outputs remain
unchanged, HTTP explanation stays deterministic. Only two old exact OpenAPI route/method
assertions were extended; no assertions removed/weakened, skips/xfails introduced or tests deleted.

Read-phase model narrative is discarded, never echoed or rendered. A separate bounded structured
final-ID phase uses the existing proposal contract. Final IDs require actual retrieved support
and existing semantic CitationValidator admission; controlled templates render facts. Invalid
final output is not repaired/retried. No-tool ID selection is MODEL_SELECTION_ONLY. Explicit
abstention does not count the appended server caution as AI-selected factual statements.

The browser validates shape, canonical digest, source/options/intent/model metadata, source path/
record/comparison membership, citation count and permanent no-cause flags before highlighting.
Step focus is transient; reload/back links keep native entity selection, not an invented executed
run. Visual filters disclose hidden nodes/edges and do not modify source. Native evidence times
retain UTC/originals or UNKNOWN; ingestion/current clock never substitutes onset.

## Genuine Ollama evidence, separate from controlled tests

Actual existing service was transiently available: `/api/version` 0.40.16; actual tags included
qwen3:8b (5,225,388,164 bytes) and openweft-qwen3:8b (5,225,387,834 bytes). No daemon/model was
installed, started or pulled by this session. Official native tool/chat documentation was read
before coding (links in decisions/contract).

| Attempt | Actual outcome | Executed tools | Chats | Admitted final claims/citations |
| --- | --- | --- | ---: | ---: |
| 1 | Initial strict parallel batch rejected: AGENT_MULTI_TOOL_REJECTED | None | 1 | 0 / 0 |
| 2 | Genuine model-selected native tool, final AGENT_FINISH_SCHEMA | trace_deployment | 2 | 0 / 0 |
| 3 | Explicit structured final phase still AGENT_FINISH_SCHEMA | trace_deployment | 3 | 0 / 0 |
| 4 | OLLAMA_CONNECTION_UNAVAILABLE | None | 0 | 0 / 0 |
| 5 | OLLAMA_CONNECTION_UNAVAILABLE | None | 0 | 0 / 0 |

Example actual attempt 3: selected D000 mapped to DEP-002/SVC-PAYMENT; three native tool queries,
ten total including initial snapshot, 7,633.602ms full measured operation. Actual paths include
INC-001 → SVC-PAYMENT ← DEP-002 → CHG-002. Stored triples are AFFECTS INC-001→SVC-PAYMENT,
TARGETS DEP-002→SVC-PAYMENT (reverse traversal), INCLUDES_CHANGE DEP-002→CHG-002. Source fingerprint
`d05166378e55098b88a4c71e69095cc206e075031a3e46ce1a5643f70c1b5520`, unchanged judge digest below.
ai_directed_tools=true, ai_generated_selection=false. This is native tool-use evidence, not
accepted explanatory output, multi-step success, source verification or model accuracy.

`reports/sprint06_live_agent_evidence.json` retains safe aggregate codes and the admitted native
trace only. No raw provider body/prompt is persisted. Current capabilities in screenshot 06 and
the actual recording show unavailable service/empty selection; a successful live-agent UI trace
capture could not be made. Controlled three/four-round native/protocol tests do not replace it.
Recommended next work is stabilize the existing service and diagnose bounded schema-only failure
metadata without exposing provider text or weakening firewall. No repeated unattended probes run.

## Actual commands and test results

All Python commands used the project `.venv`; no global install. Baseline: 420 pytest in 48.48s,
58 frontend, 36 native Playwright in 29.9s. G2 full 452/47.20s; G3 479/67.70s; G4 492/48.35s;
G5 511/52.65s; later 517/59.98s; final below. Durations are real observations under concurrent
desktop/build activity, not standardized performance comparisons.

| Command | Final observed result |
| --- | --- |
| `.venv/Scripts/python -m pytest -q` | **518 passed in 124.12s**; 420 retained + 98 added, no skips/xfails/failures |
| `.venv/Scripts/python -m ruff check .` | All checks passed |
| `.venv/Scripts/python -m pip check` | No broken requirements found |
| `npm --prefix web run typecheck` | Exit 0, also run by build |
| `npm --prefix web run lint` | Exit 0 |
| `npm --prefix web test` | **80 passed**, four files; 58 retained + 22 added |
| `npm --prefix web run build` | Exit 0; JS 571.90 kB / 176.46 kB gzip, CSS 39.82 / 8.42 kB |
| `npm --prefix web run test:e2e` | **49 passed in 37.5s**; 36 retained + 13 added, actual Relate-backed Chromium |
| `.verification/sprint01/tools/actionlint.exe` | Exit 0, version 1.7.12 |
| `.venv/Scripts/python -m traceweaver.judge --bundle examples/judge-demo --check` | PASS, read-only 51/67 native graph; INC-001 2/4 and CASE-INC 6/11 |
| Existing Sprint 02 evaluation to new ignored output | 20/20 passed, old gold/reports unchanged |
| Existing Sprint 03 explanation evaluation to new ignored output | 19/19 passed, old gold/reports unchanged |

Browser checks include no POST/foreign network on load, exact native directions, ordered trace,
proof/citation focus, conflict/UNKNOWN, source caps, explicit actual capabilities without inference,
reload without fictional run, keyboard, reduced motion, expanded-panel axe (zero violations),
1024×768, 720px equivalent reflow and 390×844 phone without document overflow. These are exercised
checks, not blanket WCAG certification. Unit/HTTP tests cover malformed/deep/duplicate/oversized
input, Origin/Host/body/model/confirmation bounds, one shared in-flight action, stale digest,
thread/reader closure before provider, byte preservation, timeout/no-tool/fake-tool/fake-claim/
causal-prose rejection and finite query/tool/chat/deadline exhaustion. Existing native blocked-
writer/read-only tests remain passing. Normal browser paths use genuine native responses.

Corrected failures are disclosed: native no-evidence test initially referenced an unavailable
fixture profile (replaced by an explicitly temporary native no-evidence specimen); duplicate new
test basename caused collection conflict (renamed new file); initial new independent browser
runner imported Playwright before setting browser-cache path (fixed ordering). Existing G1 axe
accessible-name mismatch was corrected. These failures were fixed/rerun, not skipped. Vite still
reports dependency “use client” directive warnings; this is a client bundle, no SSR claim.

Raw local evidence is ignored under `.verification/sprint06`: `final-pytest.txt`, `G9-browser.txt`,
`G9-build.txt`, owned `browser-*/playwright.json`, `baseline.json`, `independent-install.json`,
`independent-npm.txt`, `independent-pip.txt`, `wheel-build-v2.txt`, `agent-negative-control.json`.
No private stores, credentials or raw provider logs were added to Git.

## New frozen evaluation and microprofile

Gold committed at 9c49bf7 **before runner implementation/execution**. Its repository LF checkout
digest was separately pinned at adacd13 before the first run; no labels changed in normalization.
Final SHA-256 `dce5da3e7561029a8877fb03a9de86961509f728694b6c22e01155e82dfa6295`.
Command: `python -m traceweaver.agent_evaluation --suite evaluation/sprint06_agent_cases.json
--output reports/sprint06_agent_evaluation.json` (project Python). Existing reports need explicit
overwrite; output cannot alias suite even with that opt-in. All graphs are fresh isolated native
stores; no user/judge seed/migration. Old E/X/R gold is not relabeled as new independent work.

35/35 passed: 18 native scenarios plus 17 separately labeled controlled protocol scenarios.
They cover direct/three-hop/excluded-four-hop, reverse TARGETS/change, evidence, conflict/unknown,
missing/naive time/reference/external source, orphan/shared service, no evidence, caps, malicious
metadata, stale source, fake IDs/direction/write/Cypher/URL/prose, deep/oversized JSON, duplicate/
valid constrained parallel requests, timeout/unavailable/no tools, budgets and no-cause caution.

| Metric | Actual numerator / denominator | Scope |
| --- | ---: | --- |
| Positive native tool admission | 22 / 22 | Successful native cases; controlled negative cases reported separately |
| Genuine stored directed edge agreement | 57 / 57 | Distinct returned edge tuples per successful native case, independently queried again |
| Existing semantic citation support | 90 / 90 | Admitted citations only; no whole-graph completeness or truth denominator |
| Canonical repeatability | 18 / 18 | Same store/scope/options, measured durations explicitly excluded |
| Explicit no-evidence safe abstention | 1 / 1 | The authored no-evidence case only |
| Live-model/source-truth/root-cause accuracy | null | Not evaluated/established |

Zero denominators are null. Metric scope excludes failed native cases, whose failures remain
visible in total/per-case results; this run has zero failed cases. Corrupt-gold copy replaced
A01's expected stored endpoint, returned GOLD_NATIVE_EDGE and **exit 15**, 34 pass / 1 fail. Frozen
original stayed byte-identical. The runner never regenerates expectations from current outputs.

Microprofile: real Relate rehearsal, seven sequential same-process observations each, warm OS
cache uncontrolled, Intel i9-11900K (8 cores/16 threads), 31.87 GiB RAM, Windows 11 build 26200,
Python 3.14.0. Median / nearest-rank p95: baseline 44.718/45.343ms, CASE 51.485/58.817ms, capped
141.448/153.077ms. All execute four tools/23 native queries; capped source/subject flags remain
true. p95 at n=7 is max; no confidence interval, cold-cache or native RAM/work bound claimed.
Raw samples in `reports/sprint06_native_microprofile.json`. No graph/flat speed claim.

## Independent distribution evidence

Copied frontend outside checkout: fresh npm ci, 194 packages installed / 195 audited, zero reported
vulnerabilities, build exit 0; hashed JS/CSS/notices bytes matched current checkout. Fresh-source
wheel built by `scripts/build_judge_wheel.py --output .verification/sprint06/final-wheels-v2`:
300,901 bytes, SHA-256 `976835f51a0dd0252f18df4892e7c19716aee6f4d17aaba0470e871e9504e7d0`.
Exactly one JS/CSS generation, notices, no .rl. Wheel hash is a particular local build, not an
assurance that timestamp-bearing wheel ZIP bytes reproduce identically.

Fresh external non-editable Python 3.14 environment installed it using existing lock constraints;
pip check passed, import resolved outside checkout without PYTHONPATH. Copied intact judge bundle
verified natively. Server process PATH excluded Node. Health/index/assets and actual Chromium
158.0.8127.18 rendered 14 native edges with zero page errors/no initial AI. Packaged browser ran
get_incident_scope → trace_deployment → inspect_evidence → inspect_gaps: 23 native queries,
8 admitted claims / 11 citations, both AI flags false; step 2 reverse proof focus worked. Installed
traceweaver-agent entry point also ran outside checkout without Node: four tools/8 claims/11
citations. Copied database bytes unchanged; owned server stopped. No published wheel claimed.

## Captures, presentation and release limits

Six new genuine native-backed images: `docs/screenshots/sprint06/01-first-viewport.png`,
`02-native-tool-proof.png`, `03-offline-tool-trace.png`, `04-structured-conflict.png`,
`05-phone-rehearsal.png`, `06-local-capability-state.png`. First five are actual browser-test
captures, sixth is actual capability-state capture during recording. All visually inspected.
All historical seven screenshot bytes unchanged. Dense full-context graphs can still be small;
focused proof and exact accessible path lists are the reliable detailed view.

`docs/video/sprint06/native-walkthrough.webm` is a genuine **7.28s silent** VP9 1440×900/25fps
test execution clip, 2,934,834 bytes, inspected through actual extracted frames at 2/4/7 seconds.
SHA `73c93ea0ce85ef955f8742a781b871e6863a8cb036dd53825fff4ff928b5e1a9`. Companion captions.json
is approximate runner-clock action notes, not a synchronized subtitle track. It shows actual
offline tools/conflict/unavailable local capability, no live-model success. It is not a finished
1–2 minute narrated submission video. New 115-second judge guide and video plan are ready for
owner recording; no media was generated to fabricate product/model behavior and nothing uploaded.

New release readiness, competition fact check and English unsubmitted Devpost draft are supplied.
Official dates/rule wording were browsed; references and inconsistencies are documented rather
than a unilateral eligibility conclusion. Public source, license decision, final accessible
original video and remote CI remain owner actions. No Git remote exists, no push/submission/public
listener or LICENSE selection occurred. Python 3.11/Ubuntu were not available for execution;
Linux/macOS/other browsers/remote CI remain UNVERIFIED / NOT RUN. No system tools installed.

## Protected SHA-256 and local history

| Original artifact | Final unchanged SHA-256 |
| --- | --- |
| User data/traceweaver.rl, 21 nodes/27 edges, 73,728 bytes | 3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3 |
| Judge traceweaver-demo.rl, 51/67, 110,592 bytes | 29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239 |
| Judge MANIFEST.json | 50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab |
| Sprint 02 gold | 6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8 |
| Sprint 03 explanation gold | e716b63860712d9aaef23ac2b8a61b2bb77c225ce0359d8a36749cd65d2224cb |

Original fixture, packaged fixture, evaluation/report/G8 source and historical docs/image hashes
match the starting inventory. OVERNIGHT_PROGRESS is append-only and its original byte prefix
is preserved. All legacy test bytes unchanged except the two authorized exact route assertions.
Existing main and starting commit ancestry retained; no branch created, history rewritten or
database reset. Git commits already observed:

| Commit | Successful milestone |
| --- | --- |
| 8e022bb | Verified baseline and safety decisions |
| 0558418 | Native first-screen proof and protected historical browser captures |
| 8ab1e27 | Strict native investigation tools |
| 6a46081 | Bounded native model rounds and unsupported final rejection |
| 6bfcc6e | Same-tool deterministic rehearsal and CLI |
| 9c49bf7 | Independent new gold freeze before execution |
| adacd13 | Checkout-stable LF digest pin, no label change |
| 65e24ff | Guarded native UI actions and inspectable steps |
| 6ef7def | Frozen evaluation, external native runtime, actual evidence/captures |

The final documentation/audit commit contains this report and checkpoint continuation; identify
its exact hash with `git log -1` (also reported after observation in final response). No guessed
self-referential future commit hash is written here. Resume instructions and blockers are in
`docs/SPRINT_06_PROGRESS.md`. No autonomous background continuation is implied.
