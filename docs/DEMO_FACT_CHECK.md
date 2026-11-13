# Demo fact check

All examples below are synthetic. The on-screen graph is a partial returned subgraph, not an
assertion that the entire native store was visualized. “Supported” means support in returned context.

| Assertion | Actual evidence | Limit |
| --- | --- | --- |
| Embedded Relate 1.0.0, persistent file | Installed relate-db metadata; native GraphStore throughout tests; judge manifest | No hosted graph, alternate repository or CLI engine |
| Judge store 51 nodes / 67 relationships | Native check-judge-demo; immutable MANIFEST.json | Entire store counts differ from selected incident subgraph |
| INC-001 2 candidate/target pairs / 4 evidence | Actual GET dashboard and native tests | Returned scope only |
| INC-001 → SVC-PAYMENT → SVC-AUTH ← DEP-001 → CHG-001 | AFFECTS, DEPENDS_ON, reverse traversal of stored DEP-001 TARGETS SVC-AUTH, INCLUDES_CHANGE; every edge cross-checked in native Relate | Connection is not cause; accessible path list exposes exact orientation |
| Competing DEP-002 targets Payment | Actual TARGETS edge and candidate record; stored 09:58 UTC timestamp | BEFORE is temporal context only |
| Typed claim-to-proof highlight | Native dashboard cross-checks; frontend path/time/target mutation rejection; actual Playwright claim scenario | Content digest is not source authentication |
| CASE-INC 1 conflict / 2 undetermined | Actual structured pair data; Playwright observation scenario | No arbitrary free-text contradiction detection |
| Unknown/naive/orphan states persist | CASE-E-NAIVE / CASE-E-ORPHAN native graph, unit and real browser scenarios | No timestamp guessing or service edge fabrication |
| Offline explanation is not AI-generated | GET explanation/dashboard; no-provider-call tests; initial browser POST count zero | Offline means no inference, not a service worker/PWA |
| Optional real local selection | UI qwen3:8b invocation: OLLAMA, true, 7 claims / 17 citations, 4250ms; screenshot 07 | One runtime observation, not accuracy/throughput evidence |
| Model cannot submit arbitrary accepted facts/citations | Existing citation firewall + new unknown-ID/prose/timeout protocol tests | Controlled protocol tests are separate from live inference |
| Source text/private refs withheld | Adversarial native profile tests and actual browser scenario | Pattern minimization is not a universal secret detector |
| Local read-only app and preserved data | Before/after SHA-256 + native counts + read-only/thread-affinity cases | Not an authenticated multi-user/public deployment |
| Real installed package works without Node | External non-editable wheel, Node-free server PATH, actual Chromium 14-edge rendering | Windows/Python 3.14 only; other platforms unverified |
| Local responsiveness | Three native synthetic scales in LOCAL_PERFORMANCE.md | Descriptive local timings, no production speed claim |

Never say: proven root cause, authenticated source truth, perfect completeness, production-ready
remediation, measured LLM accuracy, winning competition result, successful remote CI or completed
video. No external source URL is followed. Devpost material is a draft and was not submitted.
