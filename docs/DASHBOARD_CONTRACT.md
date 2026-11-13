# Local console contract

The original health, incident, context, investigation and explanation GET contracts remain intact.
`GET /console/incidents` is a safe metadata projection, bounded to 100 with lookahead.
`GET /incidents/{id}/dashboard` returns version 1.0 `DashboardBundle`. The window parameters
are 0–1440 minutes; candidate/evidence caps are 1–100. Invalid new-console inputs receive a
generic 422 without echoed input. Missing incidents return 404; incompatible/unavailable
stores return generic 503. No route creates or seeds a database.

One synchronous worker opens one read-only native Relate connection, runs the existing
investigation and a bounded native label audit, then closes before explanation rendering.
The source fingerprint covers the canonical full Investigation including effective options.
The view fingerprint covers the privacy projection, explanation and source fingerprint.
Digests check shared content; they do not authenticate a source or establish external truth.
There is no database writer, model call or external source fetch in these GET routes.

The browser accepts strict bounded DTOs, verifies scope/digest before displaying them and
discards stale/aborted responses. Unknown selection IDs show a warning and no ghost proof.
Only actual returned paths and affected-service citations produce displayed relationships.
Arrows use persisted source/target; TARGETS may be traversed in REVERSE, separately labelled.
Native labels must match every persisted relationship's schema; ambiguous IDs fail closed.
Graph rendering caps are 300 nodes and 600 edges. Source row caps and omitted paths stay visible.

Raw properties, evidence prose and source references are absent. Short display labels are
bounded and obvious HTML/URL/path/credential forms withheld; this is a minimization rule,
not a universal secret detector. IDs must satisfy the established safe-identity contract.
Unknown timestamps remain unknown with warning/original handling; ingestion time is never used.
TRACEABLE, UNVERIFIED_EXTERNAL and NOT_PERFORMED describe different dimensions.
All conclusions remain NOT_ESTABLISHED.

New console/index/assets accept numeric `127.0.0.1` Host matching the ASGI server's exact port.
Supplied Origin must match that origin. No forwarding headers are trusted and no CORS is enabled.
Legacy endpoints keep their compatibility surface; this is a local console, not an authenticated
multi-user deployment. Bind Uvicorn to 127.0.0.1 without proxy-header trust.
JSON responses are no-store; built index has CSP, nosniff and no-referrer headers.
Vite is a developer-only same-machine proxy; production judge use has one FastAPI origin.

## Explicit local POST actions

`POST /console/models/capabilities` accepts only `{"action":"LIST_INSTALLED_MODELS"}`.
Only a direct UI click sends it. It lists up to 32 eligible actual installed tags, never pulls.
`POST /console/selection` requires incident_id, options, source_fingerprint, model_id and
confirmed=true. No prompt, URL, tools, arbitrary provider host or additional fields are accepted.
Both require exact application/json, at most 2048 bytes, shallow duplicate-free JSON and a
two-second body deadline. Exact numeric loopback Host/port and Origin and local client are
mandatory. No cookies, credentials, CORS or forwarding-header trust. One in-flight local action
per application process; multiple server workers are unsupported for this single-user demo.
Use the packaged single-origin launcher for UI selection; the Vite proxy does not rewrite Origin.

Selection rereads the native graph and checks the exact source fingerprint before inference;
changed context receives 409. Native connection closes before the established fixed
127.0.0.1:11434 adapter (45-second total deadline). Actual tags are checked again by the adapter.
Provider failures produce NONE / MODEL_UNAVAILABLE or MODEL_OUTPUT_REJECTED, empty accepted claims,
no automatic fallback. No model prose/prompt/raw response is exposed or stored. The browser
retains the deterministic view and checks selection scope before highlighting. Client cancellation
only cancels waiting; server/daemon work may continue to its deadline and retains the action lock.

Two pre-existing OpenAPI method-set assertions were extended solely for these exact two POST
routes; all previous routes still assert GET only. No other pre-existing test expectations changed.
