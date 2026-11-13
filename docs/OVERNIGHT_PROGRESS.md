# Overnight O4/O5 progress ledger

This is a resumable record of actual completed work. No background continuation is promised.
Starting main: 0783201fb5d83c072fe215cf23135eb165a2213a. No user edits at start. Local commits only.

## Latest successful gate

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
| G3 | IN PROGRESS | Strict privacy/snapshot/error/read-only guards and local-host boundary |
| G4 | PENDING | Actual browser tests, responsive/a11y/adversarial review, real screenshots |
| G5 | PENDING | Explicit secure local-only model action, genuine installed model if available |
| G6 | PENDING | Clean npm/wheel install, static assets and one-command launch/check |
| G7 | PENDING | Judge guide, fact check, draft and screenshot pack |
| G8 | PENDING | Independent fair retrieval comparison after P0/P1 pass |
| G9 | PENDING | Full regression, measurements, protected-file/staged audit, final report |

## Resume instructions

Read this ledger and OVERNIGHT_ARCHITECTURE_DECISIONS.md; inspect Git status before edits.
Do not reset or overwrite existing work. Next action: G3 local-host/snapshot/privacy hardening,
then actual G4 Playwright suite. Current app is source-built and served by FastAPI
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
