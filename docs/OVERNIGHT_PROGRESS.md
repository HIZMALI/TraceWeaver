# Overnight O4/O5 progress ledger

This is a resumable record of actual completed work. No background continuation is promised.
Starting main: 0783201fb5d83c072fe215cf23135eb165a2213a. No user edits at start. Local commits only.

## Latest successful gate

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
| G8 | IN PROGRESS | Freeze independent questions before running fair graph-vs-flat study |
| G9 | PENDING | Full regression, measurements, protected-file/staged audit, final report |

## Resume instructions

Read this ledger and OVERNIGHT_ARCHITECTURE_DECISIONS.md; inspect Git status before edits.
Do not reset or overwrite existing work. Next action: freeze G8 independent gold before execution,
then run/report study and final G9 regression/package rebuild. Current app is source-built and served by FastAPI
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
