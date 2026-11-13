# 115-second genuine offline demonstration script

Run the installed-wheel capture automation against an intact synthetic bundle copy. The scene holds
below are deliberate reading time. Narration is supplied as synchronized **explanatory captions**;
the delivered video is silent, not an audio narration recording. The app is never given fake data.
Actual successful action offsets, not runner startup, determine subtitle cues in `capture.json`.

| Planned time | Executed screen action | English explanation / reading focus |
| --- | --- | --- |
| 0–12s | Open INC-001; check 14 returned edges and no-cause label | TraceWeaver connects incident evidence in an embedded Relate graph. Synthetic, read-only; connection is not cause. |
| 12–25s | Explore the verified path; focus actual candidate graph; scroll graph into view | Payment depends on Auth. DEP-001 TARGETS Auth, explicitly traversed in reverse; INCLUDES_CHANGE reaches CHG-001. |
| 25–37s | Select DEP-002; show its actual Payment target | Both deployment/target pairs remain investigation candidates. Neither is a proven cause. |
| 37–50s | Select admitted DEPLOYMENT_BEFORE_ONSET; scroll actual claim/citations into view | Exact GRAPH_PATH and 09:58 UTC time are support for a controlled template; not causal inference. |
| 50–62s | Evidence → EVD-001; actual inspector | TRACEABLE metadata and SYNTHETIC status do not authenticate source truth. |
| 62–75s | CASE-INC → Observations → actual conflicting pair | HEALTHY/FAILED conflict only in matching service/signal/environment/window. Two DEGRADED pairs stay UNDETERMINED. |
| 75–85s | Evidence → CASE-E-NAIVE | No explicit offset: UNKNOWN. No guessed onset or substituted ingestion time. |
| 85–99s | INC-001 → Explore investigation steps → Rehearse graph investigation | Run the real fixed offline plan now: four tools, 23 native queries, eight admitted claims, eleven citations; both AI flags false. |
| 99–107s | Select executed trace_deployment step 2 | Exact stored edges, reverse traversal and change path; deterministic, not AI-generated. |
| 107–115s | Gaps and next checks | Cause NOT_ESTABLISHED, external truth NOT_PERFORMED. Local, offline, reproducible. |

No local-model control is opened during this recording. There is no supplemental L3 segment because
the fresh provider version probe timed out. Historical source-service model proof is not replayed.
Preserve all old clips. Record drafts/finals in a new ignored directory and never overwrite a take.

After independently installing the wheel, use that environment and a copied bundle:

```powershell
.\.venv\Scripts\python.exe scripts/capture_release.py --python <installed-env-python> --bundle <intact-bundle-copy> --output .verification/sprint07/new-take --ffmpeg <existing-ffmpeg>
```

Use `--check-actions` to execute every native action without recording or reading holds.
The optional existing FFmpeg encodes a 1920×1080 H.264 MP4: original 1920×960 app frames are padded
with a separately labeled black 120-pixel caption footer. No results or app controls are overlaid.
The raw WebM, safe native report, measured cues, ASS captions and SHA-256 remain local.
