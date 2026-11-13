# Local release readiness

The judge console is a single-user loopback application, with deterministic offline behavior by
default. Real Relate 1.0.0 remains the only data engine. Original 337 cases, old API contracts,
user store, judge binary/manifest and frozen Sprint 02/03 artifacts are preserved.

## Reproduced distribution gate

- Clean copied frontend outside checkout: `npm ci` (194 packages, audit zero vulnerabilities),
  `npm run build` with the committed lock. Built asset bytes matched checkout build byte-for-byte.
- `.venv/Scripts/python -m pip wheel . --no-deps --wheel-dir .verification/overnight/wheels`.
  Actual wheel SHA-256 `c0ee1ff20d91d53935403e5735227b8ef6fe762e14a1c4b722e648da214ec46c`.
- Fresh Python 3.14 virtual environment outside repository, non-editable install with existing
  requirements-dev.lock as constraints. No PYTHONPATH dependency or checkout imports. pip check clean.
- Wheel contains index, JS/CSS, upstream notices and fixtures. It contains no user database.
- Copied intact published bundle verified natively, 51 nodes / 67 edges; native INC-001 2/4,
  CASE-INC 6/11. Server process PATH deliberately omitted Node. HTTP index/assets/health worked.
- Actual Chromium 158.0.8127.18 rendered the installed wheel: 14 native edges, NOT_ESTABLISHED,
  zero page errors. Owned server stopped; copied graph bytes remained identical.
- The built console includes 555.43 kB JS (172.15 kB gzip) and 37.41 kB CSS (7.92 kB gzip).
  Client-only dependency directive warnings remain in Vite output; no SSR compatibility claim.

The local wheel is an ignored verification artifact, not a published release. Rebuilding the wheel
may change ZIP timestamps/hash; re-run distribution verification after runtime source changes.
See README for source setup and `scripts/start-judge-demo.ps1 -Build`. Subsequent launches need
neither Node nor Ollama. `scripts/check-judge-demo.ps1` verifies source/manifest/logical graph,
assets and representative native snapshots without writes. Supply the existing bundle when running
`python -m traceweaver.judge --bundle <directory>` from a wheel.

## Explicit limitations

Only local Windows/Python 3.14 and Chromium were exercised. Python 3.11, Linux, macOS, Firefox,
Safari and remote CI are UNVERIFIED. No deployment/public listener, source URL fetch, upload,
production incident integration or remediation exists. Model selection is optional, explicit and
bounded; one real qwen3:8b UI selection is runtime evidence, not an accuracy benchmark.
Client cancellation does not guarantee daemon cancellation. One server worker is supported.

Graphs are partial returned context. Source caps and 300-node/600-edge display caps are explicit;
native row limits do not bound full-store RAM/work. Dense full-context edge labels can overlap;
selection focus and keyboard-accessible exact path lists provide readable proof. Digests and
TRACEABLE metadata do not establish truth. Conclusions remain NOT_ESTABLISHED.

Presentation artifacts and final regression/performance evidence are recorded in the overnight
mission report. No finished submission video, Devpost submission or remote push is claimed.
Before public submission: owner chooses project license, records and reviews a genuine video,
checks competition terms and verifies another platform. See dependency notices for bundled OSS.
