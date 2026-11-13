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
