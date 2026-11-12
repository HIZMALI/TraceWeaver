# TraceWeaver offline synthetic evaluation

Suite: `traceweaver-sprint02-frozen-gold-v1`

Scenarios: 20; passed: 20; failed: 0.

Causation: NOT_ESTABLISHED. External verification: NOT_PERFORMED.

These are synthetic relevance/path metrics, not root-cause accuracy.

| Case | Result | Assertions | Failures |
| --- | --- | ---: | ---: |
| E01 | PASS | 56 | 0 |
| E02 | PASS | 44 | 0 |
| E03 | PASS | 122 | 0 |
| E04 | PASS | 63 | 0 |
| E05 | PASS | 62 | 0 |
| E06 | PASS | 38 | 0 |
| E07 | PASS | 92 | 0 |
| E08 | PASS | 92 | 0 |
| E09 | PASS | 122 | 0 |
| E10 | PASS | 27 | 0 |
| E11 | PASS | 27 | 0 |
| E12 | PASS | 21 | 0 |
| E13 | PASS | 68 | 0 |
| E14 | PASS | 33 | 0 |
| E15 | PASS | 45 | 0 |
| E16 | PASS | 56 | 0 |
| E17 | PASS | 56 | 0 |
| E18 | PASS | 44 | 0 |
| E19 | PASS | 26 | 0 |
| E20 | PASS | 33 | 0 |

## Metrics and denominators

```json
{
  "candidate_retrieval": {
    "excluded_truncated_cases": 2,
    "expected_count": 53,
    "false_negative": 0,
    "false_positive": 0,
    "included_case_count": 18,
    "precision": 1.0,
    "predicted_count": 53,
    "recall": 1.0,
    "true_positive": 53,
    "undefined_precision_cases": 5,
    "undefined_recall_cases": 5,
    "unit": "scenario_deployment_target_pairs"
  },
  "conflict_detection": {
    "excluded_truncated_cases": 2,
    "expected_count": 3,
    "false_negative": 0,
    "false_positive": 0,
    "included_case_count": 18,
    "precision": 1.0,
    "predicted_count": 3,
    "recall": 1.0,
    "true_positive": 3,
    "undefined_precision_cases": 15,
    "undefined_recall_cases": 15,
    "unit": "scenario_unordered_conflict_pairs"
  },
  "evidence_scope": {
    "excluded_truncated_cases": 2,
    "expected_count": 61,
    "false_negative": 0,
    "false_positive": 0,
    "included_case_count": 18,
    "precision": 1.0,
    "predicted_count": 61,
    "recall": 1.0,
    "true_positive": 61,
    "undefined_precision_cases": 1,
    "undefined_recall_cases": 1,
    "unit": "scenario_evidence_ids"
  },
  "graph_edges": {
    "agreement": 1.0,
    "correct": 432,
    "total": 432
  },
  "provenance": {
    "agreement": 1.0,
    "correct": 64,
    "total": 64
  },
  "temporal": {
    "agreement": 1.0,
    "correct": 120,
    "total": 120
  }
}
```
