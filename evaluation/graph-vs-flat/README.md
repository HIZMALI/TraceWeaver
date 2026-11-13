# Connected retrieval vs flat lexical retrieval: frozen design

This is a small illustrative, synthetic retrieval study, not a general superiority/accuracy claim.
Fourteen questions and exact ID sets were authored from the public fixture literals and documented
temporal/direction rules **before executing either arm**. They do not come from runtime predictions
or old frozen report outputs. Gold is committed separately before runner/results. Never rewrite it
to make an implementation pass. R13 explicitly evaluates capped returned scope, not whole-graph recall.
R12 is a missing-incident negative control; R14 is an unsupported-causality negative control.

Both arms receive exactly the same two public synthetic fixture files: all node fields and all
directed relationship triples/properties. Graph seed writes only a new temporary native store.
Flat indexing makes one document per entity with all its properties and its incoming/outgoing
triples. No edge facts are hidden. It uses deterministic BM25-like lexical ranking, ID components
and complete ID tokens, target label filter and fixed k=5 (candidate cap also bounds k). It does
not get gold cardinality, expected IDs, graph outputs or expanded multi-hop neighborhoods.
An exact incident-presence guard and unsupported-cause abstention are shared safety behavior.

The graph arm uses the existing unchanged native `investigate` service, then a small declared
typed selector for the requested operation (candidate, time class, change, evidence or comparison).
**Intent asymmetry:** the graph arm receives an authored structured operation; lexical ranking
receives question text, incident anchor, target label and caps. This measures structured graph
retrieval versus unjoined lexical record retrieval, not equal natural-language understanding or
all flat-data algorithms. A flat relational join engine could recover the same topology. Question
names can favor lexical matches to synthetic IDs; this too limits generalization.

Freeze BM25 constants (k1=1.2, b=0.75), stop words, singularization and tokenization in the runner
before execution. Do not tune them after seeing results. Report every question's predicted/gold
IDs, native matched edges, TP/FP/FN and null precision/recall for empty denominators. Show misses
and negative controls, not just wins. No “correct root cause” metric exists. No LLM is involved.

Measure one first read plus five repeated reads per question. Graph timing includes opening,
existing native investigation, typed selection and closing; lexical timing includes in-memory
ranking, excluding one-time indexing. Native proof rechecks/setup are outside timed retrieval.
Do not call first read machine-cold: seeding and caches have already run. No OS cache flush.
Report hardware, procedure, medians and descriptive nearest-rank p95; no preselected speed win.
Existing Sprint 02/03 gold/reports remain byte-identical. Generated study outputs belong only here.

## Actual execution and review

Freeze commit: 1c8d1fa. Gold hash:
53e089d433a5f9de6c00105aa7837e1d9ae29016750ef6802f4cc0fde095db81.
`run_study.py --output results.json --markdown RESULTS.md` produced the preserved first run.
After the disclosed evaluation-only selector repair, the same frozen questions and unchanged
lexical baseline produced results-selector-v1.1.json / RESULTS_SELECTOR_V1.1.md. Both outputs
are retained. Reproduce from repository root using project Python and **new** output paths:

```powershell
.\.venv\Scripts\python.exe evaluation/graph-vs-flat/run_study.py --output .verification/overnight/retrieval-new.json --markdown .verification/overnight/retrieval-new.md
```

See [ERRATA.md](ERRATA.md): one frozen question (R13) has an independently identified cap-order assumption
error. It is neither rewritten nor silently counted as a product defect. Thirteen valid questions
remain. Raw final counts including that invalid expectation are native 13/14 and lexical 2/14;
do not advertise those as general accuracy. Full ID sets, precision/recall, native edge matches,
first/warm timing summaries and null denominators are in the actual result JSON. Flat retrieval is
much faster on this small in-memory corpus; native retrieval enforces the declared relational
semantics. The baseline was not retuned after seeing results and no UI superiority panel was added.

Preserved artifacts: [first report](RESULTS.md), [first raw output](results.json),
[selector 1.1 report](RESULTS_SELECTOR_V1.1.md), [selector 1.1 raw output](results-selector-v1.1.json),
[frozen questions](questions.json) and [runner](run_study.py). Read the erratum alongside either report.
