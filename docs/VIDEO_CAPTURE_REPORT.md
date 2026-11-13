# Sprint 07 genuine video capture report

Status: **PASS — produced, decoded and reviewed locally; not uploaded.**
The final demonstration is **115.000 seconds, 1920×1080, H.264/yuv420p, 25 fps**, MP4 fast-start.
It is silent, with synchronized English explanatory captions in a separate black 120-pixel footer.
Original application pixels are 1920×960; no app results are overlaid or fabricated. The footer's
“NOT AI-GENERATED” describes the offline application behavior. Codex assisted caption/script/code
authoring, as disclosed in the submission draft. There is no recorded human or synthesized speech.

## Local artifacts

All videos remain ignored, outside versioned delivery source:

| Artifact under `.verification/sprint07/video-final/` | Purpose |
| --- | --- |
| `traceweaver-judge-115s-1080p.mp4` | Final captioned presentation, 5,290,900 bytes |
| `traceweaver-judge-115s.webm` | First 115 seconds of genuine VP9 source, stream-copy trim |
| `native-judge-demo.webm` | Preserved raw 1920×960 VP9 encoder output, 122.720s, 27,531,745 bytes |
| `source/` | Untouched Playwright source recording |
| `capture.json` | Measured action cues and real native offline report, no provider raw response |
| `captions.ass` | Measured successful-action subtitle cues |
| `encode.txt`, `media-*.json`, `frame-*.png` | Encoder, probe and frame-review evidence |

MP4 SHA-256: `f8b4b322024f2c023a2410a9b18ac27180c9934014883317d0a6a9e66d1723b4`.

Raw source SHA-256: `de07a5f8c251a57787423812f5dda54123d736b08b033d1cec0d0d47e686ceee`.
The trimmed WebM checksum is included in `reports/sprint07_release_evidence.json`.
Raw encoder duration exceeds the guided 115-second action timeline; the final clips use the first
115 seconds at original speed, with no retiming. The reviewed final gap/no-cause scene is included.
An earlier complete draft remains under `.verification/sprint07/video`; its graph/citation framing
was insufficient, so it was not selected as the final candidate. Both recordings are real captures.

## Actual execution and review

The capture launched the actual non-editable installed wheel outside the checkout, with Node absent
from its server PATH, on numeric loopback, reading a copied intact synthetic Relate bundle. Its
graph check returned 51 nodes/67 relationships. INC-001 has 14 returned arrows, two candidate/target
pairs and four evidence records. The sole POST was `/console/agent/rehearse`; zero foreign requests,
zero page errors and zero model calls occurred. Judge bytes and manifest were unchanged afterward.

The real offline rehearsal executed get_incident_scope, trace_deployment, inspect_evidence and
inspect_gaps: **23 native queries, eight admitted claims, eleven citations, zero model interactions**.
Both AI flags were false, cause NOT_ESTABLISHED and external verification NOT_PERFORMED.

All final MP4 frames were decoded successfully with existing FFmpeg 9.0.2. Probe confirmed H.264,
1080p, 25 fps and exactly 115.000 seconds. VP9 WebM is also supplied. No encoder was installed or
redistributed. Existing project-local/system-accessible tools only were executed.

Ten extracted frames were visually reviewed:

| Time | Observed real content |
| --- | --- |
| 2s | Synthetic incident, embedded Relate/read-only notices, starting action, no-cause status |
| 18s | Payment/Auth/DEP-001/CHG-001 stored path and competing pair; graph/inspector readable |
| 31s | DEP-002 targets Payment, competing context retained |
| 43s | Actual admitted claim, GRAPH_PATH and TEMPORAL 09:58 UTC citations visible |
| 56s | EVD-001 TRACEABLE/SYNTHETIC inspector and real evidence table |
| 69s | CASE-INC matching HEALTHY/FAILED conflict and two UNDETERMINED pairs |
| 80s | CASE-E-NAIVE Unknown / INVALID_TIMESTAMP, original naive value retained |
| 93s | Real offline four-step trace, 23 queries, 8 claims/11 citations, false AI flags |
| 103s | Executed step 2 reverse TARGETS and INCLUDES_CHANGE directed proof |
| 112s | Actual STRUCTURED_SIGNAL_GAPS, next checks, no-cause/unverified closing caption |

Caption cues follow measured successful actions at 0.359, 12.145, 25.080, 37.145, 50.212,
62.423, 75.209, 85.408, 99.126 and 107.137 seconds. Five-to-fifteen-second holds are intentional
video reading time. See [the exact script](SPRINT07_VIDEO_SCRIPT.md) and capture automation.

The small versioned [thumbnail](screenshots/sprint07/video-thumbnail.jpg) was extracted from the
actual 18-second MP4 frame and reviewed. Original 7.28-second Sprint 06 clip and historical captures
remain byte-identical. No new live-model footage or screenshot exists: the provider preflight timed
out before eligibility checks or inference. Historical source-service L3 was never spliced in.

## Reproduce and hand off

Follow the script's installed-wheel `scripts/capture_release.py` command with a new ignored output
directory and an already installed FFmpeg. Without FFmpeg the real raw WebM is still preserved;
do not automatically install an encoder. `--check-actions` runs the complete real flow without timed
holds; it also passed against the final wheel. Never overwrite prior takes or upload automatically.

The owner must review the playable final MP4, confirm content/rights and upload it to an accessible
location before adding a Devpost video link. “Local video PASS” does not imply publication, audio
narration, production validation or live AI success.
