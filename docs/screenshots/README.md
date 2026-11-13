# Genuine browser captures

Captured by `npm --prefix web run test:e2e` against the built console and actual native
Relate stores, Chromium 158.0.8127.18 on Windows. No intercepted graph responses or image generation.
Desktop viewport 1440 × 900; full-page images include content below the viewport.
Phone viewport 390 × 844. Captures are synthetic and intentionally public.

| File | Test / alt text |
| --- | --- |
| [01-connected-context.png](01-connected-context.png) | Native INC-001 graph, two competing deployments and read-only deterministic claims |
| [02-claim-proof.png](02-claim-proof.png) | Selected DEPLOYMENT_BEFORE_ONSET claim with actual graph and temporal citation; selected path focused |
| [03-structured-disagreement.png](03-structured-disagreement.png) | CASE-INC conflicting pair selected; two undetermined pairs remain separate |
| [04-gaps-next-checks.png](04-gaps-next-checks.png) | Actual CASE-INC gaps and server-provided next checks |
| [05-phone-records.png](05-phone-records.png) | Phone details view with actual INC-001 candidate records and persistent uncertainty |
| [06-safe-unavailable.png](06-safe-unavailable.png) | Owned test server with a genuinely missing temporary store, generic error without private path |

Regeneration deliberately replaces only these public captures. Store bytes and manifest are not changed.
Selected-path focus can crop unselected context; fit-view and the accessible path list remain available.
