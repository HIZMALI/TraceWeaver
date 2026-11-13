# Frozen study review: retain errors openly

The first actual run (`results.json` / `RESULTS.md`) scored native 12/14 and flat 2/14 exact sets.
The gold file remains byte-identical to freeze commit 1c8d1fa, SHA-256
53e089d433a5f9de6c00105aa7837e1d9ae29016750ef6802f4cc0fde095db81.

R11 exposed a bug in the new evaluation-only availability selector: it checked OBSERVED_ON and
signal_key but omitted consistency with the structured service_id field. The frozen fixture
literally links CASE-E-WRONG-SERVICE to CASE-API while its structured service_id says CASE-AUTH.
The frozen expected set/basis requires matching structured context. Selector revision 1.1 adds
that field check. The existing investigation engine and fixture/gold were not changed. This is
a disclosed selector repair after results, not an independently blinded model comparison.

R13 has an **invalid gold assumption**. It calls source capping “depth-first” and expects DEP-002.
The pre-existing `src/traceweaver/queries.py` INVESTIGATION_CANDIDATES orders by deployment.id,
target.id **before LIMIT**; `investigation.py` only sorts the returned subset by temporal category,
depth and time afterward. Thus the cap-one source contains DEP-001. This rule is visible in the
unchanged starting source, independently of runtime predictions. Changing engine behavior would
break the preserved contract. We neither change the frozen expected ID nor call this an engine
failure. Keep its raw TP/FP/FN and failed exact comparison; identify it as an invalid question.

Thirteen remaining independently frozen questions are valid for this illustrative study (within
the requested 10–15 range). Do not present raw 14-case exact-set totals as accuracy: they include
R13's invalid expectation. The validated-selector output is a new artifact, preserving the first
run. The lexical baseline, tokenization, constants, gold IDs and fixtures remain unchanged.
No parameters were tuned for a win. Structured-intent asymmetry and lexical latency advantage
remain explicit; this is not a general benchmark or a claim of production correctness.
