# TraceWeaver — submission draft (not submitted)

**One-line pitch:** Follow incident context through a real embedded graph, then inspect the exact
citations behind every admitted explanation while uncertainty stays visible.

## Inspiration and use case

An incident response starts with partial evidence: affected services, dependencies, recent changes
and conflicting observations. TraceWeaver provides a read-only investigation workspace where a
reviewer can follow those connections and identify useful next checks. Its examples are explicitly
synthetic; it does not claim to diagnose production root causes.

## What we built

A local React/TypeScript console with a directed graph, candidate/evidence ledger, UTC timeline,
structured comparison view, gaps and typed citation inspector. A coherent native graph snapshot
binds the explanation and displayed proof. Unsupported, stale or cross-snapshot paths are rejected.
Mobile views and keyboard-accessible path lists preserve exact relationships without relying on
graph color or tiny edge labels. The default explanation is deterministic and offline, not AI-generated.

## Why Relate is essential

Embedded relate-db 1.0.0 owns the persistent .rl graph. Parameterized native Cypher finds actual
incident-to-service dependency paths, candidate deployments, included changes and scoped evidence.
The browser derives a partial subgraph from those returned paths, preserving stored arrow direction
separately from traversal direction. It is not a browser fixture, mock graph or replacement database.
The published synthetic judge file contains 51 nodes and 67 directed relationships.

## Architecture and implementation

FastAPI runs on 127.0.0.1 with a single static/API origin. Each synchronous native read opens,
queries and closes on one worker thread. A strict privacy projection withholds source prose and
references. The existing semantic citation firewall admits claim IDs, exact paths, timestamps and
comparison classes; deterministic templates render statements. Snapshot digests detect inconsistent
content, without claiming source truth. Both source caps and display caps remain explicit.

Optional Ollama selection is a separately confirmed local action. Only an existing model at fixed
127.0.0.1:11434 receives opaque claim IDs and bounded metadata. No raw entity IDs, logs, references,
private paths, prompts supplied by users, tools or Cypher enter the provider packet. A model proposal
cannot author facts or citations; invalid selections are rejected without a hidden fallback.

## Verified evidence

The local release gate preserved all 337 original cases; expanded Python tests, frontend unit tests,
real Chromium scenarios and native graph/citation checks are recorded in the overnight mission
report. Genuine captures are in docs/screenshots. A fresh non-editable wheel outside the checkout
served the actual console without Node on the server PATH. One genuine qwen3:8b UI selection
accepted seven claims and seventeen citations in 4.25 seconds. That is runtime evidence only.
Controlled performance measurements cover three new synthetic native stores, with sample counts,
hardware and limitations disclosed. There is no fabricated production or LLM accuracy number.

## Demo setup

Follow README prerequisites, then `scripts/start-judge-demo.ps1 -Build`. The existing judge bundle
is verified and read without reseeding. Open INC-001, follow Payment → Auth ← Deployment → Change,
inspect a typed claim, then show CASE-INC's one conflict and two undetermined pairs. End with
gaps/next checks and NOT_ESTABLISHED. No API key, paid service, Docker, hosted database or model
installation is required. See JUDGE_DEMO_GUIDE.md for the timed live storyboard.

## Challenges, limits and next steps

Graph connectivity and temporal precedence are candidates for investigation, never a proven cause.
TRACEABLE metadata is separate from external truth verification (NOT_PERFORMED). Dense full-context
graphs can overlap labels; focused paths and accessible lists offer exact proof. Row caps do not
bound all native work or RAM. Browser cancellation may leave bounded daemon work running.
Windows/Python 3.14/Chromium were tested; remote CI and other platforms remain unverified.
Next: owner-selected project license, genuine reviewed video, broader platform verification and
competition-rule review before any public submission. No video or account submission is claimed.

## AI-use and OSS disclosure

Development used Codex assistance. Runtime deterministic output is explicitly labelled not
AI-generated; optional local AI selects existing claim IDs only. UI/styles are original project
work; React, React Flow, Zod, Lucide and their transitive notices accompany the build. Relate and
Python dependencies retain their upstream licenses. See DEPENDENCY_LICENSES.md. This document
is an English submission draft; nothing has been uploaded, pushed, published or submitted.
