# Sprint 06 original video plan

The primary narrated recording should follow the 115-second judge guide. Capture the actual
numeric-loopback app at 1440×900 or a readable higher resolution. Start from the intact synthetic
judge store, disclose synthetic data and keep causal/source-truth limits visible. Do not use
AI-generated screenshots, sped-up fake tool progress, prerecorded model responses presented as
live, external source text or unlicensed audio. No recording is uploaded by this sprint.

| Segment | Frame/action | Voiceover cue |
| --- | --- | --- |
| 0–15s | Incident and native proof summary | Persistent Relate connects an incident to reviewable evidence. |
| 15–40s | DEP-001/DEP-002; selected path and reverse TARGETS proof | Candidates compete; actual direction matters. Connection is not cause. |
| 40–70s | Explicit offline rehearsal, ordered native steps and admitted citation | Same real native tools, fixed plan, no model. Statements pass a citation firewall. |
| 70–95s | CASE conflict, two unknown pairs, naive timestamp/source gaps | Structured disagreement stays distinct from unknown and unverified truth. |
| 95–115s | Current genuine capability state or separately verified local model trace | Show actual availability and rejected/accepted status. Finish NOT_ESTABLISHED. |

## Supplemental recording actually produced

`video/sprint06/native-walkthrough.webm`: **7.28 seconds**, silent VP9, 1440×900, 25 fps,
2,934,834 bytes. It records genuine automated interactions against the running native-backed app:
candidate/path, offline tool rehearsal, exact proof, admitted claim, CASE comparison and current
unavailable local capability. It contains no successful model run or fabricated narration.
This fast test clip is **not** the completed 1–2 minute judge presentation. Owner must record the
readable narrated story before submission. Companion `captions.json` describes observed actions
with approximate runner-clock offsets, including startup; it is not a synchronized subtitle track.

The recording was inspected using existing bundled Playwright FFmpeg: duration/codec/resolution
read, frames extracted at 2/4/7 seconds and visually reviewed alongside screenshot 06. Last frame
shows OLLAMA_CONNECTION_UNAVAILABLE, empty unselected model and disabled confirmed action.
SHA-256: `73c93ea0ce85ef955f8742a781b871e6863a8cb036dd53825fff4ff928b5e1a9`.
Recording command: `node scripts/record_sprint06.mjs`. It preserves an existing recording and
refuses overwrite; use a separately named owner recording. No music, voice track or third-party
media were added. Existing FFmpeg/Chromium were reused; no system tool/model was installed.
