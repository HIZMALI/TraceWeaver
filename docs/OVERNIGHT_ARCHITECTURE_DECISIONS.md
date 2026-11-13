# Overnight O4/O5 architecture decisions

Recorded after G0 inspection, 2026-11-13. Starting clean main: 0783201fb5d83c072fe215cf23135eb165a2213a.
Actual baseline: 337 passed in 47.79s, Ruff/pip check clean; Node 24.13.1/npm 11.8.0 available.
Existing native stores and all versioned artifacts are hashed in ignored overnight verification.

1. Build a React/TypeScript/Vite console under web, using @xyflow/react v12 and system fonts.
   Original graphite/teal CSS, deterministic layered layout, no CDN or UI framework. Runtime
   validators admit bounded API JSON. React text rendering, no HTML injection, source navigation,
   editor, uploads, external assets or browser-owned graph facts.
2. Add a versioned GET dashboard bundle: one worker-local read-only Investigation, then the
   existing explain_investigation and citation firewall on that exact object. Old routes/JSON
   stay unchanged. Publish a strict privacy-conscious projection, not raw graph properties/logs.
   The source fingerprint binds the original Investigation/options. A separate SHA-256 content
   digest binds the published safe view/explanation; client validates it before proof highlighting.
   A separate GET /console/incidents projects the existing bounded native incident-list query:
   legacy /incidents retains its raw display contract, while browser navigation must not receive
   private-looking titles or unsupported IDs. This additional projection is a privacy boundary,
   not a replacement graph repository or a change to legacy output.
3. Use only returned candidate/change/evidence/claim paths. Preserve ordered traversal separately
   from type/source_id/target_id stored arrow orientation. Validate path layout, scope, selected
   proof membership and exact claim support before exposing the bundle. No inferred missing edges.
4. URL query state is bounded/allowlisted: incident, claim/candidate/evidence/node/edge selection,
   window/caps. Invalid values visibly recover to defaults. Abort stale fetches; compare current
   request and snapshot before applying results. Back/forward restores state without ghost proof.
5. Make graph/citation/evidence/timeline/structured-comparison views keyboard accessible, with
   readable path-list alternative, text status labels and focus indicators. Mobile uses stacked
   tabs. Filters are visual only with hidden-item counts. Source and view caps remain distinct.
6. Ordinary GET/page load is deterministic and never contacts a model. G5 may add explicit same-
   origin POST capability/selection actions after security gates: fixed numeric loopback Host,
   exact Origin/port, JSON content type, bounded body, no permissive CORS, one in-flight model
   selection. Require current source fingerprint to prevent mixing a changed context. Reuse the
   existing fixed-loopback adapter and opaque-ID proposal/firewall, never accept prompts/tools.
7. Build static assets into a well-defined package resource directory for a single local FastAPI
   origin. Vite proxy is dev-only to 127.0.0.1. Node is not needed after a verified wheel build.
   Static fallbacks must not shadow API 404s. Launcher/check scripts use only project environments
   and immutable judge store; no system install, model pull, graph seed or public binding.
8. Vitest/Testing Library cover normalization/contracts/filters/URL/stale state. Playwright runs
   the actual backend, native immutable judge store and built UI. Controlled component/error
   fixtures are labelled separately. Capture real desktop/mobile/error screenshots; no fake UI.
9. Gates run in G0–G9 order. Necessary bundle plumbing can precede its G3 hardening gate so G1
   can consume coherent real data. Commit only passing checkpoints, maintain resumable progress,
   and report any unavailable browser/model/platform honestly. No artificial ten-hour waiting.

API references inspected: [React Flow](https://reactflow.dev/learn),
[Vite](https://vite.dev/guide/), [Playwright](https://playwright.dev/docs/ci).
Technical documentation/package setup access is separate from incident source verification.
