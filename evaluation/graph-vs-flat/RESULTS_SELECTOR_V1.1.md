# Actual connected-retrieval study results

> R13 retains an invalid frozen cap-order assumption; see ERRATA.md. Thirteen remaining
> questions are valid. Their exact ID sets match native retrieval; lexical matches the two
> negative controls, while its per-question TP/FP/FN disclose partial matches and extra hits.
> Fixed-k retrieval and structured-intent differences prevent a general accuracy interpretation.

Same public node fields/all edge facts; structured native selectors vs BM25-like unjoined records. First read plus five repeated reads; setup/index/proof audit excluded. See README for intent asymmetry.

Gold SHA-256: `53e089d433a5f9de6c00105aa7837e1d9ae29016750ef6802f4cc0fde095db81`. Native store: {'node_count': 51, 'relationship_count': 67}. 
Exact ID sets: graph 13/14; flat 2/14.

No production/general accuracy or root-cause claim. Empty denominators are null in JSON.

| Case | Gold IDs | Native IDs | Flat IDs | Graph TP/FP/FN | Flat TP/FP/FN | Warm graph / flat median ms |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | DEP-001, DEP-002 | DEP-001, DEP-002 | DEP-001, DEP-003, DEP-002, CASE-DEP-NOCHANGE, CASE-DEP-UNRELATED | 2/0/0 | 2/3/0 | 3.8121 / 0.0635 |
| R02 | DEP-002 | DEP-002 | DEP-001, DEP-003, DEP-002, CASE-DEP-NOCHANGE, CASE-DEP-UNRELATED | 1/0/0 | 1/4/0 | 3.9044 / 0.0685 |
| R03 | CHG-001, CHG-002 | CHG-001, CHG-002 | CHG-001, CASE-CHG-AFTER, CASE-CHG-BEFORE, CASE-CHG-INVALID, CASE-CHG-OFFSET | 2/0/0 | 1/4/1 | 4.1000 / 0.0586 |
| R04 | EVD-001, EVD-002, EVD-003, EVD-004 | EVD-001, EVD-002, EVD-003, EVD-004 | EVD-003, EVD-001, EVD-002, EVD-004, EVD-006 | 4/0/0 | 4/1/0 | 3.9712 / 0.0844 |
| R05 | CASE-DEP-BEFORE, CASE-DEP-NOCHANGE | CASE-DEP-BEFORE, CASE-DEP-NOCHANGE | CASE-DEP-BEFORE, CASE-DEP-ONSET, DEP-001, DEP-003, CASE-DEP-NOCHANGE | 2/0/0 | 2/3/0 | 4.7411 / 0.0662 |
| R06 | CASE-DEP-OFFSET, CASE-DEP-ONSET | CASE-DEP-OFFSET, CASE-DEP-ONSET | CASE-DEP-AFTER, CASE-DEP-ONSET, CASE-DEP-OFFSET, DEP-001, DEP-003 | 2/0/0 | 2/3/0 | 4.7996 / 0.0741 |
| R07 | CASE-DEP-AFTER | CASE-DEP-AFTER | CASE-DEP-AFTER, CASE-DEP-ONSET, DEP-001, DEP-003, CASE-DEP-NOCHANGE | 1/0/0 | 1/4/0 | 4.7307 / 0.0703 |
| R08 | CASE-DEP-INVALID | CASE-DEP-INVALID | DEP-001, DEP-003, CASE-DEP-NOCHANGE, CASE-DEP-UNRELATED, CASE-DEP-INVALID | 1/0/0 | 1/4/0 | 4.7304 / 0.0621 |
| R09 | CASE-E-ORPHAN | CASE-E-ORPHAN | CASE-E-WRONG-SERVICE, CASE-E-EARLY, CASE-E-LATE, CASE-E-DEGRADED, CASE-E-FAILED | 1/0/0 | 0/5/1 | 4.6981 / 0.0969 |
| R10 | CASE-E-FAILED, CASE-E-HEALTHY | CASE-E-FAILED, CASE-E-HEALTHY | CASE-E-HEALTHY, CASE-E-FAILED, CASE-E-EARLY, CASE-E-LATE, CASE-E-WRONG-SERVICE | 2/0/0 | 2/3/0 | 4.6699 / 0.1047 |
| R11 | CASE-E-DEGRADED, CASE-E-FAILED, CASE-E-HEALTHY | CASE-E-DEGRADED, CASE-E-FAILED, CASE-E-HEALTHY | CASE-E-DEGRADED, CASE-E-FAILED, CASE-E-HEALTHY, CASE-E-WRONG-SERVICE, CASE-E-EARLY | 3/0/0 | 3/2/0 | 4.7743 / 0.0954 |
| R12 | ∅ | ∅ | ∅ | 0/0/0 | 0/0/0 | 2.1453 / 0.0013 |
| R13 | DEP-002 | DEP-001 | DEP-001 | 0/1/1 | 0/1/1 | 3.8710 / 0.0732 |
| R14 | ∅ | ∅ | ∅ | 0/0/0 | 0/0/0 | 4.1883 / 0.0016 |

Every graph matched edge was rechecked in native Relate after timing; exact triples, per-case precision/recall and descriptive timing p95 are in results.json. Flat edge facts are adjacent record facts, not a joined incident proof path.

This small authored task set favors explicit relational operations. The graph arm receives structured intent; the lexical arm gets text plus anchor/type/cap. A flat join engine can express the same relationships. Lexical retrieval may be much faster and has weaker relational scope; no universal winner is inferred.
