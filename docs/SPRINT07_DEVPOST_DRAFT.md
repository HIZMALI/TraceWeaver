# TraceWeaver — submission draft (not submitted)

**Tagline:** Connected incident evidence, inspectable graph paths, honest uncertainty.

## Inspiration

Incident investigations involve services, dependency chains, deployments, changes and observations.
A list of matching text cannot itself show which stored relationship connects a particular candidate.
TraceWeaver makes that context inspectable while keeping source authenticity and causation unresolved.

## What it does

The offline console reads the real embedded Relate 1.0.0 synthetic `.rl` store. It shows directed
paths, competing deployment/target pairs, UTC event times, evidence provenance quality, structured
conflicts, undetermined comparisons and gaps. The starting action exposes an exact stored path.
Server-admitted explanations use controlled templates and typed citations checked against the same
snapshot. TRACEABLE is a metadata classification, not independently VERIFIED source truth.

An explicit deterministic rehearsal executes actual bounded read-only Relate tools and exposes their
results. It is labeled offline and not AI-generated. An optional local Ollama agent may choose
allowlisted tools and opaque existing claim IDs; arbitrary Cypher and model-authored facts are not
accepted. It is experimental and not required for installation or the main demonstration.

## How we built it

Python/FastAPI/Pydantic and the native Relate Python package provide the engine and read-only API.
React/TypeScript/React Flow render the directed graph and keyboard-accessible proof inspector.
Connections open, execute and close in their own worker thread before optional inference. The
wheel contains built console assets; the synthetic graph is supplied separately with a manifest.
The Windows local export includes compatible runtime wheels for offline installation.

## Demonstrated versus planned

| Feature | Actual state |
| --- | --- |
| Embedded persistent Relate / native read-only graph tools | Implemented, locally exercised |
| Typed citation validation / exact stored directions | Implemented, unchanged firewall |
| Onboarding / competing paths / unknown time / conflicts and gaps | Implemented, responsive/keyboard/axe checked |
| Deterministic tool rehearsal | Implemented, four tools / 23 queries on INC-001, not AI |
| Optional model-directed tools | Experimental; historical source-service L3 succeeded in Sprint 06B |
| Current Sprint 07 installed-browser L3 | BLOCKED: fresh fixed-loopback version probe timed out; no inference attempted |
| Finished offline presentation | Genuine 115-second silent captioned browser recording, local review only |
| Windows Python 3.14 | Actually tested |
| Python 3.11 / Ubuntu / hosted CI | Runtime NOT RUN / NOT RUN / UNVERIFIED |
| Production integration / source authentication / causal verdict | Outside implemented scope; no claim |
| Public hosting / public repo / video upload / license / submission | Owner pending |

## Challenges and limits

Native connections are thread-affine; snapshot binding, finite reads and explicit truncation prevent
unbounded context from being presented as complete. The semantic firewall rejects cross-snapshot,
unsupported or excessive claim selections. Model availability and latency remain unreliable: a
previous source-service success is not a current installed-browser success. Historical
AGENT_FINISH_SCHEMA field-level cause remains unresolved. We retained the existing budgets.

The frozen evaluations exercise synthetic graph scenarios and controlled protocol cases, not model
accuracy or production reliability. The graph-versus-flat study has only 13 valid questions under
its published correction. No universal retrieval advantage is asserted. Source truth is always
NOT_PERFORMED and cause NOT_ESTABLISHED.

## Source and AI-assistance disclosure for owner review

TraceWeaver was developed with substantial assistance from OpenAI Codex for implementation,
debugging, tests, documentation, release automation and guided Playwright capture. This disclosure
does not imply OpenAI or event-organizer endorsement. The owner must review the development dates,
any reused code, dependency notices and their own authorship/rights before final submission.
Runtime offline explanations and tool rehearsal are deterministic, not AI-generated. Optional local
model inference has a separate visible status. The video uses actual application frames and labeled
explanatory captions; no generated image or fabricated model result is used.

## Video description (under the two-minute limit)

The 115-second recording opens the synthetic Payment incident in a genuinely installed local wheel.
It follows Payment → Auth ← Deployment → Change, compares a second candidate, inspects an admitted
claim and its UTC/path citations, distinguishes provenance metadata from source truth, and opens
CASE-INC's one conflict and two undetermined comparisons. A naive timestamp remains unknown.
An explicit offline rehearsal runs four real Relate tools; its trace shows 23 native queries, eight
admitted claims and eleven citations. The final view exposes gaps and preserves no-cause/source-
unverified limits. It is silent with synchronized English explanatory captions. No live model run
is represented. Owner must review and upload it to an accessible location before supplying a link.

**Fields still required:** owner/team, confirmed eligibility and project start/reuse disclosure,
chosen project license, public repository URL with required topic, observed hosted CI, accessible
video URL, selected genuine screenshots and owner approval. See SPRINT07_PUBLIC_READINESS.md.
