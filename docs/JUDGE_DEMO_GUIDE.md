# TraceWeaver: 110-second live demo

Use the intact synthetic judge bundle, a built console, one loopback origin and a desktop viewport
around 1440 × 900. Run `scripts/check-judge-demo.ps1`, then `scripts/start-judge-demo.ps1`.
Open http://127.0.0.1:8000/?incident=INC-001. No seeding, production data or hosted graph is needed.
Keep a deterministic fallback ready; model availability is not required to explain graph proof.

| Time | Exact action | Suggested narration |
| --- | --- | --- |
| 0–15s | Show INC-001 and the persistent causal/source-truth labels. | “Incident evidence is scattered. TraceWeaver makes the connected context and its citations inspectable. Embedded Relate 1.0.0 reads this persistent synthetic .rl file; no hosted graph service is involved.” |
| 15–40s | In Candidates click **DEP-001** on SVC-AUTH. Use **Focus selected paths**; read the inspector's full path and returned CHG-001. | “Payment depends on Auth. The stored TARGETS arrow goes from deployment to Auth; we traverse it in reverse to find a candidate. The path reaches the actual included change. DEP-002 is a competing candidate directly targeting Payment. Connection and BEFORE do not establish cause.” |
| 40–65s | In Proof inspector select **DEPLOYMENT BEFORE ONSET** for DEP-002. Inspect GRAPH_PATH and TEMPORAL entries. | “This admitted statement names DEP-002, its real directed path and 09:58 UTC time. Source prose and references are withheld. The server's semantic firewall checks citation scope before template rendering; the browser checks the shared snapshot before highlighting.” |
| 65–90s | Select **CASE-INC**, then **Observations**. Click the HEALTHY/FAILED conflict. Switch to Evidence and inspect CASE-E-NAIVE; optionally CASE-E-ORPHAN. | “One structured pair conflicts; two DEGRADED comparisons remain undetermined. These are matched service/signal/window observations, not a causal verdict. A naive timestamp stays unknown, and orphan evidence gets no invented service edge.” |
| 90–110s | Open **Gaps** and next checks. Optional preflighted model variation below. | “Partial context and missing evidence stay visible. Relate contributes actual multi-hop traversal and directed, persistent relationships. The result is a narrower investigation and concrete next checks. Cause remains NOT_ESTABLISHED; external truth remains NOT_PERFORMED.” |

For a 120-second model variation, replace the last section with the INC-001 local selection panel:
click **Compare with local AI selection**, choose the actually installed **qwen3:8b**, check the
confirmation, then **Run confirmed local selection**. Show requested/executed mode, exact model,
accepted claim/citation counts and a local claim's proof. One real invocation in this mission took
4.25 seconds and accepted seven claims, but do not promise that latency or selection on another run.
Say “AI selects opaque existing claim IDs; server templates still render facts. No cause or model
accuracy is established.” If unavailable/rejected/slow, show the honest status and continue offline.
Do not call CLI or API results a live AI demo unless that actual call succeeds.

Keyboard: Tab/Enter operate records; left/right arrows move detail tabs. Use the **Accessible path
list** below the graph for exact directions. On phone, use Graph / Inspector / Details and the
incident navigation menu. Visual filters change displayed items only; clear them before narration.
The **Guided demo** button offers four manual steps on these actual synthetic records.

Read [demo fact check](DEMO_FACT_CHECK.md), [genuine captures](screenshots/README.md),
[local measurements](LOCAL_PERFORMANCE.md) and [release limits](RELEASE_READINESS.md).
No finished video has been recorded or claimed. This is a storyboard for a genuine screen recording.
