# TraceWeaver public release report

November 13, 2026. **Overall: PASS** for the implementation release and observed gates below.
Owner **HIZMALI**; repository **https://github.com/HIZMALI/TraceWeaver**; actual visibility/default
branch **PUBLIC / main**. Implementation pushed without rewrites:
`5e31b44b329095eaf3268eaef4499dbcf371598b`.

This report follows in a documentation-only commit. [Main's history](https://github.com/HIZMALI/TraceWeaver/commits/main)
identifies that revision; the CI table records the exact completed implementation run. The final
owner response records the subsequent pushed HEAD and its actual CI, without claiming a future
run inside this revision.

## P0–P11 evidence

| Phase | Result | Actual evidence |
| --- | --- | --- |
| P0 | PASS | Clean existing main; baseline `f99deb60d3a909298c9e2646693e951225b23c09`; hashes/native counts; authenticated HIZMALI; target initially absent |
| P1 | PASS | All-ref/all-object/current scan, Gitleaks plus source/binary/visual/identity review; no unresolved high-risk finding |
| P2 | PASS | Exact canonical Apache-2.0; truthful NOTICE; Python/npm SPDX; upstream notices retained; licensed wheel assertions |
| P3 | PASS | Tested source judge entry point; real graph/tool explanation; synthetic/offline/historical AI distinction; media disclosure; no fake hosted/video URL |
| P4 | PASS | 574 Python / 88 frontend / 54 browser; frozen 35/20/19; negative control; independent source/wheel/launcher checks |
| P5 | PASS | SHA-pinned least-privilege Windows/Ubuntu Python 3.11 and full frontend/native/package workflow; actionlint |
| P6 | PASS | Staged review, exact clean commit scanned again; protected hashes/counts and account/absent target rechecked before publication |
| P7 | PASS | Exact authorized public repository created; main-only normal push; remote SHA matched; Apache recognized; secret scanning/push protection enabled |
| P8 | PASS | Actual hosted Windows/Ubuntu Python 3.11 and Ubuntu frontend/browser/wheel jobs all successful on implementation SHA |
| P9 | PASS | Fresh anonymous HTTPS clone outside checkout, no credential helper/auth header; installed/built source; native startup/browser; clean clone; public files HTTP 200 |
| P10 | PASS | SUBMISSION_HANDOFF.md with real results/links and explicit owner actions |
| P11 | PASS | This redacted report, CI report and Turkish owner result; no Devpost/video upload |

## Audit, rights and publication scope

See [the audit](PUBLIC_RELEASE_AUDIT.md). Baseline inventory: **41 commits / 701 objects**, including
410 blobs, 41 commits and 250 trees. All 451 content objects / 11,174,214 bytes were read, including
four unreachable blobs. After the release commit the repeated full inventory covered **42 commits /
725 objects / 469 content objects / 11,370,791 bytes**, including six unreachable content objects.
Gitleaks current/history/all-content scans returned zero findings. Two supplemental private-host/IP
matches were individually reviewed X19 forbidden-output assertions; the gold stayed unchanged.
Raw values and detailed inventories remain ignored, never published.

All 26 historical image versions were visually inspected. The existing 7.28-second silent synthetic
technical clip remains historical evidence; no new recording/final narration was added. Largest
blob: 2,934,834 bytes. Only the exact intended synthetic judge .rl exists in public history. No
user store, environment, node_modules, model weights, dependency executable or private logs were
published. All existing history remains intact; no force push, reset or history rewrite occurred.

No unresolved secrets/content/rights blocker was found in the enumerated scope. This bounded
review is not a guarantee of secret absence or a legal certification. GitHub's checked secret-alert
list was empty. Secret scanning/push protection are enabled without bypass. Apache LICENSE is
11,358 bytes, SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
copied unchanged from the [Apache Software Foundation](https://www.apache.org/licenses/LICENSE-2.0.txt).
GitHub recognizes Apache-2.0. It covers eligible original work, not third-party dependencies,
trademarks or separate models/media. Installed Python/npm license inventories were reviewed;
required notices remain. npm audit and pip-audit against requirements-dev.lock each reported
zero known vulnerabilities at execution time, not a perpetual vulnerability-free guarantee.

## Local results and disclosed failure

Windows x64/Python 3.14: **574 passed in 98.22 s**, no skips; frontend **88 PASS**; Ruff, pip check,
typecheck, lint, build and actionlint passed. Initial browser result was **53 PASS / 1 FAIL**:
the first INC-001 edge stayed absent for seven seconds while React Flow nodes remained unmeasured/
hidden. An independent browser verifier overlapped that invocation. The retained trace does not
prove the underlying timing cause. After that process ended, the entire unchanged zero-retry
suite returned **54 passed in 45.5 s**. No test weakening, timeout change, gold adjustment or
application patch was used. Hosted Ubuntu subsequently passed the complete 54 too. The observed
initialization flake remains a disclosed reproducibility limitation.

Frozen suites: **agent 35/35, graph 20/20, explanation 19/19** into fresh ignored outputs.
Corrupted agent gold returned expected **exit 15 / one failure**; original gold was unchanged.
These synthetic/protocol tests do not establish production or live-model accuracy.

Local licensed wheel: 310,444 bytes, SHA-256
`9401551e971a24a2044643d07fbaae9e476c474387e63c9a035d1c86420bbcff`.
Exact LICENSE/NOTICE/SPDX and shipped frontend notices passed validation. Fresh source setup and
non-editable wheel installation outside the checkout both passed actual Chromium checks; the wheel
server PATH excluded Node. Each flow observed 14 native INC-001 edges, CASE-INC's one conflict/two
undetermined pairs and 4 tools / 23 queries / 8 claims / 11 citations, with zero page errors/foreign
requests. Missing/corrupt/locked owned copies returned generic 503 without fallback. The existing
PowerShell launcher served native health 51/67 and index 200 on numeric loopback; its read-only
judge checker passed. No preexisting store was seeded or written.

## Protected bytes and history

| Item | Actual result / SHA-256 |
| --- | --- |
| User store | **21 nodes / 27 relationships**, 73,728 bytes; `3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3` |
| Judge store | **51 / 67**, 110,592 bytes; `29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239` |
| Judge MANIFEST.json | `50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab` |
| Graph gold | `6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8` |
| Explanation gold | `e716b63860712d9aaef23ac2b8a61b2bb77c225ce0359d8a36749cd65d2224cb` |
| Agent gold | `dce5da3e7561029a8877fb03a9de86961509f728694b6c22e01155e82dfa6295` |

All match baseline; read-only native counts match. Of 263 baseline tracked files, only nine reviewed
release docs/metadata/workflow/build-helper files changed; the other 254 remain byte-identical,
including every old runtime source, test, gold/report, screenshot and tracked clip. No API,
citation-firewall or causality behavior changed. User .rl remains ignored and absent from the clone.

## Actual hosted CI

[Successful run 43470554631](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631),
exact SHA `5e31b44b329095eaf3268eaef4499dbcf371598b`:

| Job | Result | Observed tests |
| --- | --- | --- |
| [Windows/Python 3.11](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631/job/132040993865) | PASS | Ruff; 574 Python in 199.93 s |
| [Ubuntu/Python 3.11](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631/job/132040993809) | PASS | Ruff; 574 Python in 44.76 s |
| [Ubuntu frontend/browser/wheel](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631/job/132040993195) | PASS | type/lint/build; 88 unit; 54 native browser; licensed wheel/browser/failure copies |

See [the CI report](GITHUB_CI_REPORT.md) for exact job durations and coverage limits. No hosted
failure required a code fix; meaningful steps were inspected, not inferred from workflow syntax.

## Anonymous public judge and handoff

The HTTPS clone excluded global/system Git configuration and disabled credentials/auth headers.
It was created outside the original checkout with no inherited venv, node_modules or assets.
It independently installed the lock, built the console, launched the unchanged PowerShell entry
point and passed real INC-001/CASE-INC/offline-tool checks. Only the test client reused an existing
Chromium binary cache; server dependencies/assets were fresh. LICENSE, NOTICE, README, MANIFEST
and judge .rl each returned anonymous HTTP 200 with matching committed bytes. The clone and bundle
remained clean/unchanged. This check exposed a README manifest link case error; the documentation
follow-up corrects it and checks relative Markdown links against exact Git path case.

Actual release commit: `5e31b44` — release: add Apache-2.0 and prepare public judge repository.
This report follows in a normal documentation commit; final owner response identifies its pushed
SHA and repeated CI result. Baseline remains an ancestor and no old commit was rewritten.

Remaining limitations/actions: one first-load initialization flake; reliable live browser L3 NOT
VERIFIED, historical source-service qwen3 L3 is not a guarantee; no new model call; no macOS/other
Python/production incident validation. Owner must review eligibility/rights, upload the separate
115-second English-narrated video, provide the actual publicly viewable URL, review AI disclosures
and personally submit Devpost. [Contest main page](https://relate.devpost.com/) and
[rules](https://relate.devpost.com/rules) retain inconsistent new-project wording; commit dates
alone do not settle eligibility. See [the handoff](SUBMISSION_HANDOFF.md).

**No Devpost submission, video upload, GitHub Release asset upload, model download, global service
change, store reset, force push or history rewrite was performed.**
