# Sprint 07 — Judge-ready release candidate

**Offline local release candidate: PASS. Optional current browser L3: BLOCKED, no model action.**
Platform portability remains PARTIAL: Python 3.11 and Ubuntu runtime NOT RUN; hosted CI UNVERIFIED.
The genuine 115-second offline presentation is produced and reviewed. Publication, license choice,
video upload and Devpost submission are OWNER-PENDING. These separate statuses are not conflated.

Work stayed on existing `main`, starting at `96bedcc4b5032ec1853f6866a56c3f11241436ee`, initially clean.
The complete mission, project rules, previous reports/guides, manifest, package scripts, workflows
and existing tests were inspected. No old expectations, gold, API routes, CLI contracts, provider
budgets or citation admission rules were changed. No branch, remote, model, service or system runtime
was created, downloaded, restarted or configured. No push, public hosting or submission occurred.

## Acceptance gates

| Gate | Status | Actual result |
| --- | --- | --- |
| R0 baseline | PASS | 567 Python, 86 frontend, 50 native browser; evaluations 35/20/19, all green; original hash inventory |
| R1 first run | PASS | Fresh source venv/pip/npm/build and browser; fresh non-editable external wheel, copied bundle, Node-free server, native browser; generic missing/corrupt/locked-copy 503; no fallback |
| R2 portability/CI | PARTIAL | Native wheel metadata and current locks audited; offline frontend/package CI added; local actionlint passes. No installed Py3.11/Ubuntu; runtime NOT RUN, remote CI UNVERIFIED |
| R3 optional current L3 | BLOCKED | One fresh version GET timed out at 2006.851ms. No tags request, eligibility assumption, inference, retry or new live screenshot |
| R4 onboarding/accessibility | PASS | Visible Explore the verified path, explicit stored-path/truth distinction, native selected path; readable graph labels, full edges retained; desktop/tablet/phone/reflow/keyboard/reduced-motion/axe pass |
| R5 full video | PASS | Actual 115.000s 1080p H.264 MP4 and 115s VP9 WebM; silent English captions; 10 timestamps reviewed and complete MP4 decoded |
| R6 artifact/public readiness | PASS locally | 25 safe exported payloads, checksums, compatible offline runtime wheels, intact judge bundle; real launcher installation/check and tamper rejection; quick-start/disclosures/license decision note |
| R7 closure | PASS locally | 574 Python / 88 frontend / 54 native browser, frozen 35/20/19, bad-gold negative control, quality checks, final independent installation, protected hash/count audit |
| R8 versioned handoff | PASS locally | Scoped tested local commits, this report, progress ledger, video report, English submission draft and owner checklist. Public actions remain pending |

## What changed and why

The first screen now says what the console does and provides **Explore the verified path**. It
selects the existing dependency candidate and existing native path focus/inspector. It does not
introduce another analyzer or claim a causal verdict. “Verified” explicitly means an exact stored
path, not authenticated truth. Both competing pairs and all 14 INC-001 returned arrows remain.

New responsive selection/axe checks exposed opacity fading that made unselected graph text fail
contrast on tablet. Removing node/edge opacity fading preserves readable context; existing selected
outlines and highlighted path strokes still show focus. No source graph data or counts are hidden.
Changed interactions passed at 1440×900, 1024×768, 390×844 and 720×900 CSS width reflow (the 200%
width equivalent for a 1440px layout). Browser zoom itself was not modified. The existing keyboard
path list, focus, reduced-motion behavior and domain assertions remain intact.

The browser runner now uses an owned current-source copy because historical tests write screenshots
relative to both cwd and source paths. All original assertions execute against the real engine;
dependency junctions are only used for regression execution. This is distinct from clean-install
verification, which copies no environment, node_modules or ignored build assets. Historical capture
bytes remain untouched. New genuine captures are under `docs/screenshots/sprint07/`.

New release tools verify a genuinely external installation, record native browser actions, encode
using an already installed local FFmpeg, and stage an allowlisted offline distribution. Existing
runtime API/agent/firewall code and the legacy fixture were not edited. The CI addition exercises
frontend type/lint/unit/build and an independently installed offline package browser on Ubuntu
Python 3.11; existing Windows/Ubuntu Python quality jobs remain. Hosted execution is unverified.

## Actual tests and evaluations

| Family | Preserved | Added | Final passed |
| --- | --- | --- | --- |
| Python | 567 | 7 | **574** |
| Frontend | 86 | 2 | **88** |
| Real native Playwright | 50 | 4 | **54** |

Final Python closure: `574 passed in 99.37s (0:01:39)`. The prior final implementation run also
passed 574 in 85.08s. Frontend: seven test files / 88 tests. Native browser: `54 passed (1.3m)`.
Concurrent capture/build work means these are not controlled performance benchmarks.
Ruff, pip check, TypeScript, ESLint, build, local actionlint **1.7.12**, Node syntax checks and
`git diff --check` passed. Vite still reports existing nonfatal `use client` dependency directives;
there was no build failure and these warnings are disclosed, not hidden.

