# Actual connected-retrieval study results

> First actual run, preserved before selector repair. R11's selector was incomplete and R13's
> frozen cap-order assumption is invalid. See ERRATA.md and RESULTS_SELECTOR_V1.1.md. Do not
> interpret the raw 14-case total as accuracy. No frozen expectation or lexical setting changed.

Same public node fields/all edge facts; structured native selectors vs BM25-like unjoined records. First read plus five repeated reads; setup/index/proof audit excluded. See README for intent asymmetry.

Gold SHA-256: `53e089d433a5f9de6c00105aa7837e1d9ae29016750ef6802f4cc0fde095db81`. Native store: {'node_count': 51, 'relationship_count': 67}.
Exact ID sets: graph 12/14; flat 2/14.

No production/general accuracy or root-cause claim. Empty denominators are null in JSON.

| Case | Gold IDs | Native IDs | Flat IDs | Graph TP/FP/FN | Flat TP/FP/FN | Warm graph / flat median ms |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | DEP-001, DEP-002 | DEP-001, DEP-002 | DEP-001, DEP-003, DEP-002, CASE-DEP-NOCHANGE, CASE-DEP-UNRELATED | 2/0/0 | 2/3/0 | 4.6963 / 0.0755 |
| R02 | DEP-002 | DEP-002 | DEP-001, DEP-003, DEP-002, CASE-DEP-NOCHANGE, CASE-DEP-UNRELATED | 1/0/0 | 1/4/0 | 4.4948 / 0.0760 |
| R03 | CHG-001, CHG-002 | CHG-001, CHG-002 | CHG-001, CASE-CHG-AFTER, CASE-CHG-BEFORE, CASE-CHG-INVALID, CASE-CHG-OFFSET | 2/0/0 | 1/4/1 | 4.6909 / 0.0680 |
| R04 | EVD-001, EVD-002, EVD-003, EVD-004 | EVD-001, EVD-002, EVD-003, EVD-004 | EVD-003, EVD-001, EVD-002, EVD-004, EVD-006 | 4/0/0 | 4/1/0 | 4.3119 / 0.0896 |
| R05 | CASE-DEP-BEFORE, CASE-DEP-NOCHANGE | CASE-DEP-BEFORE, CASE-DEP-NOCHANGE | CASE-DEP-BEFORE, CASE-DEP-ONSET, DEP-001, DEP-003, CASE-DEP-NOCHANGE | 2/0/0 | 2/3/0 | 5.1684 / 0.0706 |
| R06 | CASE-DEP-OFFSET, CASE-DEP-ONSET | CASE-DEP-OFFSET, CASE-DEP-ONSET | CASE-DEP-AFTER, CASE-DEP-ONSET, CASE-DEP-OFFSET, DEP-001, DEP-003 | 2/0/0 | 2/3/0 | 5.6202 / 0.0797 |
| R07 | CASE-DEP-AFTER | CASE-DEP-AFTER | CASE-DEP-AFTER, CASE-DEP-ONSET, DEP-001, DEP-003, CASE-DEP-NOCHANGE | 1/0/0 | 1/4/0 | 5.3968 / 0.0788 |
| R08 | CASE-DEP-INVALID | CASE-DEP-INVALID | DEP-001, DEP-003, CASE-DEP-NOCHANGE, CASE-DEP-UNRELATED, CASE-DEP-INVALID | 1/0/0 | 1/4/0 | 5.7261 / 0.0727 |
| R09 | CASE-E-ORPHAN | CASE-E-ORPHAN | CASE-E-WRONG-SERVICE, CASE-E-EARLY, CASE-E-LATE, CASE-E-DEGRADED, CASE-E-FAILED | 1/0/0 | 0/5/1 | 5.3352 / 0.1066 |
| R10 | CASE-E-FAILED, CASE-E-HEALTHY | CASE-E-FAILED, CASE-E-HEALTHY | CASE-E-HEALTHY, CASE-E-FAILED, CASE-E-EARLY, CASE-E-LATE, CASE-E-WRONG-SERVICE | 2/0/0 | 2/3/0 | 5.1551 / 0.1130 |
| R11 | CASE-E-DEGRADED, CASE-E-FAILED, CASE-E-HEALTHY | CASE-E-DEGRADED, CASE-E-FAILED, CASE-E-HEALTHY, CASE-E-WRONG-SERVICE | CASE-E-DEGRADED, CASE-E-FAILED, CASE-E-HEALTHY, CASE-E-WRONG-SERVICE, CASE-E-EARLY | 3/1/0 | 3/2/0 | 5.1913 / 0.1001 |
| R12 | ∅ | ∅ | ∅ | 0/0/0 | 0/0/0 | 2.2964 / 0.0012 |
| R13 | DEP-002 | DEP-001 | DEP-001 | 0/1/1 | 0/1/1 | 4.2071 / 0.0777 |
| R14 | ∅ | ∅ | ∅ | 0/0/0 | 0/0/0 | 4.4408 / 0.0020 |

Every graph matched edge was rechecked in native Relate after timing; exact triples, per-case precision/recall and descriptive timing p95 are in results.json. Flat edge facts are adjacent record facts, not a joined incident proof path.

This small authored task set favors explicit relational operations. The graph arm receives structured intent; the lexical arm gets text plus anchor/type/cap. A flat join engine can express the same relationships. Lexical retrieval may be much faster and has weaker relational scope; no universal winner is inferred.
