# Overnight O4/O5 progress ledger

This is a resumable record of actual completed work. No background continuation is promised.
Starting main: 0783201fb5d83c072fe215cf23135eb165a2213a. No user edits at start. Local commits only.

## Latest successful gate

G9 PASS — 2026-11-13 01:49 UTC. Final complete pytest: 420 passed in 51.56s (337 original +
83 additions), zero failures/skips. Ruff/pip/actionlint clean. Frontend type/lint/build pass;
58 unit cases and 36 actual Playwright cases pass (42.9s, zero unexpected/skipped/flaky).
Old graph evaluation 20/20 and explanation evaluation 19/19 rerun to new ignored output paths.
Final fresh-source wheel 273904 bytes, SHA-256 102a805a564ad420c626b6d3442a1f24eec9293f32ffd32eabaccd8e8659c41f,
independently installed non-editably outside checkout: Node-free server, actual Chromium/native
14-edge UI, no page errors. Both original stores and all original docs/fixtures/gold/reports
remain byte-identical; only seven authorized pre-existing files changed, plus new sprint files.
Final audit checks local links/staging/private patterns. No owned test ports remain listening.

G9 repairs: bind browser response to requested incident/options; strict POST OpenAPI body schemas
without eager unbounded parsing; excessive length-header bound; actual new-route writer lock test.
Added eight browser scenarios (INC-002's two legitimate DEP-003 target pairs, search, undetermined,
missing source, phone drawer, reduced motion, no external requests, zoom/fit). New INC-002 test
initially assumed a single deployment/target pair; changed to assert both actual pairs explicitly.
Repeated in-place setuptools builds retained old hashed assets; a fresh-copy wheel builder now
checks exactly one JS/CSS generation. Final package verification reran after the fix. Markdown
trailing whitespace was removed and future study output uses explicit LF. No legacy gold changed.

G8 PASS WITH DISCLOSED STUDY LIMIT — 2026-11-13 01:35 UTC. Fourteen questions were frozen in
1c8d1fa before either arm ran; actual same-input 51/67 native vs BM25-like record study executed.
First raw output native 12/14, flat 2/14 preserved. R11 exposed a new evaluation-selector missing
structured-service consistency check; fixed, native raw result 13/14. R13's frozen depth-first
cap assumption contradicts unchanged pre-existing query ordering (ID before LIMIT). Gold remains
unchanged; ERRATA identifies that invalid question, with its raw mismatch preserved. Thirteen
valid frozen questions remain; native exact sets match all thirteen, flat matches negative controls
and has partial/extra hits detailed per case. No accuracy/superiority panel or universal claim.
Flat is faster: median of per-question warm medians 0.0694ms vs native 4.4291ms; declared setup/
intent asymmetry applies. Three new actual/native/metric tests pass, Ruff clean. First new token
unit assertion incorrectly expected an underscore token; corrected to the frozen tokenizer's
documented component tokens. Baseline constants/tokenization/expected IDs were not retuned.

G7 PASS — 2026-11-13 01:23 UTC. Added the actual 110-second judge flow, fact-check mapping,
English unsubmitted Devpost draft and LOCAL_PERFORMANCE.md. Seven genuine captures support the
storyboard; no video claimed. Three new native scales (14/17, 92/121, 332/441 stored nodes/edges)
were actually rendered seven times each; capped display 300/399, no page errors. Corrected
process-tree memory measurement after detecting Windows virtualenv shim-only sampling, then reran.
Ruff/frontend lint and diff checks clean. License collector now removes only trailing blank lines;
the earlier G6 wheel remains historical evidence and the final package will be rebuilt/rechecked.

G6 PASS — 2026-11-13 01:15 UTC. 414 Python tests passed in 45.73s, Ruff/pip clean.
Clean external npm ci/build succeeded with zero audit vulnerabilities and identical asset bytes.
Fresh external non-editable wheel installation served the actual UI with Node absent from server
PATH; Chromium rendered 14 native edges with no errors. Wheel c0ee1ff20d91d53935403e5735227b8ef6fe762e14a1c4b722e648da214ec46c.
PowerShell source launcher and read-only check both actually ran; owned processes stopped.
25 upstream frontend notices collected from installed runtime tree; no system tools installed.
See RELEASE_READINESS.md and DEPENDENCY_LICENSES.md. Original graph files remain intact.

