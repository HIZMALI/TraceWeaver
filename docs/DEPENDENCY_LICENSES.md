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