Frozen fresh-output evaluation results: **35/35 agent**, **20/20 graph**, **19/19 explanation**.
Agent cases remain 18 native / 17 controlled protocol; live-model accuracy is null. Successful native
edge agreement is 57/57 and citation support 90/90 in that explicitly bounded scope, not production
or model accuracy. A separately corrupted gold copy returned the expected **exit 15,
GOLD_NATIVE_EDGE, one failed case**. Original gold was unchanged; this is a passing negative control,
not a failed regression suppressed from totals. The graph-versus-flat 13-valid-question erratum and
earlier evaluation outputs remain unchanged.

New tests cover real documented parameterized Cypher, refusing artifact overwrite, ordered measured
caption cues and caption injection rejection, truthful empty-scope onboarding, plus actual native
responsive path selection/edge direction/keyboard/axe behavior. The full capture action flow,
checksum tamper control and independent install are additional executed verification commands.

Logs and fresh outputs remain ignored under `.verification/sprint07/`: `closure-pytest.txt`,
`final-{unit,browser,type,lint,build,actionlint,pip-check}.txt`, `final-{agent,graph,explanation}.json`,
`bad-gold-control.json`, `install-final/result.json`, `privacy-screen.json`, `integrity-final.json`.
The safe versioned summary is [release evidence](../reports/sprint07_release_evidence.json).

## Clean installation and artifact

Final wheel: `traceweaver-0.1.0-py3-none-any.whl`, **305,534 bytes**,
SHA-256 `77ba04b14d7044806e8b22eba28daf3c1afdee71980e95d64c6b664521bc0bd5`.
It contains exactly one current JS/CSS generation and frontend notices, no `.rl`.

`scripts/verify_release.py --source-check` installed a new source environment and npm dependencies,
built from clean source, checked the bundle and exercised its genuine browser. A separate fresh
non-editable wheel environment outside the checkout served numeric loopback with **Node absent
from server PATH**. Imports came from that environment, and fetched assets matched wheel bytes.
Its source and wheel browsers both exercised INC-001/CASE-INC, real stored reverse TARGETS,
typed citation/evidence inspection, one conflict/two undetermined pairs, gaps, rehearsal and refresh.
Initial POSTs: zero; foreign requests: zero; page errors: zero. Refresh cleared execution state.
Copied bundle bytes were unchanged. Actual missing/corrupt/locked-copy API checks returned generic
503 `Graph database unavailable`, with no fabricated fallback graph or private paths.

Local export: `.verification/sprint07/release-candidate/`, **25 payloads / 13,922,257 bytes**, plus
its manifest. `SHA256.json` SHA-256:
`af4ba99733a7b6bc0ce0d320b81815a4e2b37dfcd5db73632c44d2c4511ac135`.
It contains runtime wheels, the intact synthetic judge bundle, constraints, notices, launcher and
guides. `RUN_JUDGE.ps1 -CheckOnly` really installed from included wheels using `--no-index` and
passed native verification. A tampered independent copy was rejected before creating an environment.
The generated test environment was moved out of the export; no cache/env/video/FFmpeg/user store is
part of its manifest. It is a **local Windows x64/Python 3.14** export, not a universal platform bundle.

Start the source checkout with `scripts/start-judge-demo.ps1` (assets are already built), or run
`RUN_JUDGE.ps1 -Port 8000` in the exported folder after reviewing its prerequisites. Then open
`http://127.0.0.1:8000/?incident=INC-001`. See [judge quick start](JUDGE_QUICK_START.md) for full
first-install commands, actual parameterized Cypher and the real persistent single-file engine.

## Video and current model status

Final MP4: `.verification/sprint07/video-final/traceweaver-judge-115s-1080p.mp4`,
**115.000s / 1920×1080 / H.264 / 25 fps / 5,290,900 bytes / no audio**.
SHA-256 `f8b4b322024f2c023a2410a9b18ac27180c9934014883317d0a6a9e66d1723b4`.
Final 115-second VP9 WebM SHA-256:
`39b14e707c33454dbbb30a59ebf75c6b470af90d90de6c90d132c60659156ad5`.
Raw 122.720-second source and the earlier complete framing draft were preserved. Only the first
115 seconds are selected; no action is retimed. The actual recorded wheel's console assets are
byte-identical to the final wheel's assets. Measured successful scene cues anchor labeled explanatory
captions; no app data overlay or model success is fabricated.

Frames at 2/18/31/43/56/69/80/93/103/112s show the full truthful progression. The complete final MP4
decoded without errors. Real rehearsal: four tools, **23 native queries / 8 admitted claims /
11 citations**, zero model interactions, both AI flags false. This is not an AI-directed result.
See [capture report](VIDEO_CAPTURE_REPORT.md), [exact script](SPRINT07_VIDEO_SCRIPT.md) and the small
real-frame [thumbnail](screenshots/sprint07/video-thumbnail.jpg). Videos are ignored and not committed.

At **2026-11-13T14:08:34.637148Z**, one fixed-loopback `/api/version` request timed out after
**2006.851ms**. `/api/tags` and capabilities were not requested by the live track. Current installed
model eligibility is unknown. **Zero live model actions, zero executed live tools, no admitted live
claims/citations** this sprint. No retry, timeout increase, download or service change occurred.
There is no new L3 screenshot or supplemental segment. The previous source-service qwen3:8b L3
remains historical genuine evidence; it is not a current installed-browser success. Historical
AGENT_FINISH_SCHEMA field-level cause remains UNRESOLVED. No provider raw prompt/response was saved.

