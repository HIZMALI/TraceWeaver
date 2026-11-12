# Explanation gold review record

The 19 initial scenarios were explicitly authored before implementing/executing the explanation
runner. They were derived from reviewed published topology, existing temporal/provenance rules,
and the prior frozen graph suite, not generated from explanation outputs.

An initial pre-execution fixture review corrected DEP-001's timestamp to 09:55Z by reading the
original published fixture. Initial execution then reported 18/19: X19's authored expectation
incorrectly said PARTIAL_CONTEXT. Independent review of the pre-existing Sprint 02 E19 gold
shows READY_FOR_REVIEW, which maps to EXPLAINED under the documented explanation status policy.
EV-OPAQUE has complete structured demo metadata. An opaque URL is withheld and never fetched;
it does not itself invalidate that metadata or establish source authenticity.

Only that X19 status label was corrected to EXPLAINED. No citation IDs, graph facts, scenario,
assertion, source contract or production logic was removed or weakened to conceal the mismatch.
The first implementation-run gold digest was
636930125e11808f77ad1f47d2685eab64ff1147c6dae28af8892af70e41d710.
The reviewed gold is frozen for regression/evaluation, with its final digest in the sprint report.
The test suite deliberately corrupts a separate copied gold and requires a failing evaluation.
This disclosed label correction is not independent external adjudication or real-world accuracy.
