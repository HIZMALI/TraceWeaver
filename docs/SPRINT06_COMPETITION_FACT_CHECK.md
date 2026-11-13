# Sprint 06 evidence and competition fact check

Checked 2026-11-13. The [official Devpost schedule](https://relate.devpost.com/details/dates)
lists December 11, 2026 at 18:00 PST. Fixed UTC−08:00 to Türkiye UTC+03:00 conversion gives
December 12 at 05:00 Türkiye. Recheck before submission.

The [official announcement](https://neo4j.com/blog/graph-database/announcing-the-relate-by-neo4j-hackathon-2026-build-ai-agents-on-an-embedded-graph-database/)
requests public GitHub source/setup and a 1–2 minute demo; it describes new work on existing
projects as acceptable. The [Devpost rules](https://relate.devpost.com/rules) have stricter new-project
wording, duplicate rule sections, unresolved placeholders, a bracketed video limit and differing
judging dates. Treat these as unresolved organizer wording, not permission inferred here. Owner
should confirm eligibility/rights, disclose significant AI assistance and conservatively document
new work within the contest period. No legal eligibility conclusion or submission is made.

| Demo statement | Exact implementation/evidence | Permitted interpretation |
| --- | --- | --- |
| Real persistent Relate | `storage.py`, `agent_tools.py`; original judge SHA below; independent native wheel check 51 nodes/67 edges | Actual engine, no fake graph repository |
| Payment → Auth ← DEP-001 → CHG-001 | trace_deployment TRACE_QUERY, actual `TARGETS DEP-001→SVC-AUTH`, `DEPENDS_ON SVC-PAYMENT→SVC-AUTH`, `INCLUDES_CHANGE DEP-001→CHG-001`; native/e2e tests and screenshot 02 | Connected candidate with explicit reverse traversal, no cause |
| Two competing baseline candidates | Existing investigate; INC-001 returns DEP-001/Auth and DEP-002/Payment | Returned scope, not whole-graph completeness |
| Same tools without a model | `agent_rehearsal.py`, separate CLI, real HTTP/native/browser tests; screenshots 03/05 | Fixed deterministic plan, both AI flags false |
| Genuine model-directed tool | `reports/sprint06_live_agent_evidence.json`; observed qwen3:8b trace_deployment with native result and safe IDs | Actual tool use, final schema rejected, zero admitted live claims/citations |
| Citation firewall | `retrieved_claims`, `admit_finish`, existing `CitationValidator`, controlled renderer; protocol attacks and browser proof tests | Semantic support in returned graph; never source truth/causality |
| Conflict vs unknown | Existing structured comparison service; CASE-INC one conflict/two UNDETERMINED pairs; screenshot 04 | Matching structured windows/context, not free-text contradiction detection |
| Safe local action | `local_console.py`, `bounded_action`, shared `single_action` lock, strict AgentRequest; HTTP/late/cancel tests | Numeric loopback + exact Origin/port, no public-host security claim |
| Test/evaluation success | Full recorded commands in sprint report; frozen A01–A35 suite committed before execution | Synthetic regressions; no root-cause or live-model accuracy metric |
| Local performance | `reports/sprint06_native_microprofile.json`, seven actual same-process samples per scale | Machine-specific descriptive timings; no superiority or native cost bound |
| Real images/video | `web/e2e/sprint06.spec.mjs`, `scripts/record_sprint06.mjs`; native-backed Chromium captures | Six actual images and a short silent execution clip, not fabricated UI/model output |

Original judge SHA-256:
`29b10010152ebf82fe61b7dd8eff71848f39963e58d7b7a56f0aecebf1150239`.
Manifest: `50bdfbf4f700aedd13b099cc8cb5224141ccdd3c917fd32f2373be6187741aab`.
New gold: `dce5da3e7561029a8877fb03a9de86961509f728694b6c22e01155e82dfa6295`.
TRACEABLE never means VERIFIED; digests establish byte equality only. Always finish with
NOT_ESTABLISHED / NOT_PERFORMED. Historical graph-versus-flat raw totals must not be marketed as
accuracy or runtime superiority; see the unchanged erratum and new research limitations note.
