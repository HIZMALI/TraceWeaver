# Sprint 06 checkpoint ledger

Starting main a8f4ac502c8bb4eaefce8d6e448a273aa133a73e. Original worktree clean.

| Gate | Status | Evidence / next step |
| --- | --- | --- |
| G0 | PASS | 420 pytest / 58 frontend / 36 native Chromium baseline; protected hashes match |
| G1 | PASS | Actual native first-screen proof, larger type/core viewport; 62 unit / 36 real browser cases |
| G2 | PASS | Strict agent 1.0 models + five actual parameterized native tools; 452 pytest passed |
| G3 | IN PROGRESS | Bounded native Ollama tool orchestration; live installation unavailable |
| G4 | PENDING | Same-tool deterministic offline rehearsal and CLI |
| G5 | PENDING | Explicit local agent panel and step-to-proof selection |
| G6 | PENDING | Readable real screenshots and new judge story |
| G7 | PENDING | Independent frozen scenario gold, native/protocol runner and corruption control |
| G8 | PENDING | Preserve historical study and rigorous limitations note |
| G9 | PENDING | Expanded tests/security/performance/independent package |
| G10 | PENDING | Release/fact check/draft/video plan and actual optional recording |
| G11 | PENDING | Final protected audit, full gates, local commits and report |

Baseline evidence: .verification/sprint06/baseline.json, baseline-pytest.txt and owned
baseline-browser/.verification/sprint06-browser.txt. Old screenshots were written only in the
mirror; originals remain byte-identical. All tests use native Relate, temporary write specimens.
No old expectation changed. Ollama refused connection at G0; checking existing installation only.

G1: typecheck/lint/build/Ruff pass, 62 frontend and 36 actual current-source Chromium tests pass
(32.2s). Native first-screen capture in ignored G1-first-screen.png visually inspected. Original
screenshots/fixtures/reports/stores remain identical. Test setup initially imported original static
assets in a source mirror; the positive new-heading capture caught it. New test runner now uses
current source with an owned cwd for unchanged historical screenshot writes. New summary buttons
initially failed axe label-content matching; fixed actual accessible text without excluding rules.
Ollama service, PATH/standard installation/registry/cache/binary searches found no executable/model;
live agent verification is BLOCKED unless an existing usable local installation becomes available.
Only Docker Desktop WSL is registered; no Ubuntu/Python 3.11 found, no system setup attempted.

G2: 452 full pytest passed in 47.20s; 32 added native/strict-contract cases pass, Ruff clean.
All five tools issue fresh native Cypher and recheck directed edge identities. Scope/digest guards,
orphan/unknown timestamps, structured conflicts, caps, private-metadata withholding and query
budgets verified on temporary native stores. Query counters include failed native work after
reader closure; final focused rerun passed. Tool contract documented. Original bytes unchanged.

Resume: read this ledger/decisions, inspect git status, preserve user changes. Complete G1 then
the strict native tool layer. No model pulls/installations or user-store writers. Browser mirrors
are owned copies with environment/dependency junctions; never recursively delete their targets.
