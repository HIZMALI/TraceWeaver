# Public release audit

Owner authorization: Apache-2.0, HIZMALI/TraceWeaver, PUBLIC, existing main/full history, only after
P0–P6 pass. Initial HEAD `f99deb60d3a909298c9e2646693e951225b23c09`; clean worktree, no remote.
No history rewriting, final video publication or Devpost submission is authorized by this audit.

## Enumerated scope and reviewed findings

P0/P1: PASS. Gitleaks 8.30.1 from its official release, verified against its published SHA-256
manifest, scanned current tracked files and all local-ref history with redaction, five decoding
levels and three archive levels. An independent complete object inventory scanned **701 objects**:
410 blobs, 41 commits, 250 trees; all 451 content objects / 11,174,214 bytes, including four
unreachable blobs, were read. Every reachable commit tree/path was enumerated. An additional
Gitleaks pass consumed every content object in memory. No raw secrets or matching lines are
included in this report. Detailed inventories stay ignored and must never be published.

Gitleaks returned zero findings in each scope. Two supplemental private-host/IP pattern matches
were individually reviewed: both are explicit **X19 forbidden_output_fragments** assertions in
the frozen explanation gold, not real service settings or private incident data. They are retained
unchanged. No unresolved high-risk finding remains at this checkpoint. This is a bounded automated
scan plus source/visual review, not a guarantee of secret absence or a legal certification.

All commit identities use the authenticated owner's GitHub noreply identity. Commit author dates
span November 12–13, 2026; these dates are provenance, not an organizer eligibility ruling. All local
refs were included, not just main. Normal main-only push will preserve history and exclude unrelated
Codex checkpoint refs/dangling objects.

## Binary, data and rights review

The 28 binary content objects comprise 26 historical image versions, one previously versioned
7.28-second **silent synthetic technical sample**, and the one exact synthetic judge store.
Image PNG metadata contains no text/EXIF chunks; all 26 versions were visually inspected through
three contact sheets. They show project-authored synthetic UI, not customer incidents or third-party
stock footage. The deliberately documented old technical sample remains as historical evidence;
it is not the final 115-second video, narration, private raw production take or submission upload.
No new recording is added. The largest historical blob is 2,934,834 bytes, below GitHub file limits.

The only historical `.rl` is `examples/judge-demo/traceweaver-demo.rl`, exactly SHA-256
`29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239`, with 51/67 native counts,
the unchanged manifest and explicit demo flags. User data remains ignored. No credentials, model
weights, dependency executables, private production logs, virtual environments or node_modules
were found in publishable history. Final narrated videos and TTS assets remain outside Git.

The owner selected Apache-2.0. Canonical LICENSE is copied unchanged from the Apache Software
Foundation; NOTICE attributes eligible original work to HIZMALI, with substantial Codex assistance.
Third-party notices remain intact. Python runtime dependencies are separately installed; frontend
production notices remain bundled. Development-only MPL/BlueOak tools and optional/local media
tools do not receive a new Apache grant. No proprietary font or encoder binary is redistributed.
See DEPENDENCY_LICENSES.md for actual installed package review and media/model boundaries.

## Gate ledger before publication

| Gate | Status | Evidence |
| --- | --- | --- |
| P0 | PASS | Clean main, fsck, verified HIZMALI CLI/connector, target absent, native/hash baseline |
| P1 | PASS | All-ref/all-object/current scans and classified binary/rights review; zero unresolved high risk |
| P2 | PASS | Canonical LICENSE/NOTICE/SPDX; built wheel contains exact license/notice bytes |
| P3 | PASS | Tested judge entry points; synthetic/offline/historical live distinction; AI/media disclosure |
| P4 | PASS | 574 Python, 88 frontend, 54 browser; frozen 35/20/19; independent source/wheel/launcher |
| P5 | PASS | SHA-pinned least-privilege Windows/Ubuntu/Py3.11 workflow; actionlint passed |
| P6 | PASS | Reviewed staged inventory, protected-byte comparison, final redacted scans and clean commit gate |
| P7–P11 | NOT RUN | No repository creation or public push before all preceding gates pass |

## Actual local validation and limits

Ruff, pip check, frontend typecheck/lint/build and actionlint passed. All 574 Python tests passed
without skips, as did 88 frontend tests. The initial browser invocation returned **53 PASS / 1 FAIL**:
React Flow nodes remained unmeasured/hidden and its first edge was absent for seven seconds. This
overlapped an independent browser installation check. The retained trace does not establish the
underlying timing cause. After that process ended, the entire unchanged zero-retry browser suite
passed **54/54 in 45.5 seconds**. No assertion, timeout, fixture, application code or gold was changed
to obtain that result. This observed initialization flake remains disclosed, not erased.

Frozen agent/graph/explanation suites returned 35/35, 20/20 and 19/19. Deliberately corrupted agent
gold returned exit 15 and one detected failure; original gold remained unchanged. npm audit and
pip-audit against the development lock returned zero known vulnerabilities at execution time.
These are point-in-time database checks, not a claim that dependencies are vulnerability-free.

A new licensed wheel was installed non-editably in a fresh environment outside the checkout;
the source setup was independently rebuilt too. Both actual Chromium flows returned 14 native
INC-001 edges and offline 4 tools / 23 queries / 8 claims / 11 citations, no external requests or
page errors. The wheel server's PATH excluded Node. Missing/corrupt/locked owned bundle copies
returned generic 503 without fallback. The unchanged PowerShell launcher independently served
the 51/67 native store on loopback, and the read-only judge checker passed.

All 263 baseline tracked files were compared by bytes: only nine explicitly reviewed release
documentation/metadata/build/workflow files changed; the other 254, including every old source
test, gold, screenshot, report and tracked clip, remain identical. Both user/judge database hashes
and native counts remain unchanged. Runtime application code and API contracts were not edited.

Review sign-off: Codex completed the enumerated automated and targeted source/visual audit under
the owner's stated conditions. The exact resulting commit, clean worktree, scans and authenticated
target identity are rechecked locally before creation/push. Detailed evidence stays ignored.
Security or rights findings reopen the hard gate. Hosted CI is a separate post-push gate.
