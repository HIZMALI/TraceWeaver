# Local browser measurements

Actual command: `node web/e2e/performance.mjs`. Chromium 158.0.8127.18, Node 24.13.1,
Windows 11 build 26200, Intel i9-11900K 3.50GHz; OS reported 34,220,597,248 memory bytes.
No CPU/GPU throttling or OS page-cache flush was performed. This is descriptive local evidence,
not a production benchmark, capacity promise or claim about another machine.

The runner allocates three fresh OS-temporary native Relate stores and transactionally writes
4, 30 or 110 synthetic deployment/change/evidence triples. All values are parameterized, all
records/demo edges explicitly synthetic. It uses the actual dashboard, citation firewall and
built React Flow UI, not JSON responses supplied by a test. It verifies every expected rendered
node/edge count. Each scale owns/stops one numeric-loopback server. No existing store is written.

| Scale | Stored nodes / edges | Returned candidate pairs / evidence | Rendered nodes / edges | First-context load ms | Warm load median / p95 ms | Proof selection median / p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| Small | 14 / 17 | 4 / 4 | 14 / 17 | 330.39 | 116.22 / 132.77 | 83.82 / 116.47 |
| Medium | 92 / 121 | 30 / 30 | 92 / 121 | 460.35 | 239.98 / 267.19 | 145.97 / 149.30 |
| Capped | 332 / 441 | 100 / 100 | 300 / 399 | 879.77 | 689.55 / 845.86 | 303.87 / 376.68 |

One fresh browser context per scale; first-context load is one observation, not a distribution
or machine-cold load. Six further navigations use that same context. Seven candidate-selection
samples per scale include Playwright polling/scrolling and two animation frames. p95 uses
nearest rank; at n=6 or 7 it is the maximum sample and has no statistical confidence claim.
Browser network timing for dashboard requests (n=7) was median/p95 13.82/18.41, 40.00/44.40 and
108.50/187.85ms respectively. These include transport/response handling; they are not pure
Cypher-engine timings. Concurrent desktop work and native query warmup can affect results.

Owned server **process-tree** working-set snapshots after measurements were 83,574,784,
86,233,088 and 91,402,240 bytes. They include the Windows virtualenv launcher and interpreter;
shared pages may be counted twice. These are neither peak RAM nor isolated native-engine memory.
An initial diagnostic sampled only the 4MB virtualenv shim, so it was rejected; the runner was
corrected to enumerate owned descendants and the full finite measurement was rerun. Only the
corrected run appears above. No artificial sleep was used beyond bounded server readiness.

The capped scale really reaches source limits and omits two nodes from the returned display.
The browser discloses source/display caps. The graph cap does not bound native whole-store work
or RAM. Large data, pathological degree and external writers remain unmeasured. Full-context
edge labels can overlap; focus a selected path or use the exact accessible path list.

Production JS is 555.43kB (172.15kB gzip), CSS 37.41kB (7.92kB gzip) in the measured build.
Vite emits client-only dependency directive warnings. The separate graph-vs-flat study measures
retrieval tasks, not browser render performance or model accuracy.
