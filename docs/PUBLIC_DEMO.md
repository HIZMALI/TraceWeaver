# Public synthetic demo deployment

The dedicated `traceweaver.public_demo:app` serves the real embedded Relate 1.0.0 judge graph.
It does not mount the local application. `LocalConsoleBoundary`, the local judge launcher, legacy
GET contracts and local Ollama actions retain their existing behavior. Node 24 builds a separate
public frontend; Python 3.11 runs the installed wheel without Node in the runtime image.

## Public surface

Only GET is accepted. Unknown paths return 404; other methods on permitted paths return 405.

| Path | Behavior |
| --- | --- |
| `/` | Dedicated public-build HTML, including query-based incident/deep-link navigation |
| `/assets/{name}` | Only the index's exact hashed JS/CSS and required third-party notices |
| `/health` | Minimal readiness; the approved graph and manifest must still match |
| `/console/incidents` | Existing bounded, privacy-projected native incident list |
| `/incidents/{id}/dashboard` | Existing native investigation, deterministic explanation and typed proof |
| `/public/rehearsal/{id}` | Explicit snapshot-bound deterministic native tool plan; never inference |

The last route requires a 64-character lowercase `source_fingerprint` from the current dashboard.
It accepts only the four existing investigation options and one of four declared `intent` enums.
No model, prompt, URL, source path, arbitrary query or extra field is accepted. Duplicate parameters
are rejected. A stale/cross-incident snapshot returns 409. The same four-tool INC-001 plan executes
23 actual native queries and admits eight claims / eleven citations. Both AI flags are false and
model interactions remain zero. It shares the existing final citation firewall and support checks.

Every local model/selection/agent POST, legacy raw-context route, ingestion/query/upload/admin route,
OpenAPI/docs and WebSocket is absent. Hiding controls is not the security boundary: the server itself
rejects these requests. The public UI offers native rehearsal but no model discovery or inference.

## Immutable data and admission

The only accepted graph is `examples/judge-demo/traceweaver-demo.rl`: 51 nodes / 67 relationships,
SHA-256 `29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239`.
The exact manifest digest is `50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab`.
Startup validates exact bytes, the native graph, fixtures/demo flags and the public asset marker.
Missing/corrupt/changed artifacts fail closed; nothing is seeded, repaired or regenerated.
Graph reads recheck both digests before/after the existing services execute. Native readers open,
query and close on the same worker thread; no connection is shared with another thread.

Exactly one application worker and one instance are used. At most two graph requests run at once.
A constant-space, process-wide bucket has capacity 60 and refills at two units/second. Dashboards/
lists cost one unit; rehearsal costs four. Rejection is 429 with Retry-After. This is not per-IP or
distributed DDoS protection. Row caps do not bound arbitrary native RAM/work; only the exact tiny
approved graph is admitted. Health checks remain outside the expensive-read budget.

Host is an exact configured authority. Supplied Origin must match its configured HTTPS origin;
CORS is not enabled. Forwarded headers cannot choose the Host, scheme or throttling identity.
The launcher explicitly disables Uvicorn proxy trust/access logging. Security headers include CSP,
frame denial, nosniff, no-referrer and restricted browser permissions; APIs/HTML are no-store.
No private source text/reference or raw validation/exception detail is returned.

## Reproduce the deployment artifact

Docker is optional deployment/test tooling, not a local application runtime dependency. The
multi-stage Dockerfile pins official Node 24 and Python 3.11 image digests, builds a wheel, installs
it independently, drops root and ships only the public assets and approved graph/manifest. The
default-deny Docker context excludes user stores, secrets, local drafts, audit logs and caches.
The graph/manifest have read-only file permissions. Local verification additionally enforces a
read-only container filesystem, 512 MiB, 0.1 CPU and a host port bound only to 127.0.0.1:

```powershell
docker build --tag traceweaver-public:verify .
.\.venv\Scripts\python.exe scripts/verify_public_container.py --image traceweaver-public:verify --output .verification/public-container-check
```

Use a fresh output directory. Install the project's Playwright Chromium test client first; Node
runs that client outside the server image. The verifier runs real browser/proof/security cases,
checks installed package location and unchanged data, reports actual cgroup peak memory when
available, then stops only its owned container. This is a measured synthetic workload, not a
guarantee about all Render traffic or native-query resource usage.

## Render Free setup

Use the repository's `render.yaml`, or create a **Web Service** from the public repository URL:

1. Repository `https://github.com/HIZMALI/TraceWeaver`, branch `main`, root directory blank.
2. Language **Docker**, Dockerfile `./Dockerfile`, context repository root. Keep its CMD; do not
   replace it with the local launcher. It binds `0.0.0.0:$PORT` only inside the hosting/container.
3. Instance type **Free**, one instance, health check `/health`, no disk or additional database.
   Stop if Free is unavailable or payment/upgrade is required; no billing change is authorized.
4. Set `PORT=10000` and `TRACEWEAVER_PUBLIC_BUNDLE=/app/judge-demo` if creating manually.
   Render supplies `RENDER_EXTERNAL_HOSTNAME`; do not use a wildcard host or enable the HTTP-test flag.
5. Prefer automatic deployment after CI checks pass. Wait for a successful deployment and verify
   its assigned HTTPS URL anonymously; a prepared configuration is not evidence of a live service.

For explicit local container tests only, `TRACEWEAVER_PUBLIC_HOSTS` can select a numeric-loopback
authority and `TRACEWEAVER_PUBLIC_ALLOW_HTTP=1` permits that HTTP origin. The HTTP exception refuses
non-loopback hosts. Never run the public launcher directly on the owner's network; use the existing
local judge launcher or the loopback-bound container verifier.

Render Free sleeps after 15 idle minutes; waking can take about a minute. Its filesystem is
ephemeral and shared monthly free hours/usage limits apply. This is suitable for an immutable demo,
not a production SLA. See current [Free service limits](https://render.com/docs/free),
[Blueprint reference](https://render.com/docs/blueprint-spec),
[Docker deployment](https://render.com/docs/docker) and [health checks](https://render.com/docs/health-checks).

## External acceptance

Set `TRACEWEAVER_PUBLIC_BASE_URL` to the actual assigned HTTPS origin and run
`npm --prefix web run test:public`. The same browser suite checks real INC-001 paths, competing
candidates, CASE-INC comparisons, citations, native offline tools, desktop/tablet/phone/keyboard,
HTTPS assets, rejected privileged APIs, no external source/model requests and no page errors.
No local server is started in external mode. Record the deployed Git SHA and its own successful CI;
update the README only after the assigned URL genuinely passes. No Devpost or video upload occurs.
