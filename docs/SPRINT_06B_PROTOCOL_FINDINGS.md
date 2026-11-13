# Sprint 06B protocol findings

## Observed availability and limits of the evidence

Initial main was 8702efa4061525f3f8e37faa6aa90aedb5187b5c, clean. Reproduced baseline:
518 Python / 80 frontend / 35 agent evaluation cases passed. Historical safe records establish
one native tool followed by AGENT_FINISH_SCHEMA in Sprint 06; they contain no field-level error
metadata or raw transcript. They cannot establish which field/JSON shape failed.

The first fixed GET to `http://127.0.0.1:11434/api/version` on 2026-11-13 at
12:41:24.708116 UTC timed out after 2016.04ms. No Ollama process or listening local 11434 socket
was observed by the read-only Windows checks. No retry loop, service change, tags/show or inference
followed that initial failed audit. Current version/model/capabilities were initially UNKNOWN and
B6 was marked BLOCKED_DEPENDENCY / L0.

After B5, an explicit UI capabilities action used while preparing a truthful blocked-state capture
unexpectedly returned qwen3:8b and openweft-qwen3:8b. The capture assertion failed rather than
saving a false unavailable screenshot. On that concrete external-state change, B1 was reopened:
one additional bounded version request at 12:58:42.541533 UTC returned **0.40.16 in 4.364ms**.
There were two explicit version checks total, no version polling. Exact installed-model eligibility
was rechecked by the existing /api/tags guard for each permitted live action. No /api/show request
was necessary. No daemon, global environment, service, model or system installation was changed.

B6 then ran the initial explicit trial and one issue-driven follow-up. Trial 1 reached L2; trial 2
reached genuine L3 (details below). Earlier outage evidence is retained, not relabeled as schema
failure or erased. Availability remains an observed runtime condition, not a reliability promise.
If the existing service becomes unavailable again, stop the live track. The owner may open their
existing Ollama application or manually run their already-installed `ollama serve`; this session
never does so and does not assert an installed CLI exists on PATH.

## Protocol facts and discriminated hypotheses

