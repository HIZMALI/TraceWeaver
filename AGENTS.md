# TraceWeaver development rules

- Work on the existing `main` branch unless the user explicitly requests another branch.
- Preserve all existing user changes when changing branches or checkouts.
- Complete every sprint with meaningful tests using the real Relate embedded engine.
- Keep Relate as the actual data engine; never substitute a fake graph repository.
- Never delete user data, reset a graph, or remove stores without explicit authorization.
- Keep seed commands idempotent and preserve unrelated and conflicting user records.
- Parameterize user values in Cypher. Only allowlisted schema identifiers may enter query text.
- Support critical findings with sources and actual relationship paths.
- Mark demo records explicitly and keep them distinct from real incidents.
- Never hide failed tests with skipped assertions, fake results, or unearned PASS claims.
- Never state conclusions more strongly than the evidence supports. Connected deployments are
  candidates for investigation, not proven causes.
- Leave large features outside the current sprint for later sprints.
- Write code names, comments, README, and technical documentation in English.
- Communicate with the user in Turkish.
- Run Ruff and pytest before finishing. Report remote CI as unverified unless it actually ran.
- Use project virtual environments. Keep local databases and secrets outside Git.
- Keep seed writes finite and transactional. API connections must be read-only and must open,
  execute, and close in the same worker thread; Relate connections are thread-affine.
- Do not add runtime dependencies on the Relate CLI, paid services, API keys, or Docker.
