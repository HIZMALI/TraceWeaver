# TRACEWEAVER — OVERNIGHT O4/O5 MISSION REPORT

Overall: **PASS for the local judge release candidate**, with the explicit research/platform
limitations below. G0–G9 executed. No failed test is represented as a pass. G8 retains one invalid
frozen question openly; thirteen other independently frozen questions support the limited study.
This is a local product/demo result, not production certification or a competition result.

## Repository and execution boundary

- Existing branch: **main**, unchanged throughout. Starting HEAD:
  `0783201fb5d83c072fe215cf23135eb165a2213a`.
- Ending tested implementation HEAD:
  `ded79a07b948a5a10814e07fb639a34b8c3859ab`.
- Working tree was clean at baseline and after that implementation commit. This report and its
  ledger reference are a subsequent documentation-only commit; `git log -1` identifies that
  final report commit without a self-referential hash inside its own contents.
- Baseline audit timestamp: 2026-11-13 00:08:29 UTC. Final verification/report: approximately
  01:49–01:55 UTC. The supplied backlog was executed in this actual session; no ten-hour runtime,
  unattended continuation or future background execution is claimed.
- No branch/worktree switch, history rewrite, push, remote creation, database reset, user-store
  writer, model pull, system-wide installation, public listener, tunnel or submission occurred.
- No remote is configured in this checkout. Remote CI is **UNVERIFIED**. Test processes owned by
  this run were stopped; ports 8765–8774 had no remaining owned listener at closeout. The existing
  Ollama service was left running.

## Gate acceptance

| Gate | Status | Actual acceptance evidence |
| --- | --- | --- |
| G0 | PASS | Clean main audited; original source/contracts/rules inspected; 337 pytest passed in 47.79s, Ruff/pip clean; native counts and hashes captured; architecture decision note written before implementation |
| G1 | PASS | Built Vite/React/TypeScript console consumes actual native API; original claims, counts and uncertainty visible; initial Chromium smoke rendered 14 INC-001 edges without page errors |
| G2 | PASS | Directed proof explorer, candidate/change/evidence/claim/pair drilldown, timeline/gaps, visual filters and deep links; native checks validate every displayed edge and authoritative label/domain; frontend mutation tests reject forged paths/time/snapshot |
| G3 | PASS | Strict bounded privacy DTO, single worker-local reader, unchanged legacy responses, numeric-loopback boundary, generic errors, real lookahead/caps, concurrency and actual cross-process writer-lock tests; protected bytes unchanged |
| G4 | PASS | **36/36 actual Chromium scenarios**, six default screenshots plus one live-model capture; four viewports, keyboard/focus, reduced motion, equivalent 200% reflow, actual error/adversarial stores; zero axe violations in the tested default desktop state |
| G5 | PASS | No inference on GET/load. Explicit capability click, chosen installed model and confirmation; bounded exact-origin POST, source fingerprint, single in-flight action, existing opaque-ID firewall. One genuine qwen3:8b UI invocation accepted 7 claims / 17 citations |
| G6 | PASS | PowerShell launch/check actually executed; clean external npm ci/build; fresh-source wheel, non-editable external install, Node-free server PATH and actual Chromium/native UI verified |
| G7 | PASS | 110-second real screen-action guide, fact-check table, English unsubmitted Devpost draft, seven genuine captures and honest three-scale local measurements; no finished video claimed |
| G8 | PASS, limited study | Fourteen questions frozen before either arm ran; thirteen are valid after disclosed R13 gold-assumption erratum. Same input fields/edges; actual native vs unchanged lexical baseline, full ID/edge/metric/timing outputs, first failed selector output preserved; no universal accuracy/speed claim |
| G9 | PASS | Final **420 pytest / 58 frontend / 36 Playwright**, old **20/20 + 19/19** evaluations; Ruff/pip/actionlint clean; final wheel/browser, protected originals, Markdown links and staged artifact/pattern audits pass; local commits only |

## Implemented product and contracts

The console includes incident search/navigation, persistent synthetic/read-only notices, returned
scope metrics, bounded window/cap controls, deterministic directed layout, fit/zoom and selected-path
focus, five visual filters, a keyboard-accessible path alternative, candidates and included changes,
evidence ledger, UTC timeline, structured comparisons, gaps/next checks, typed citation inspector,
URL/back navigation, guided manual demo and responsive Graph/Inspector/Details views.

