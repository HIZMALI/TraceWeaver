# TraceWeaver synthetic explanation evaluation

Cases: 19; passed: 19; failed: 0.

Causation NOT_ESTABLISHED; external verification NOT_PERFORMED.

Model transports and live inference are verified separately, not by this offline suite.

| Case | Result | Assertions |
| --- | --- | ---: |
| X01 | PASS | 24 |
| X02 | PASS | 28 |
| X03 | PASS | 21 |
| X04 | PASS | 21 |
| X05 | PASS | 20 |
| X06 | PASS | 21 |
| X07 | PASS | 19 |
| X08 | PASS | 20 |
| X09 | PASS | 20 |
| X10 | PASS | 21 |
| X11 | PASS | 21 |
| X12 | PASS | 19 |
| X13 | PASS | 19 |
| X14 | PASS | 20 |
| X15 | PASS | 21 |
| X16 | PASS | 22 |
| X17 | PASS | 19 |
| X18 | PASS | 20 |
| X19 | PASS | 21 |

Metrics count returned admitted claims/citations, not whole-graph completeness.
Truncated cases excluded from completeness: X12, X13

```json
{
  "abstention_observed": 1,
  "abstention_required": 1,
  "actual_graph_edges": 181,
  "admitted_claims": 231,
  "adversarial_attempted": 133,
  "adversarial_rejected": 133,
  "deterministic_repeat": 19,
  "expected_graph_edges": 181,
  "generated_claims": 231,
  "noncausal_cases": 19,
  "required_warnings_present": 10,
  "required_warnings_total": 10,
  "reviewed_claims_correct": 32,
  "reviewed_claims_total": 32,
  "validated_citations": 380,
  "validated_claims": 231
}
```
