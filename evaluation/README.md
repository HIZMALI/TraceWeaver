# Frozen offline synthetic suite

The 20 cases in [cases.json](cases.json) are explicit gold labels authored before harness
execution. They cover real graph traversal, scope, event windows, provenance, structured states,
missing data and honest caps. Fixture profiles are curated packaged synthetic data, not arbitrary
filesystem paths or query scripts.

```powershell
python -m traceweaver evaluate --suite ./evaluation/cases.json --output ./reports/new-evaluation.json
```

Use a fresh output name. --overwrite explicitly replaces an existing report; it cannot alias
the input suite. Each case uses its own temporary real Relate .rl and the unchanged investigate
service. An expected-result failure writes JSON/Markdown details and exits 11. Labels are never
learned, regenerated, or updated from outputs.

The committed [JSON report](../reports/sprint02-evaluation.json) and
[Markdown report](../reports/sprint02-evaluation.md) are actual local outputs: 20/20 passed.
See [the evaluation method](../docs/EVALUATION_METHOD.md) for exact denominators, empty-case nulls,
truncated-case exclusions, determinism, and limitations. These are synthetic retrieval/path
metrics, not root-cause accuracy or source authentication. Remote runtime checks remain unverified.