G5 PASS — 2026-11-13 01:09 UTC. Full pytest 410 passed in 52.25s, followed by 29 focused
selection tests (two additional thread-close/no-GET-provider cases included). Frontend 55 passed,
lint/type/build passed, actual Playwright 28 passed in 29.8s. Ruff/pip check clean. A genuine
single qwen3:8b invocation through UI confirmation completed in 4250ms: OLLAMA, AI selection=true,
PARTIAL_CONTEXT, 7 claims / 17 citations, no rejection. Source d05166378e55098b88a4c71e69095cc206e075031a3e46ce1a5643f70c1b5520.
No model pull/install or raw provider storage. Actual installed tags include qwen3:8b and
openweft-qwen3:8b; UI selects neither automatically. Screenshot 07 is genuine and visually reviewed.
All protected bytes/counts unchanged. Tests distinguish controlled protocol cases from this live run.
Initial regression failed the second old exact GET-method assertion; extended only the two
authorized POST exceptions, preserving GET-only assertions for every legacy route. Rerun passed.

G4 PASS — 2026-11-13 01:01 UTC. 28/28 actual Playwright scenarios passed in 29.2s;
48 frontend cases, lint/type/build passed. Axe reports zero violations on the tested desktop
state. Four viewport sizes and 720px equivalent 200% reflow have no page overflow. Actual
missing/adversarial/empty/capped stores, navigation and keyboard flows pass. Six genuine public
screenshots captured; desktop, selected claim and phone images visually reviewed.
First rounds found incorrect new test strings/profile ID plus actual heading/accessible-name
issues; fixed without excluding axe rules. Added visible explanation status. The audit helper
had compared unordered rg enumeration as a list; corrected to compare sorted full records.
Direct hashes confirmed both stores unchanged before that helper correction.

G3 PASS — 2026-11-13 01:00 UTC. Full pytest: 383 passed in 56.45s; Ruff clean.
46 added native/dashboard/local-boundary cases now protect the console. New routes reject
alternate/duplicate Hosts and cross-origin reads without affecting legacy API contracts.
Generic 422 errors never echo private input. Actual Chromium/native smoke reran successfully.
Single-worker read-only ownership, immutable data checks and safe metadata projection pass.
See DASHBOARD_CONTRACT.md for the exact boundary and privacy limitations.

G2 PASS — 2026-11-13 00:54 UTC. Full Python suite: 366 passed in 45.95s. Frontend:
48 unit cases passed; typecheck/build/lint passed. Actual Chromium smoke: 14 INC-001 edges,
CASE-INC comparisons, no page errors. Every displayed kind is now checked with one bounded
native label query in the same reader (seven queries total). Duplicate identities and
off-schema stored relationships are rejected. Stored arrows and reverse traversal remain distinct.
Selected paths can be focused and the evidence layout wraps. Unit inputs are explicitly
recorded native API data, never E2E substitutes. Protected hashes/counts unchanged.

G1 PASS — 2026-11-13 00:43 UTC. Actual console compiled/typechecked/linted and ran in Chromium
158.0.8127.18 with native judge-store requests: INC-001 rendered 14 real edges, CASE-INC displayed
its actual comparison records, zero page errors. Full Python suite: 363 passed in 41.07s,
including all original 337 and 26 new native dashboard cases. Ruff/pip check clean.

G0 PASS — 2026-11-13 00:06 UTC. Baseline pytest: 337 passed in 47.79s; Ruff and pip check clean.
Node 24.13.1, npm 11.8.0, Windows x64/Python 3.14.0, Relate 1.0.0. Existing data/judge files
match previously reported hashes and native counts. Exact initial state is recorded under
ignored .verification/overnight/baseline.json. Architecture decisions recorded before coding.

## Gate status

| Gate | Status | Evidence / next action |
| --- | --- | --- |
| G0 | PASS | Native baseline, protected hashes, source/contracts inspected, decision note |
| G1 | PASS | Actual native snapshot console, type/lint/build and Chromium smoke; 363 Python tests |
| G2 | PASS | 48 frontend cases, 29 native dashboard cases, real arrows/labels and browser smoke |
| G3 | PASS | 383 total tests; strict new-console Host/origin, safe errors, native read-only snapshot |
| G4 | PASS | 28 actual browser scenarios, zero axe violations, six real captures and responsive checks |
| G5 | PASS | Strict local POST actions, 29 protocol/native cases, actual qwen3:8b UI inference |
| G6 | PASS | External clean npm/wheel/browser, Node-free server, verified PowerShell launch/check |
| G7 | PASS | Timed genuine demo/storyboard, fact check/draft/screenshots and actual local measurements |
| G8 | PASS | Actual frozen study; R13 invalid assumption retained/disclosed, thirteen eligible questions |
| G9 | PASS | 420/58/36, 20/20 + 19/19 evaluations, final clean wheel/native browser and protected audit |

