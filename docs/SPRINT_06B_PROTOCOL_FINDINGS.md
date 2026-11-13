# Sprint 06B protocol findings

## Observed availability and limits of the evidence

Initial main was 8702efa4061525f3f8e37faa6aa90aedb5187b5c, clean. Reproduced baseline:
518 Python / 80 frontend / 35 agent evaluation cases passed. Historical safe records establish
one native tool followed by AGENT_FINISH_SCHEMA in Sprint 06; they contain no field-level error
metadata or raw transcript. They cannot establish which field/JSON shape failed.

One initial fixed GET to `http://127.0.0.1:11434/api/version` on 2026-11-13 at
12:41:24.708116 UTC timed out after 2016.04ms. No Ollama process or listening local 11434 socket
was observed by the read-only Windows checks. No second probe, tags/show request, inference,
daemon start/restart/configuration change, model pull or installation followed. Current version,
installed model and capabilities are UNKNOWN. Historical 0.40.16/qwen3 tags are not current
availability evidence. B6 is BLOCKED_DEPENDENCY / L0; no live recovery trial was attempted.

If an existing installation is available, the owner may open the Ollama application or manually
run its already-installed `ollama serve` command in their own terminal. This session did neither
and does not assert an installed CLI exists. After the owner restores reachability, run a fresh
bounded probe; only then authorize/run one observed trial and at most two issue-driven follow-ups.

## Protocol facts and discriminated hypotheses

The official [chat endpoint](https://docs.ollama.com/api/chat) documents native message history,
tools, format and thinking controls. [Tool calling](https://docs.ollama.com/capabilities/tool-calling)
shows assistant native tool_calls followed by a tool role/tool_name result.
[Structured outputs](https://docs.ollama.com/capabilities/structured-outputs) recommends a
Pydantic-generated format schema, validating message.content, and grounding the schema in the
prompt. These documents do not prove how an unreachable particular daemon/model behaved.

| Hypothesis | Evidence | Conclusion |
| --- | --- | --- |
| tools and format sent together | Baseline AgentProvider.chat already excludes tools for final=True and sends no format during tool selection; current controlled requests verify both phases | Not found in baseline builder; not an established cause |
| Wrong envelope parsed | Baseline and current agent read actual message.content after strict envelope validation | Not found in inspected code |
| Native assistant/result history missing | Baseline records the admitted first native call and immediately paired role=tool/tool_name result; controlled next request verifies actual native-derived result | Documented minimal history form retained; no speculative history rewrite |
| Thinking text treated as fact | Existing firewall ignores thinking; new hostile controlled envelope confirms no echo, rendered claim or diagnostic leakage | No observed evidence of this cause |
| Empty/malformed JSON, wrong root, null, missing/extra/wrong fields, duplicate/excessive IDs | Each can be structurally distinguished by new controlled tests and safe diagnostics | Plausible prior shapes, none identified as the historical live root cause |
| Truncation/stop reason/token limit | Existing envelope rejects non-stop completion; diagnostic captures allowlisted stop reason and bounded counts | No historical token/stop data; no timeout/token-budget increase justified |
| Known but unsupported/unknown valid-format ID | Existing semantic checks reject with distinct UNKNOWN_CLAIM_ID / CLAIM_NOT_RETRIEVED | Different gate from structural schema rejection; format-pattern errors can still be schema failures |
| Provider refuses connection | Independently measured timeout at initial connect stage | Current dependency blocker, not schema failure |

**Historical AGENT_FINISH_SCHEMA root cause: UNRESOLVED / NOT REPRODUCED LIVE.** No raw model
output was recovered, logged or invented. No claim is made that schema-in-prompt grounding fixes
that historical failure. The safe new observability makes a future bounded trial discriminating.

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
