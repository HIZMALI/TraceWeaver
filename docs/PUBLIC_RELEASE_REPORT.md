# TraceWeaver public release report

Status: PREPUBLICATION. Authorized target HIZMALI/TraceWeaver, PUBLIC/main, Apache-2.0.
The target did not exist when checked with the authenticated HIZMALI account. No creation/push
has occurred. All P0–P6 gates must pass first; see PUBLIC_RELEASE_AUDIT.md.

Baseline: clean main `f99deb60d3a909298c9e2646693e951225b23c09`; 41 reachable commits / 701 local
objects inspected. User store 21/27 and judge store 51/67 match protected bytes; manifest unchanged.
Local regression: 574 Python, 88 frontend and unchanged full rerun 54 Chromium PASS; frozen suites
35/20/19 PASS. Initial browser 53/1 failure is retained and explained in PUBLIC_RELEASE_AUDIT.md.
Ruff/pip check/typecheck/lint/build/actionlint and point-in-time npm/pip vulnerability audits passed.
Fresh source and non-editable outside-checkout licensed wheel checks passed, including Node-free
runtime, real native browser flow and missing/corrupt/locked-copy generic failures. Launcher passed.
All existing tests, gold, reports, screenshots, historical media and both graph stores are unchanged.
Hosted CI and anonymous public clone are NOT RUN. No Devpost submission or video upload occurred.
Final observed repository URL, pushed commit, workflow/job links and remaining limitations will be
recorded after those actions actually happen; target authorization is not evidence of publication.