The official [chat endpoint](https://docs.ollama.com/api/chat) documents native message history,
tools, format and thinking controls. [Tool calling](https://docs.ollama.com/capabilities/tool-calling)
shows assistant native tool_calls followed by a tool role/tool_name result.
[Structured outputs](https://docs.ollama.com/capabilities/structured-outputs) recommends a
Pydantic-generated format schema, validating message.content, and grounding the schema in the
prompt. These documents do not prove how the prior failed daemon/model interaction behaved.

| Hypothesis | Evidence | Conclusion |
| --- | --- | --- |
| tools and format sent together | Baseline AgentProvider.chat already excludes tools for final=True and sends no format during tool selection; current controlled requests verify both phases | Not found in baseline builder; not an established cause |
| Wrong envelope parsed | Baseline and current agent read actual message.content after strict envelope validation | Not found in inspected code |
| Native assistant/result history missing | Baseline records the admitted first native call and immediately paired role=tool/tool_name result; controlled next request verifies actual native-derived result | Documented minimal history form retained; no speculative history rewrite |
| Thinking text treated as fact | Existing firewall ignores thinking; new hostile controlled envelope confirms no echo, rendered claim or diagnostic leakage | No observed evidence of this cause |
| Empty/malformed JSON, wrong root, null, missing/extra/wrong fields, duplicate/excessive IDs | Each can be structurally distinguished by new controlled tests and safe diagnostics | Plausible prior shapes, none identified as the historical live root cause |
| Truncation/stop reason/token limit | Existing envelope rejects non-stop completion; diagnostic captures allowlisted stop reason and bounded counts | No historical token/stop data; no timeout/token-budget increase justified |
| Known but unsupported/unknown valid-format ID | Existing semantic checks reject with distinct UNKNOWN_CLAIM_ID / CLAIM_NOT_RETRIEVED | Different gate from structural schema rejection; format-pattern errors can still be schema failures |
| Provider unreachable | Independently measured initial timeout; later explicit capability/version evidence showed a transition | Separate intermittent dependency state, never schema failure |

**Historical AGENT_FINISH_SCHEMA root cause: UNRESOLVED / NOT REPRODUCED LIVE.** No raw model
output was recovered, logged or invented. No claim is made that schema-in-prompt grounding fixes
that historical failure. The new bounded live trials admitted valid structured finals; they do not reconstruct the old invalid field. No historical raw transcript is available.

## Independently reproduced defects and minimal corrections

1. **Offered-set mismatch:** on a fresh native caps fixture, the catalog has 128 entries and
   sanitized metadata offers only 64. Four actual native tools retrieve support for some entries
   outside those 64. The preserved baseline admit_finish function, compiled directly from its
   Git AST without modifying the module, accepted a valid supported but never-offered deployment
   claim. Current code rejects the identical proposal with CLAIM_NOT_OFFERED. This is an
   independently demonstrated admission-boundary defect, **not** the cause of the earlier
   structural rejection. One helper now constructs the exact retrieved-and-offered intersection
   for model packets and admission. Existing offline rehearsal still uses its full supported set.
2. **Malformed Unicode:** an unpaired surrogate could escape final admission as an unhandled
   encoding exception. It now returns the existing safe AGENT_FINISH_SCHEMA rejection, without
   rendering or persisting the malformed value. It is not attributed to historical Qwen behavior.
3. **Final instruction consistency:** both early completion and forced final-budget rounds now
   receive the same concise final packet: supported offered IDs, actual step numbers and the
   exact existing AgentFinalProposal JSON schema. Tools and format remain phase-separated. The
   schema validator is unchanged; no JSON repair, ID substitution or permissive extra fields.
   Explicit empty supported factual offers permit only honest abstention, not invented claims.

Parallel batch policy, model/round/native/byte/deadline budgets, fixed endpoint, provenance/time
semantics, shared API lock, old routes/DTOs and CitationValidator are unchanged. Final tool calls
cannot execute; the existing four-call/five-interaction budget rejection remains intact.

## Structural diagnostics contract

Internal opt-in only: `run_agent(database, action, diagnostics=StructuralDiagnostics())`.
No API request field, frontend surface or automatic file/logger output is added. Call export()
and write only to an owned ignored local artifact after bounded operation. Existing HTTP/CLI
report shapes remain unchanged. Normal calls leave diagnostics disabled.

Request records contain phase, tools/format kind, stream/think booleans, bounded role list and
actual offered count. Response records contain message/content presence, byte size, tool-call
count, allowlisted done_reason and bounded token counts. Final inspection distinguishes JSON
syntax/root, strict object/depth/duplicate parsing, Pydantic shape and semantic admission. Only
allowlisted field names and bounded error paths/types are exported; unknown names become OTHER.
No error messages, inputs, contexts, values, provider text, thinking or prompt are exported.
Source/database digests bind the snapshot; diagnostic probe clock is never incident time.

Limits: 40 records, 4096 bytes/record, 32768-byte export; dropped records counted. Export owns
a deep copy. Existing local-file/source and provider caps apply independently. Diagnostic JSON
inspection does not normalize or replace the separately strict admission parser.

Ignored evidence: `.verification/sprint06b/connectivity.json`, `diagnostics.json` (explicitly
CONTROLLED, not live), `offer-boundary-comparison.json`, baseline hashes and actual test logs.
The controlled null selected_claim_ids record exposes safe list_type/missing/extra-field paths;
it is not described as the previous live response. All raw provider/prompt/source text remains
absent from persistent artifacts and public results.

## Genuine bounded recovery observations

Trial 1 (actual qwen3:8b, daemon observed 0.40.16): trace_deployment, 10 native queries total,
3 chats, 8755.763ms; 3 non-caution / 4 total admitted claims and 5 citations. Final response was
280 UTF-8 bytes, JSON OBJECT, strict object parse accepted, zero unknown fields, selected_count=3,
Pydantic shape valid and semantic support ADMITTED. Both AI flags true. Level **L2**: only one
native tool, so this was not called multi-step success. Source remained partial, no cause/truth.

The measured L3 shortfall was early tool-phase stopping after one native tool. A small soft task
instruction now explicitly requests at least two different **model-chosen** available tools and
returns the actual distinct-executed count in opaque tool metadata. It does not select a tool,
force a native call, fabricate a trace, repair a final or reject otherwise valid single-tool
results as if they had two steps. A new controlled regression verifies precisely that distinction.
147 focused tests passed before the next real run.

Trial 2: actual model chose get_incident_scope, then separately trace_deployment; 13 native queries
(7 initial snapshot + 3 scope + 3 deployment), 4 chats, 15435.171ms. Initial valid parallel batch
was fully checked/constrained to its first call; the unexecuted proposal was not counted. The model
selected the second actual tool in the next native response. Final response: 314 bytes, JSON OBJECT,
strict parse accepted, four allowlisted fields, zero unknown fields, selected_count=4 and semantic
ADMITTED. Result: **L3**, 4 non-caution / 5 total claims / 6 citations, both AI flags true, no rejection.
Three stored directed edge tuples independently queried again; judge bytes unchanged. Warnings
PARALLEL_PROPOSALS_CONSTRAINED and READ_PHASE_TEXT_NOT_USED remain visible, not hidden.

The third and final bounded action was attempted through the independently installed wheel and
actual browser. It timed out before a native tool response: OLLAMA_TIMEOUT, 20023.387ms, one chat,
7 initial native queries, zero tool steps/claims/citations, both AI flags false. The existing public
status MODEL_OUTPUT_REJECTED is retained for compatibility; its specific transport code is not a
schema failure. No fourth trial was attempted. CLI L3 is not browser L3. The installed browser
offline four-tool rehearsal passed separately (8 claims/11 citations, no initial AI). Public safe evidence is `reports/sprint06b_live_agent_evidence.json`; complete
structural metadata remains ignored, with no provider prose, thinking or raw prompt persistence.

The genuine timeout screenshot also showed a previous deterministic rehearsal's selected tool
proof still visible beside the new zero-tool AI report. This is a view-state defect, not a native
query/model success. A focused UI correction clears transient tool/claim focus when a new agent
action begins and labels transport timeout separately from schema rejection. It was verified
with a clearly CONTROLLED provider timeout after actual native snapshot/HTTP/UI interaction; this
is not a fourth live Qwen action. Preserve the genuine pre-refinement screenshot as diagnostic
evidence, never label it successful live inference. Final validation/results are in the report.

Final verification: 567 Python, 86 frontend and 50 browser tests passed. The controlled timeout
case confirms stale native tool focus is cleared before the next action. Final installed-wheel
offline browser passes; it intentionally does not spend a fourth live trial. No source validator,
API report enum or provider deadline changed. Overall PARTIAL / best genuine L3, with the exact
historical schema cause unresolved and live installed-browser timeout disclosed.
