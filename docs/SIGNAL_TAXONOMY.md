# Structured signal taxonomy — version 1

This documents the implemented Sprint 01 comparison rules; Sprint 02 does not change or
normalize them. Local tests verify the rules. Remote execution is not claimed. Numeric metric
interpretation, threshold policies, unit conversion, and natural-language classification are PLANNED.

| Example exact signal_key | Meaning of the supplied identity |
| --- | --- |
| availability | An explicitly named availability observation |
| error_rate | An explicitly named error-rate observation |
| latency | An explicitly named latency observation |
| queue_depth | An explicitly named queue-depth observation |

These are examples, not an automatic naming registry. Other bounded nonempty exact names may be
provided. No aliases, case folding, unit guessing, or merging of signals occurs. A number such as
0.05 or 900 does not become HEALTHY/FAILED without a separately approved future policy.

## Admissible observation

An evaluable observation needs explicit signal_key, observed_state, service_id, environment,
and a valid time instant or ordered closed observation interval. The service must be connected
by an actual OBSERVED_ON edge; evidence must belong to the queried incident through HAS_EVIDENCE.
Both interval endpoints are required when an interval is supplied; a partial/invalid interval
does not fall back to an observation point. Event/observation time is not ingestion time.

## State matrix

| Left / Right | HEALTHY | DEGRADED | FAILED |
| --- | --- | --- | --- |
| HEALTHY | No conflict | UNDETERMINED | CONFLICTING_OBSERVATIONS |
| DEGRADED | UNDETERMINED | No conflict | UNDETERMINED |
| FAILED | CONFLICTING_OBSERVATIONS | UNDETERMINED | No conflict |

Pairs must have equal incident scope, actual service, exact signal_key, and environment, and
overlapping closed UTC intervals (including equal instants). Different times/services/environments/
signals are not contradictions. Equal states do not authenticate either source. Missing/invalid
structured fields produce not-evaluable warnings, not invented observations.

The existing synthetic CASE-INC scenario remains **one conflicting pair and two undetermined
pairs**. The separate evaluation fixture includes different-context/time negative controls.

## Glossary

- **Supplied state:** the input author's explicit category, not an automatic threshold decision.
- **Comparable:** matching graph context and overlapping valid time; not independently verified.
- **Conflict:** opposite structured states under this limited matrix; not proof that a source lied.
- **UNDETERMINED:** different states without a declared opposition rule; not counted as a conflict.
- **TRACEABLE:** graph/source metadata can be traced; not factual truth.
- **Integrity MATCH:** raw bytes equal an expected digest; not source authenticity.
- **Causal conclusion:** always NOT_ESTABLISHED in the current investigation contract.
