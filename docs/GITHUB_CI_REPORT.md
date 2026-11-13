# GitHub CI verification

Observed November 13, 2026: **PASS** for implementation commit
`5e31b44b329095eaf3268eaef4499dbcf371598b` on PUBLIC/main. These are actual hosted runner results.
[Successful run 43470554631](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631).

| Actual job | Python / OS | Result | Job duration | Observed checks |
| --- | --- | --- | --- | --- |
| [quality, Windows](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631/job/132040993865) | 3.11 / windows-latest | PASS | 237 s | Ruff; **574 passed in 199.93 s**, no skips/failures |
| [quality, Ubuntu](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631/job/132040993809) | 3.11 / ubuntu-latest | PASS | 73 s | Ruff; **574 passed in 44.76 s**, no skips/failures |
| [packaged-console](https://github.com/HIZMALI/TraceWeaver/actions/runs/43470554631/job/132040993195) | 3.11 / Ubuntu; Node 24 | PASS | 156 s | typecheck/lint; **88 frontend**; build; **54 native Chromium in 53.9 s**; licensed wheel; independent server/browser |

Run SHA matched local HEAD and remote main. Every expected job and meaningful step concluded
success. No continue-on-error, platform removal, skipped assertion, gold change or live-model
substitution was used. Actions are SHA-pinned; workflow permissions are contents: read.

The wheel ran outside the checkout, non-editably, against the real 51/67 synthetic Relate store.
It observed 14 INC-001 edges, CASE-INC's one conflict/two undetermined pairs, four offline tools /
23 native queries / eight claims / eleven citations; zero page errors/foreign requests. Missing,
corrupt and locked independent copies each returned generic 503 without fallback. Bundle bytes
remained unchanged. Node was excluded from the server PATH. No model ran. Ubuntu wheel SHA:
`bc1e1b6d76586f5d3768f1cd5897edc2439b3aec96ddee4e2c2e7845c9b03752`.
It need not match the Windows build: build metadata differs.

The table records the completed implementation run before this report's documentation commit.
That follow-up corrects manifest link case and records results without altering application code,
tests or workflow. Its push triggers the same full workflow. Compare [main's subsequent runs](https://github.com/HIZMALI/TraceWeaver/actions?query=branch%3Amain)
with [main's commit history](https://github.com/HIZMALI/TraceWeaver/commits/main); the final owner
response records the subsequent pushed HEAD and observed CI. The report does not claim a future
commit/run result. A report cannot contain its own Git hash without changing that hash.

Coverage: native Python on both hosted platforms; frontend/installed-wheel browser on Ubuntu;
local PowerShell launcher and anonymous source clone on Windows/Python 3.14. macOS, other Python
versions, installed Windows/Python 3.11 browser wheel, production accuracy, current live browser
L3, source truth and contest eligibility are not established by these jobs.
