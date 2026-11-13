# Dependency notices

Original console layout/styles are project-authored; no stock images, CDN fonts or paid assets.
Installed package licenses were read locally for the pinned versions, not guessed from names.
`node scripts/frontend-licenses.mjs` collects the actual installed production dependency tree
(25 packages, including six type-only dependencies). Full upstream notices are committed in
[third-party-licenses.txt](../web/public/assets/third-party-licenses.txt) and copied into the
built wheel at `/assets/third-party-licenses.txt`. Regenerate after `npm ci` if dependencies change.

| Dependency | Version | Installed license |
| --- | --- | --- |
| React / React DOM | 19.3.1 | MIT |
| React Flow / xyflow system | 12.12.1 / 0.0.84 | MIT |
| Zod | 4.6.7 | MIT |
| Lucide React | 1.72.0 | ISC |
| Zustand / classcat / scheduler / use-sync-external-store | Locked transitive versions | MIT |
| d3 color/dispatch/drag/interpolate/selection/timer/transition/zoom | Locked 3.x versions | ISC |
| d3-ease | 3.0.2 | BSD-3-Clause |
| Relate Python engine | 1.0.0 | Apache-2.0 (installed dist-info/licenses/LICENSE) |
| FastAPI / Pydantic | Python lock | MIT |
| Uvicorn | Python lock | BSD-3-Clause |

Build/test tooling (Vite, TypeScript, Vitest, ESLint, Playwright, axe and testing-library) is
project-scoped development tooling, not a runtime service. Chromium test binaries are ignored,
not redistributed with the application. Python dependencies retain their own installed notices;
the TraceWeaver wheel does not bundle their binaries. The repository had no project LICENSE at
baseline; a public release should have the owner select the project's license. No license was
silently assigned to the user's existing work.

## Authorized public release

The owner has now explicitly selected Apache-2.0 for eligible original TraceWeaver material.
See the canonical root LICENSE and project NOTICE. This supersedes the earlier pending decision;
third-party code, trademarks, models and separately produced footage/narration retain their own terms.
The wheel builder verifies both license files and its SPDX License-Expression. No dependency
binary is embedded in the project wheel; frontend production notices remain bundled with its assets.

The public-release review enumerated 31 installed Python distributions and all npm lock entries.
The direct/transitive application stack uses Apache-2.0, MIT, BSD, ISC and PSF terms as recorded
in the installed notices. Existing extra HTTP tooling includes certifi under MPL-2.0; no certifi
source is copied into the TraceWeaver distribution. Development-only axe/lightningcss packages
include MPL-2.0 and minimatch tooling uses BlueOak-1.0.0. Those tools are not shipped as application
source or runtime binaries; their licenses are not replaced by the project's Apache grant.

System fonts are referenced by family name, not redistributed as font binaries. Graphics and
screenshots are project-authored synthetic UI, with licensed Lucide icons covered by the existing
notices. Existing FFmpeg was used as a local recording tool and is not redistributed. Optional
Qwen/Ollama weights and Kokoro TTS assets are absent from Git. The local final narration uses
Kokoro af_heart (Apache-2.0 model declaration, MIT integration); dependency/model notices were
preserved with that separate production kit. No narrated video or audio is published in this task.
