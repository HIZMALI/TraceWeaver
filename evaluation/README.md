# Frozen synthetic evaluations

All three suites use isolated, real Relate stores and explicit frozen expectations. They measure
consistency with authored synthetic cases, not production accuracy, source truth or model quality.
They never use the existing user/judge database as scratch space.

| Suite | Cases | Scope |
| --- | ---: | --- |
| [Graph](cases.json) | 20 | Paths/directions, incident evidence scope, UTC windows, comparisons and truncation |
| [Explanations](explanation_cases.json) | 19 | Semantic citation support, controlled rendering, abstention and adversarial selections |
| [Agent](sprint06_agent_cases.json) | 35 | 18 native cases and 17 explicitly controlled provider-protocol cases |

## Reproduce

Install the source project's development dependencies first. From the repository root, use **new**
output paths. On Windows/PowerShell:

```powershell
New-Item -ItemType Directory -Path .verification/evaluation -Force | Out-Null
.\.venv\Scripts\python.exe -m traceweaver evaluate --suite evaluation/cases.json --output .verification/evaluation/graph.json
.\.venv\Scripts\python.exe -m traceweaver evaluate-explanations --suite evaluation/explanation_cases.json --output .verification/evaluation/explanations.json
.\.venv\Scripts\python.exe -m traceweaver.agent_evaluation --suite evaluation/sprint06_agent_cases.json --output .verification/evaluation/agent.json
```

On Linux create the output directory with mkdir -p and use .venv/bin/python. Existing reports
require explicit --overwrite; do not overwrite frozen inputs or committed reports.
Expected-result failures return nonzero: graph 11, explanations 14, agent 15. Graph/explanation
commands also write Markdown details. No model, key or network source fetch is required.
Controlled transports in the agent suite are not evidence of a live Ollama invocation.

The retained [graph JSON](../reports/sprint02-evaluation.json) and
[Markdown report](../reports/sprint02-evaluation.md) record 20/20. The retained
[explanation JSON](../reports/sprint03-explanation-evaluation.json) and
[Markdown report](../reports/sprint03-explanation-evaluation.md) record 19/19.
They are actual historical outputs, not regenerated to match code.

## Method and corrections

[Evaluation method](../docs/EVALUATION_METHOD.md) defines denominators, nulls for empty sets,
truncated-case exclusions, repeatability and native edge audits. The
[explanation gold review](EXPLANATION_GOLD_REVIEW.md) discloses its original label correction.
The [agent contract](../docs/AGENT_TOOL_CONTRACT.md) defines finite native tool execution and final
claim admission; the agent suite's companion [digest](sprint06_agent_cases.sha256) freezes its bytes.

The separate illustrative [graph-versus-flat study](graph-vs-flat/README.md) retains its original
questions, runner, both raw result generations and [erratum](graph-vs-flat/ERRATA.md). One invalid
gold assumption remains visible. Structured-intent asymmetry and lexical latency prevent a
universal graph superiority claim.

## Negative controls

Regression tests corrupt **separate copies** of gold and require failed reports/nonzero exits:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_evaluation.py tests/explanations/test_explanation_evaluation.py tests/agent/test_agent_evaluation.py
```

Never edit a frozen suite to make implementation output pass. Causal conclusion remains
NOT_ESTABLISHED; external verification remains NOT_PERFORMED.