## Integrity and platform limits

Before and after hashes/counts are identical:

| Store | Bytes | Native nodes / relationships | SHA-256 (both before and after) |
| --- | --- | --- | --- |
| User `data/traceweaver.rl` | 73,728 | 21 / 27 | `3bdf4ffa20ec647120780ad769832f04b51d418c33ed78d83751d0586220fbf3` |
| Judge `examples/judge-demo/traceweaver-demo.rl` | 110,592 | 51 / 67 | `29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239` |

Unchanged manifest: `50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab`.
Unchanged logical judge graph: `1cc7f23c5bc9926d9aec9b5f6a91c32022a8a6e268d52bc6120b9d4411c6743d`.
Frozen graph/explanation/agent gold hashes:

```text
6749145aa8e28937bc74aa8d3b53ec00fe0651d29b0cadc39ce6fd5547f4cef8
e716b63860712d9aaef23ac2b8a61b2bb77c225ce0359d8a36749cd65d2224cb
dce5da3e7561029a8877fb03a9de86961509f728694b6c22e01155e82dfa6295
```

Of 241 original tracked files, only five intentionally changed: CI, README, browser runner,
ProofFocus and GraphCanvas. The other 236 match baseline, including **15 historical screenshot
inventory files**, the old WebM, all earlier tests, reports/evaluations, fixtures, manifest and gold.
Old WebM SHA-256 remains `73c93ea0ce85ef955f8742a781b871e6863a8cb036dd53825fff4ff928b5e1a9`.

Actually exercised: Windows 11 build 26200, Python **3.14.0**, Relate **1.0.0**, Node **24.13.1**,
npm **11.8.0**, Chromium **158.0.8127.18**. No Python 3.11 executable/launcher or installed Ubuntu
distribution was found; WSL listed only docker-desktop, which was not started or used. No runtime
was installed. Official [Relate 1.0.0 package metadata](https://pypi.org/project/relate-db/1.0.0/#files)
lists cp39-abi3 wheels for Windows x64, manylinux x64/aarch64 and macOS x64/arm64. This availability
does not establish runtime compatibility. Existing declared Python >=3.11 and locks were preserved.

## Privacy, licensing and owner actions

Limited pattern screening covered 260 tracked/new nonignored paths at the audit snapshot and all
staged/wheel text. No personal Windows path, credential-pattern or unexpected executable/model
artifact finding was returned in that scope. Native dependency wheel libraries are expected.
The final closure screen extended this to 263 paths, again with no pattern findings; exported
artifact/video hashes and all original native counts/bytes were rechecked at the same closure.
Screening cannot guarantee absence of secrets. Ignored installation logs/scratch trees were not
exported. The only staged `.rl` is the exact synthetic judge exception; no user store was exported.

The [new readiness note](SPRINT07_PUBLIC_READINESS.md) records current official rules/deadline,
remaining dates ambiguity, dependency notices and an owner licensing decision. No project license
grant was chosen. The [English Devpost draft](SPRINT07_DEVPOST_DRAFT.md) distinguishes implemented,
experimental, unverified and planned scope, and discloses substantial Codex assistance and runtime
offline/non-AI behavior. No universal retrieval superiority or live-model accuracy is asserted.

Owner actions: choose project license after dependency review; authorize/create/publicize the GitHub
repository and required topic; observe hosted CI; review/upload the actual video and confirm access;
review genuine screenshots, eligibility/start/reuse/rights and the draft; submit Devpost personally.
Loopback is not a public demo URL. See the readiness note's official-source links for event facts.

## Local commits and handoff

| Commit | Tested milestone |
| --- | --- |
| `8182bbe` | Independent baseline, protection inventory and media audit |
| `6d0db4b` | Clean source/wheel/native browser verifier, screenshot-safe regression runner, offline CI preparation |
| `7d5a175` | Clear proof onboarding, contrast repair, native responsive/keyboard/axe captures |
| `8410090` | Genuine 115-second capture automation, measured captions, reviewed video report and native query/tooling tests |
| `125a011` | Offline distribution exporter/launcher, actual install/tamper control and owner documentation |

The final report/evidence/ledger closure is a separate local documentation commit, identifiable with
`git log -1 -- docs/SPRINT_07_RELEASE_REPORT.md`. Final status and that observed hash are returned to
the owner after commit. The observed wall-clock evidence window on November 13 was
13:54:53.523Z–14:37:53.055Z: **2579.5 seconds (about 43 minutes)** from baseline inventory to final
closure audit, excluding earlier mission reading. Work, testing, recording and reporting completed
in this active session, without idle padding or future-run claims.
No application regression remains failing locally. Outstanding technical limits are provider
availability/schema history, unexecuted platforms/hosted CI, existing build warnings and the
deliberately synthetic/partial/no-cause evidence contract. The source, video and local export are
ready for owner review; public release remains an owner action.
