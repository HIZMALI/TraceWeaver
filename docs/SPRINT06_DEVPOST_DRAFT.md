# TraceWeaver — unsubmitted Devpost draft

**Status:** Local prototype and draft only. Public repository URL, license and final video URL
are owner-pending. No award, public deployment, production validation or submission is claimed.

## Inspiration

During incident review, a nearby deployment is an investigation lead. Its relationship to an
affected service, evidence timestamps and missing source context should be inspectable before
anyone treats an explanation as a conclusion.

## What it does

TraceWeaver reads an embedded persistent Relate graph and presents candidate deployment paths,
UTC classifications, structured observation disagreements and provenance gaps. Select a candidate
or an admitted statement to inspect exact stored edge directions and citation support.

“Rehearse graph investigation” runs a fixed offline plan through real read-only native tools.
It works without a model and is explicitly not AI-generated. The experimental local agent can
choose among the same five tools using opaque IDs. It cannot submit Cypher, follow source URLs,
write the database or supply factual prose. Final claim IDs must pass the existing semantic
citation firewall and actual retrieved-support checks. The conclusion remains NOT_ESTABLISHED.

## How we built it

Python/FastAPI with Relate 1.0.0, strict Pydantic contracts, deterministic claim templates,
React/TypeScript and React Flow. Worker-local native connections close before optional fixed
loopback Ollama calls. Bounded steps and source fingerprints prevent mixed-snapshot proof.
The prepared judge dataset is explicitly synthetic and manifest-verified. Original data and
historical evaluations remain unchanged. Build once; the packaged Python server runs without Node.

## What currently works and what remains

Offline native rehearsal, proof inspection, structured conflict/unknown handling and isolated
synthetic evaluation are verified locally. One genuine qwen3:8b run selected a native
trace_deployment; its final proposal failed strict admission. Later local service checks were
unavailable. We therefore do not claim a fully accepted live AI investigation or model accuracy.
Controlled protocol tests are separate from live evidence. Timings are local descriptive samples.

Graph structure matters here because every tool returns actual incident membership and stored
directed relationship paths. No graph-versus-flat speed or universal accuracy advantage is claimed.
Hashes and TRACEABLE metadata do not authenticate source truth. Causal inference/remediation and
production integrations remain outside scope. Other platforms and remote CI are unverified.

## AI and third-party disclosure

Development was materially assisted by Codex. Optional runtime Ollama selects tool/claim IDs;
server-rendered facts still require graph-grounded citations. Significant AI assistance, actual
model/runtime evidence, dependency notices and limitations must remain disclosed in the submitted
version. Owner must review rights/attribution for source, models, data and the original video.

Owner completion fields: public GitHub/setup URL; selected license; original accessible 1–2 minute
demo URL; team/eligibility details; organizer clarification if needed. See release readiness and
competition fact check. No URL placeholders should be presented as a working public deployment.