Nodes/edges come from actual returned candidate/change/evidence/claim paths. Stored source/target
determine arrows; REVERSE is traversal metadata. For example:

`INC-001 → SVC-PAYMENT → SVC-AUTH ← DEP-001 → CHG-001`

Native relationships are AFFECTS, DEPENDS_ON, **DEP-001 TARGETS SVC-AUTH**, and INCLUDES_CHANGE.
DEP-002 separately targets SVC-PAYMENT. INC-002 legitimately returns two DEP-003/target pairs;
the UI keys deployment/target pairs separately rather than collapsing distinct targets.
CASE-INC actually returns six pairs, eleven evidence records, one HEALTHY/FAILED conflict and two
UNDETERMINED comparisons. Orphans retain incident/evidence proof without an invented service.
Unknown/naive times stay unknown. Source refs/prose remain withheld. `TRACEABLE` is metadata
quality, `NOT_PERFORMED` is external verification, and cause remains `NOT_ESTABLISHED` everywhere.

Existing health/list/context/investigation/explanation response contracts remain unchanged.
New routes are:

| Route | Behavior |
| --- | --- |
| GET /console/incidents | Bounded privacy projection of actual native incident list |
| GET /incidents/{id}/dashboard | Versioned safe Investigation/Explanation bundle from one native reader; source/view fingerprints |
| POST /console/models/capabilities | Explicit local click only; eligible actual installed tags, no pulls |
| POST /console/selection | Confirmed chosen model, exact source fingerprint/options; existing opaque-ID selection and citation firewall |
| GET / and /assets/* | Built package resources; no catch-all API fallback |

The browser verifies strict DTOs, source/view scope, digest, requested incident/options and cited
paths/times before highlighting. Abort/sequence guards prevent stale responses replacing current
context. Native label audit rejects ambiguous identities and off-schema edges. The ordinary
dashboard uses seven native queries in one read-only worker connection, then closes before
explanation rendering; optional inference closes its native reader before any provider request.

New console Host must be numeric 127.0.0.1 at the actual ASGI port; supplied Origin must match.
POST requires exact Origin/local client, exact application/json, at most 2048 bytes, shallow
duplicate-free JSON, a two-second body deadline and one in-flight local action per server process.
No arbitrary provider URL/prompt/tools/Cypher/path is accepted. Strict OpenAPI request schemas
document the same manually bounded Pydantic parsing. There is no CORS or credential forwarding.
Use one worker and the single-origin launcher; Vite does not rewrite Origin for model actions.
Legacy GET compatibility is retained; this is a local single-user surface, not authentication.

See [dashboard contract](DASHBOARD_CONTRACT.md) and
[architecture decisions](OVERNIGHT_ARCHITECTURE_DECISIONS.md).

## Actual verification results

All commands used the project virtual environment and real embedded Relate. Final source gates:

```text
.venv/Scripts/python -m pytest -q
420 passed in 51.56s

.venv/Scripts/python -m ruff check .
All checks passed!

.venv/Scripts/python -m pip check
No broken requirements found.

npm --prefix web run typecheck       PASS
npm --prefix web run lint            PASS
npm --prefix web test                58 passed, 2 test files
npm --prefix web run build           PASS (client-library directive warnings disclosed)
npm --prefix web run test:e2e         36 passed (42.9s)
Playwright: expected=36, unexpected=0, skipped=0, flaky=0

actionlint 1.7.12                    PASS (local syntax check, not remote CI)
```

The original **337** cases remain, with **83 added Python cases**. No skip, xfail, deleted case or
weakened domain assertion hides a failure. The only changes to pre-existing tests are the two
intentionally exact OpenAPI route/method-set assertions: four authorized console routes were
added, while every legacy route still asserts GET only. All other old tests/source services are
byte-identical. New cases cover native paths/labels, coherence/privacy/caps/errors, file immutability,
thread ownership, concurrency, local action guards/firewall, launch checks and the actual study.

Frontend unit inputs are explicitly native-recorded public synthetic DTOs. Controlled component
and provider tests are identified as controlled tests, never full-stack/live-model evidence.
Playwright uses actual Python servers and real judge or freshly allocated temporary Relate stores;
there are no mocked normal graph responses. The final suite adds explicit INC-002, search,
undetermined comparison, missing-source, phone drawer, reduced-motion, no external request and
zoom/fit checks to the original 28 scenarios. Axe is automated evidence for the tested default
desktop state, not proof of complete accessibility or every assistive technology.

Old evaluations were rerun with **new** output paths, preserving old artifacts:

```powershell
.\.venv\Scripts\python.exe -m traceweaver evaluate --suite evaluation/cases.json --output .verification/overnight/graph-evaluation-final.json
.\.venv\Scripts\python.exe -m traceweaver evaluate-explanations --suite evaluation/explanation_cases.json --output .verification/overnight/explanation-evaluation-final.json
```

Graph: **20 passed / 0 failed**. Explanation: **19 passed / 0 failed**, 181/181 native matched
edges, 133/133 controlled adversarial proposals rejected. These are synthetic semantic/citation
regressions, not source truth, whole-graph accuracy or live-model accuracy. The offline evaluation
explicitly does not invoke a live model.

Ignored local audit artifacts include final-pytest.txt, playwright.json, final-build.txt,
independent-install.json, final-install-output.txt, final-audit.json, performance.json, live-local.json
and both fresh evaluation outputs under `.verification/overnight/`. They were not staged as public logs.

## Mandatory adversarial matrix

| Boundary | Result | Actual coverage and limits |
| --- | --- | --- |
| HTML/JS/private-looking source metadata | PASS | Native adversarial store + actual browser; title withheld, no script execution; React text rendering |
| Large/deep browser JSON | PASS | Unit parser byte/depth/stream bounds; not a claimed native malicious-response E2E |
| Query injection/window/cap errors | PASS | Parameterized native reads, strict range tests, safe new-route 422 without echoed values |
| Reversed stored edge forgery | PASS | Native edge checks + frontend path-layout mutations; reverse TARGETS remains deployment → service |
| Valid ID/wrong target/time/citation | PASS | Server semantic firewall plus client target/path/time membership and request binding tests |
| Other incident candidate/snapshot | PASS | Client scope/request checks and actual back/rapid navigation; no ghost proof |
| Orphan evidence | PASS | Native CASE-E-ORPHAN and actual selectable two-node path |
| Unknown/naive/AFTER/zero window | PASS | Existing native temporal cases + frontend/browser checks; no guessed ingestion time |
| Structured comparison context | PASS | Existing native taxonomy/firewall + actual conflict/undetermined selection |
| TRACEABLE vs UNVERIFIED_EXTERNAL | PASS | Separate strict fields and native cases; external truth always NOT_PERFORMED |
| Source/display/catalog caps | PASS | Native capped fixtures + 300-node browser scale; visible partialness/omissions |
| Inference via GET/load | PASS | Provider-forbidden tests, 405 on action GETs, browser initial POST count zero |
| Forged Origin/Host/name/port | PASS | Strict local boundary/protocol cases before provider; no CORS |
| Unknown claim / provider prose | PASS | Controlled adapter/firewall rejection tests; separate from genuine qwen3 run |
| Unavailable/timeout provider | PASS | Controlled protocol cases; NONE/empty accepted claims, no hidden fallback-as-AI |
| Missing/corrupt/writer-locked store | PASS | Actual native missing/corrupt cases, separate-process held writer and generic 503 |
| Concurrent refresh / response binding | PASS | Abort/sequence/snapshot guards, native-recorded wrong-request tests and actual rapid/back navigation |
| Back/forward/filter/source stability | PASS | Actual browser scope checks; filters don't edit source or fingerprints |
| Double clicks / cancellation | PASS | Controlled component in-flight/abort and native-backed single-action lock tests; daemon cancellation not promised |
| Protected judge/user bytes | PASS | Before/after SHA-256/native counts, all original protected files audited unchanged |

Pattern minimization is not a universal secret detector. Fixed trusted loopback daemon/model
authenticity and operating-system compromise are outside this single-user threat model.

## Genuine browser captures

All seven images are actual Chromium screenshots from this run and were visually inspected.
No generated image, substitute graph or polished video is represented as a screenshot.
Desktop viewport is 1440×900; full-page capture includes lower content. Phone is 390×844.

| Capture | Actual scenario / alt text |
| --- | --- |
| [01-connected-context](screenshots/01-connected-context.png) | INC-001, 11 nodes / 14 actual directed edges, two competing pairs, deterministic claims |
| [02-claim-proof](screenshots/02-claim-proof.png) | Selected admitted DEPLOYMENT_BEFORE_ONSET claim and exact graph/temporal proof |
| [03-structured-disagreement](screenshots/03-structured-disagreement.png) | Actual CASE-INC HEALTHY/FAILED pair, matched service/signal/window and separate undetermined pairs |
| [04-gaps-next-checks](screenshots/04-gaps-next-checks.png) | Actual source gaps and server-provided next checks |
| [05-phone-records](screenshots/05-phone-records.png) | Phone Details view with real candidate records and persistent uncertainty |
| [06-safe-unavailable](screenshots/06-safe-unavailable.png) | Genuinely missing temporary store, generic error without private path |
| [07-live-local-selection](screenshots/07-live-local-selection.png) | Genuine installed qwen3:8b invocation, deterministic/local selection side by side |

Also tested 1024×768 and 768×1024; 720×450 provides 200% equivalent reflow for the desktop width.
No full-page overflow, keyboard focus trap or axe violation was observed in the tested flows.
Dense global edge labels can overlap; focus a selected path or use the exact accessible list.

## Genuine optional model result

Executed explicitly with `node web/e2e/live-local.mjs` through the real built app's capability,
model choice, confirmation and selection buttons. Actual already-installed model: **qwen3:8b**,
fixed provider **127.0.0.1:11434**, elapsed **4250ms**. Requested/executed **OLLAMA**,
`ai_generated_selection=true`, `PARTIAL_CONTEXT`, **7 validated claims / 17 citations**,
no rejection codes. Source fingerprint:
`d05166378e55098b88a4c71e69095cc206e075031a3e46ce1a5643f70c1b5520`.

Accepted opaque claim IDs only:

```text
C-137d0d5cc03effe27c154b25
C-5b118ea365ea35831a7f99ad
C-54c4c370e92e2f2bc7f5d109
C-8cbec333b5a692766348f324
C-a44ded691c6db0b178ce1748
C-a5a7d81f08112511b9059000
C-02c51c9fdd50a9a03b37c175
```

This was one actual runtime observation, not LLM accuracy evidence or a promised future selection.
No raw provider response/prompt was persisted. No model/daemon was installed, pulled or restarted.
Default use remains fully functional without Ollama. Browser abort cancels waiting; server/provider
work can continue to its bounded deadline and retains the in-flight lock.

## Independent package and exact launch

Environment actually used: Windows 11 x64 build 26200, Python **3.14.0**, relate-db **1.0.0**,
pytest **9.2.0**, Ruff **0.17.4**, Node **24.13.1**, npm **11.8.0**, Chromium **158.0.8127.18**.
Pinned frontend runtime: React/React DOM 19.3.1, @xyflow/react 12.12.1, Zod 4.6.7, Lucide 1.72.0.
Final clean npm ci audited 195 packages with **zero vulnerabilities**. The targeted minimatch
11.0.1 override was reviewed; no automatic unrelated dependency upgrade was used.

Final production JS **555.61kB / 172.19kB gzip**, CSS **37.41kB / 7.92kB gzip**. Client-library
“use client” directive warnings remain; actual client rendering works, no SSR claim is made.

`scripts/build_judge_wheel.py` builds in a fresh owned source copy, avoiding stale setuptools
build/lib hashed assets. It validates one JS/CSS generation, upstream notices and no database.
Final wheel: **273,904 bytes**, SHA-256
`102a805a564ad420c626b6d3442a1f24eec9293f32ffd32eabaccd8e8659c41f`.
It was installed **non-editably in a new virtual environment outside the checkout**, constrained
by the existing Python lock. Import path was outside the repo; pip check passed. A copied intact
judge bundle was verified, then the installed app ran with **Node absent from server PATH**.
HTTP index/assets/health and actual Chromium 14-edge rendering passed with zero page errors;
copied and original stores remained unchanged. Clean copied npm ci/build also reproduced identical
asset bytes. Earlier wheel hashes remain historical G6 evidence, not the final artifact identity.

From the prepared checkout, launch:

```powershell
.\scripts\check-judge-demo.ps1
.\scripts\start-judge-demo.ps1
```

Open [http://127.0.0.1:8000/?incident=INC-001](http://127.0.0.1:8000/?incident=INC-001).
Both PowerShell flows actually ran. Ctrl+C stops the foreground server; `-Port 8001` selects
another local port. From a fresh checkout follow README prerequisites and `-Build`; scripts
never install system tools or seed a store. A wheel install uses
`python -m traceweaver.judge --bundle <intact-judge-demo-directory>` and needs no Node/checkout.

Build another wheel with project Python only after building web:

```powershell
.\.venv\Scripts\python.exe scripts/build_judge_wheel.py --output .verification/overnight/another-new-wheel-directory
```

See [release readiness](RELEASE_READINESS.md) and [dependency notices](DEPENDENCY_LICENSES.md).
Full notices for the 25 installed frontend production-tree packages accompany the built assets.
No project license was assigned to the owner's existing work; owner selection precedes public release.

## Protected state: before equals after

| Artifact | Native counts / bytes | SHA-256 at start and finish |
| --- | --- | --- |
| data/traceweaver.rl | 21 nodes / 27 edges; 73,728 bytes | 3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3 |
| examples/judge-demo/traceweaver-demo.rl | 51 / 67; 110,592 bytes | 29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239 |
| examples/judge-demo/MANIFEST.json | Unchanged | 50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab |
| evaluation/cases.json | Original frozen gold | 6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8 |
| evaluation/explanation_cases.json | Original frozen gold | e716b63860712d9aaef23ac2b8a61b2bb77c225ce0359d8a36749cd65d2224cb |

Every pre-existing file under docs/, fixtures/, packaged fixtures, evaluation/, reports/ and the
judge bundle is byte-identical to baseline. No database or environment/static build directory was
staged. Exactly seven pre-existing files changed: .gitignore, AGENTS.md (explicit mission POST
exception), README.md, pyproject.toml, api.py and the two exact OpenAPI route assertions. New
modules/docs/web/tests are separate. Existing engine/investigation/explanation/firewall/CLI code
and dependency locks were preserved. Staged audit checked local Markdown links, unintended private
paths/credential patterns, store/environment files and whitespace; it is not a universal secrets proof.

## Measurements and retrieval study

See [local performance](LOCAL_PERFORMANCE.md) for real samples, hardware and methodology.
Three fresh temporary native stores (14/17, 92/121, 332/441 nodes/edges) rendered 14/17,
92/121 and 300/399 visible nodes/edges. First-context loads were 330.39, 460.35 and 879.77ms;
six-repeat warm medians 116.22, 239.98 and 689.55ms. Seven proof-selection medians were 83.82,
145.97 and 303.87ms. Small-n nearest-rank p95 and API/network/owned-process memory caveats are
explicit. Initial Windows shim-only memory sampling was rejected and corrected before publication.
These measured the earlier 555.43kB client build; final request-binding hardening adds about
0.18kB. No claim that final or production timing is identical is made. Row caps do not bound RAM.

G8 [study design/results](../evaluation/graph-vs-flat/README.md) uses the same public fields and
all edge facts in both arms. The graph arm receives typed intent and uses unchanged native
investigate; the lexical arm gets question text/anchor/type/caps and fixed BM25-like settings,
not expected IDs/cardinality. No edge information was secretly withheld from flat records.
Fourteen questions were frozen in commit 1c8d1fa, hash
`53e089d433a5f9de6c00105aa7837e1d9ae29016750ef6802f4cc0fde095db81`.

First raw results (native 12/14, flat 2/14) are preserved. The new evaluation-only R11 selector
omitted structured service consistency; repairing it yielded native raw 13/14. R13's depth-first
cap expectation contradicts the pre-existing ID-before-LIMIT query contract. That frozen expected
ID is deliberately unchanged and its raw failed comparison retained. [ERRATA](../evaluation/graph-vs-flat/ERRATA.md)
identifies the invalid question independently from the unchanged query source. Thirteen valid
frozen questions remain; do not turn raw 14-case totals into accuracy. All per-case IDs, TP/FP/FN,
null denominators, native matched edges and first/warm timing summaries are published.
Median of per-question warm medians: native **4.4291ms**, flat **0.0694ms**. Flat is much faster on
this tiny indexed corpus; native enforces the declared relationships. Intent/setup asymmetry,
fixed-k extra hits and authored synthetic IDs limit interpretation. No superiority panel, parameter
retuning, production/root-cause metric or general winner claim was added.

## Failures found and repaired

- Native GraphPath → strict ProofPath conversion and initial TypeScript CSS typing fixed before G1.
- A new source-cap test initially conflated source truncation with selected claim subset; corrected
  to the existing independent contract, without changing legacy expectations.
- Browser import/readiness checks fixed before successful runs; real edge mounting is awaited.
- Added provenance checks initially treated EVIDENCE's null provenance fields like PROVENANCE;
  corrected to each typed citation contract.
- Actual axe heading order/accessibility-name faults repaired without excluding rules. New test
  strings/profile IDs were corrected to actual UI/native values. Explanation status is now visible.
- The second old OpenAPI GET-set assertion initially failed on authorized POST additions; only
  those exact method exceptions were added. Full old suite reran successfully.
- Audit helper initially compared unordered rg file enumeration; direct protected hashes were
  checked, then full records compared in sorted order. No changed bytes were ignored.
- G8 evaluation selector/gold defects remain transparently documented as above; old gold unchanged.
- Final review added expected-request binding, strict POST OpenAPI documentation, bounded excessive
  length headers and actual new-route writer-lock coverage. An INC-002 test's single-pair assumption
  was corrected to assert both real deployment/target pairs explicitly.
- Repeated in-place package builds retained old hashed assets in ignored build/lib. The fresh-source
  builder removed that packaging hazard; the final single-generation wheel was independently retested.
- Trailing whitespace in new study Markdown/notices was removed; future study files explicitly use LF.

## Local commit record

| Commit | Verified milestone |
| --- | --- |
| 6662e52 | Baseline and architecture decisions |
| 496c289 | Read-only connected console |
| d93625e | Native identities/directions, proof explorer and frontend tests |
| 6c55620 | Local boundary/privacy and native regression |
| 1044204 | Real browser/accessibility/responsive verification and captures |
| 70efbf3 | Guarded explicit local selection and genuine runtime evidence |
| 1372bdc | Launcher, independent package and OSS notices |
| cf1ec55 | Judge presentation and native browser measurements |
| 1c8d1fa | Independent gold/design freeze before study execution |
| 79221f1 | Actual study outputs and disclosed erratum |
| ded79a0 | Final request/OpenAPI/package/browser integrity gates |

All are local descendants of the original main history. The final report is a documentation-only
follow-up. There was no push, publication, external messaging or Devpost submission.

## Remaining limits and next actions

- **UNVERIFIED:** remote CI, Python 3.11, Ubuntu/Linux/macOS, Firefox/Safari and other assistive
  technologies. Local actionlint and Python 3.14/Chromium do not establish those outcomes.
- **NOT PRODUCED:** polished competition video. The [110-second guide](JUDGE_DEMO_GUIDE.md),
  [fact check](DEMO_FACT_CHECK.md) and [unsubmitted Devpost draft](DEVPOST_DRAFT.md) are ready
  for the owner to rehearse, record and review.
- **Declared limits:** partial paths/caps, dense full-context edge labels, no independent source
  authentication/causal verdict, native high-degree RAM/work not generally bounded, local daemon
  trust, one server worker, client cancellation not guaranteed to cancel daemon work.
- **Study limit:** R13 frozen expectation invalid; raw first/final outputs and erratum retained.
  Treat thirteen eligible synthetic tasks as an illustration, not a general benchmark.
- Before public submission: owner chooses project license, verifies competition terms, records
  an actual reviewed video and runs the target platform. No production connector, remediation,
  cloud service or public hosting was introduced outside the mission.

Resume/operation entry point: [overnight progress](OVERNIGHT_PROGRESS.md). Development is complete
at the tested local checkpoint; launch the console using README when needed.
