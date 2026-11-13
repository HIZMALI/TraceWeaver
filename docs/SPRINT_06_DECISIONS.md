# Sprint 06 implementation decisions

Starting main: a8f4ac502c8bb4eaefce8d6e448a273aa133a73e, clean worktree. G0 executed before
application edits: 420 pytest passed in 48.48s, 58 frontend tests and 36 actual Chromium cases
passed (29.9s). Ruff, pip, TypeScript, lint and build pass. Existing native stores and supplied
manifest/gold hashes match; the complete tracked inventory is in ignored .verification/sprint06.

1. Preserve legacy DTOs, explanation/catalog/firewall and existing tests. Introduce new agent
   1.0 DTO/service/tools/provider modules, two explicit POST actions and a separate CLI module.
   Share the existing exact-origin/body parser and one-action lock with local claim selection.
2. Each tool validates a snapshot-grounded opaque subject handle, opens a fresh read-only native
   worker connection, performs its own allowlisted parameterized Cypher and audits actual directed
   edges. Tools do not merely read a cached dashboard. Close every reader before provider HTTP.
3. Bind source Investigation/options fingerprint and bounded local file SHA-256 at start and before/
   after tools and final admission. A changed source aborts; no mixed-context claim rendering.
   Digest caps fail closed, not a promise to bound whole-engine RAM or native query execution time.
4. Model sees opaque subject/node handles, fixed tool names, enums/counts/UTC and admissible opaque
   claim IDs. No raw IDs/prose/refs/private paths/original hostile timestamps enter model messages.
   Use native Ollama chat tools, not JSON action output falsely called native tool calling.
5. At most four actual tool calls, five model interactions, one tool per round, no retries. Bound
   per-request/total provider time and bytes; validate final IDs with the existing semantic firewall
   and require factual graph/time/provenance support retrieved by actual tools. No source/model prose.
6. Offline rehearsal calls the same real tools with a finite declared plan and never calls Ollama.
   Timings are real but explicitly excluded from canonical repeatability. No current clock becomes
   incident/evidence time. Model-selection-only and invalid/no-tool responses are separate failures.
7. First-screen UX emphasizes a native-derived proof summary, readable candidate viewport and
   selected/hover edge labels; counts/edges and full accessible paths remain. Agent UI is distinct
   from existing claim selection. Only explicit actions can rehearse or infer.
8. Keep original screenshots/reports/evaluation/G8 source bytes immutable. Run existing browser
   cases in owned source mirrors so their unchanged screenshot helper cannot overwrite history.
   New captures use docs/screenshots/sprint06. Freeze new independent evaluation before execution.
9. Rebuild a fresh-source wheel and verify an external non-editable, Node-free server. No license,
   public host, remote/push, model/system install or Devpost submission. A genuine video is optional;
   label storyboard/recording honestly. Public repository/video/license remain owner actions.
10. Product/technical docs are English; owner-facing result and report summary are Turkish per
    explicit task request. The report distinguishes blocked live-model/platform tracks from code
    and controlled-protocol evidence. Never claim a future unattended session.

Official native protocol references read before agent coding:
[Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling),
[native chat API](https://docs.ollama.com/api/chat). Tool results use role=tool/tool_name;
assistant tool_calls are validated before any execution. Provider availability/version is checked
locally; at G0 127.0.0.1:11434 refused the connection. No model availability is assumed.