## Resume instructions

Read this ledger and OVERNIGHT_ARCHITECTURE_DECISIONS.md; inspect Git status before edits.
Do not reset or overwrite existing work. Implementation and checks are complete. Next action is
read OVERNIGHT_MISSION_REPORT.md, inspect clean main and launch the judge demo when needed.
There is no ongoing background development/server. Current app is source-built and served by FastAPI
at one loopback origin. Rebuild web after frontend edits. Browser files live in ignored
.verification/overnight/browsers; web/e2e/smoke.mjs configures that path before importing Playwright.
All tests that write graph data must use new OS temporary stores. The existing judge artifact,
manifest, fixtures, saved examples and frozen reports/gold must remain byte-identical.

## Actual commands and failures

- git root/status/log/remote inspected; no remote configured/output and clean existing main.
- .venv Python: pytest -q (337 PASS), ruff check . (PASS), pip check (PASS).
- node --version / npm --version: v24.13.1 / 11.8.0.
- No application edits or test failures at G0; no model download/system installation/push.
- G1: npm typecheck/lint/build PASS; node web/e2e/smoke.mjs PASS with actual Chromium and native API.
- G1: initial new Python test incorrectly conflated source caps with selected_subset. Corrected
  it to assert the documented distinct dimensions: source truncated, all six catalog claims
  selected, selected_subset=false. Original tests/assertions unchanged except two new GET routes.
- G1: native GraphPath→strict ProofPath conversion fixed before passing regression. Initial
  smoke browser path was read before environment configuration; fixed import order, no global install.
- Dependency review: TypeScript 6.0.3 matches typescript-eslint peer range; happy-dom 21.0.4
  supports installed Node. jsdom's higher Node floor was rejected without changing system Node.
  Targeted minimatch 11.0.1 override fixes GHSA-g3hv-75wg-m249 in new lint tooling. Type/lint/build
  pass; reviewed npm audit reports zero vulnerabilities. No npm audit fix --force was used.
- Build reports client-only library "use client" directive warnings; actual production browser
  works. No SSR claim. Generated static assets and unreviewed screenshots remain ignored.

## Changed files / local commits

- G0 commit: 6662e52, baseline and architecture notes only.
- G1 files: safe dashboard models/service + GET dashboard/console list, static serving/package data,
  React/Vite/TypeScript web app + pinned lock/tools, actual smoke helper, 26 native Python tests,
  documented exact OpenAPI GET additions, README and ignore updates.
- G1 commit: 496c289451994533ba4025bca3fa3e25db1b3156.
- G2: native labels/domain audit, path focus/directional handles, 48 frontend tests and two
  public synthetic native-recorded unit inputs. New provenance check initially applied provenance
  fields to EVIDENCE citations, whose contract fields are null; corrected to validate provenance
  fields only on PROVENANCE, while EVIDENCE still requires actual source membership.
- G2 browser smoke initially sampled the DOM before edges mounted; now waits for a real edge.
  Passing output above was rerun after the fix. No failed run was counted as PASS.
- G2 commit: d93625e. G3 adds local_console boundary, new native Host/privacy tests,
  safe request errors and developer console proxy adjustment. No old tests changed.
- G3 commit: 6c55620. G4 adds real browser runner/scenarios, accessibility repairs and public captures.
- G4 commit: 1044204. G5 adds console_selection, LocalSelection component, native/security and
  component cases, guarded dedicated POSTs, explicit AGENTS exception and real-model helper.
- G5 commit: 70efbf3. G6 adds judge.py, source launcher/check scripts, license collector/notices,
  installed-wheel browser helper, launcher cases and release/readme documentation.
- G6 commit: 1372bdc. G7 adds presentation documents and finite native browser-scale runner;
  license collector's trailing blank-line diff warning was corrected before this gate.
- G7 commit: cf1ec55. G8 preparation: 14 independent questions/expected IDs and fairness design
  authored from fixture literals before implementing/executing the new runner. Commit this freeze
  first; do not derive expectations from predictions or change old gold.
- G8 freeze commit: 1c8d1fa. New runner and both actual result versions, explicit ERRATA and
  native tests are separate from original Sprint 02/03 evaluations. No runtime application
  analyzer or API was changed for this study.
- G8 implementation/results commit: 79221f1. G9 tested implementation commit is recorded in the
  final mission report; the report is a subsequent documentation-only commit. Remote CI, Python
  3.11, Ubuntu, other browsers and a finished competition video remain UNVERIFIED / NOT PRODUCED.
