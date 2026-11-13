import { z } from "zod";
import {
  allPaths,
  canonical,
  explanationSchema,
  optionsSchema,
  pathKey,
  pathSchema,
  temporal,
  validateScope,
  type Bundle,
} from "./contracts";

const id = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const code = z.string().regex(/^[A-Z_]{1,64}$/);
const number = (max: number) => z.number().int().min(0).max(max);
export const intents = [
  "CHECK_COMPETING_DEPLOYMENTS",
  "TRACE_DEPENDENCY_PATH",
  "RECONCILE_OBSERVATIONS",
  "FIND_EVIDENCE_GAPS",
] as const;
export const stepSchema = z.strictObject({
  step_number: z.number().int().min(1).max(4),
  tool_name: z.enum([
    "get_incident_scope",
    "trace_deployment",
    "inspect_evidence",
    "compare_observations",
    "inspect_gaps",
  ]),
  parameters: z.strictObject({ subject: z.string().regex(/^[IDEP][0-9]{3}$/) }),
  subject_ids: z.array(id).min(1).max(2),
  selected_by: z.enum(["DETERMINISTIC_PLAN", "LOCAL_MODEL"]),
  native_query_count: z.number().int().min(1).max(8),
  deferred_proposal_count: number(3),
  result: z.strictObject({
    status: z.enum([
      "RETURNED_CONTEXT",
      "PARTIAL_CONTEXT",
      "INSUFFICIENT_EVIDENCE",
    ]),
    entity_ids: z.array(id).max(64),
    graph_paths: z.array(pathSchema).max(8),
    records: z
      .array(
        z.strictObject({
          entity_id: id,
          timestamp: z.strictObject({
            utc: z.string().max(40).nullable(),
            original: z.string().max(96).nullable(),
            warning_code: z.string().max(64).nullable(),
            original_withheld: z.boolean(),
          }),
          temporal_classification: temporal,
          provenance_status: z
            .enum(["TRACEABLE", "INCOMPLETE", "INVALID"])
            .nullable(),
          verification_status: z
            .enum(["SYNTHETIC", "UNVERIFIED_EXTERNAL", "NOT_AVAILABLE"])
            .nullable(),
        }),
      )
      .max(8),
    comparisons: z
      .array(
        z.strictObject({
          evidence_ids: z.array(id).length(2),
          service_id: id,
          signal_key: z.strictObject({
            text: z.string().max(160),
            status: z.enum(["RETURNED_TEXT", "WITHHELD", "SHORTENED"]),
          }),
          environment: z.strictObject({
            text: z.string().max(160),
            status: z.enum(["RETURNED_TEXT", "WITHHELD", "SHORTENED"]),
          }),
          observed_states: z.array(z.string().max(160)).length(2),
          classification: z.enum(["CONFLICTING_OBSERVATIONS", "UNDETERMINED"]),
          overlap_window: z.strictObject({
            start: z.string().max(40),
            end: z.string().max(40),
          }),
        }),
      )
      .max(1),
    gap_codes: z.array(code).max(20),
    truncated: z.boolean(),
  }),
  elapsed_ms: z.number().min(0).max(1e9),
});
export const agentSchema = z.strictObject({
  contract_version: z.literal("1.0"),
  incident_id: id,
  source_fingerprint: digest,
  database_digest: digest,
  options: optionsSchema,
  intent: z.enum(intents),
  mode_executed: z.enum(["DETERMINISTIC_TOOL_REHEARSAL", "OLLAMA", "NONE"]),
  model_requested: z.string().max(128).nullable(),
  model_executed: z.string().max(128).nullable(),
  agent_status: z.enum([
    "COMPLETED",
    "PARTIAL_CONTEXT",
    "ABSTAINED",
    "MODEL_SELECTION_ONLY",
    "MODEL_UNAVAILABLE",
    "MODEL_OUTPUT_REJECTED",
    "STALE_SNAPSHOT",
    "BUDGET_EXHAUSTED",
  ]),
  ai_directed_tools: z.boolean(),
  ai_generated_selection: z.boolean(),
  tool_trace: z.array(stepSchema).max(4),
  validated_claims: explanationSchema.shape.claims,
  validated_citation_count: number(120),
  rejection_codes: z.array(code).max(8),
  proposal_warnings: z.array(code).max(4),
  gap_codes: z.array(code).max(20),
  source_truncated: z.boolean(),
  model_subjects_truncated: z.boolean(),
  model_interactions: number(5),
  native_query_count: number(40),
  elapsed_ms: z.number().min(0).max(1e9),
  synthetic_notice: z.string().max(256),
  causal_conclusion: z.literal("NOT_ESTABLISHED"),
  external_verification_status: z.literal("NOT_PERFORMED"),
  no_cause_statement: z.literal(
    "Causal conclusion is NOT_ESTABLISHED. Connected deployments are investigation candidates.",
  ),
  canonical_fingerprint: digest,
});
export type AgentReport = z.infer<typeof agentSchema>;
export type AgentStep = z.infer<typeof stepSchema>;
export function canonicalAgent(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalAgent);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value)
        .filter(([k]) => !["elapsed_ms", "canonical_fingerprint"].includes(k))
        .map(([k, v]) => [k, canonicalAgent(v)]),
    );
  return value;
}
export async function verifyAgent(
  raw: unknown,
  b: Bundle,
): Promise<AgentReport> {
  const r = agentSchema.parse(raw),
    i = b.investigation;
  if (
    r.incident_id !== i.incident_id ||
    r.source_fingerprint !== b.source_fingerprint ||
    canonical(r.options) !== canonical(i.options) ||
    r.source_truncated !== i.results_may_be_truncated
  )
    throw new Error("Agent snapshot mismatch");
  const directed = r.tool_trace.some((s) => s.selected_by === "LOCAL_MODEL");
  const offline = r.mode_executed === "DETERMINISTIC_TOOL_REHEARSAL";
  if (
    r.ai_directed_tools !== directed ||
    (offline &&
      (directed ||
        r.ai_generated_selection ||
        r.model_requested ||
        r.model_executed ||
        r.model_interactions)) ||
    (r.ai_generated_selection && (!directed || !r.validated_claims.length)) ||
    (!["COMPLETED", "PARTIAL_CONTEXT", "ABSTAINED"].includes(r.agent_status) &&
      r.validated_claims.length) ||
    r.validated_citation_count !==
      r.validated_claims.reduce((n, c) => n + c.citations.length, 0) ||
    (r.validated_claims.length &&
      r.validated_claims.at(-1)?.claim_type !== "NO_CAUSAL_VERDICT")
  )
    throw new Error("Agent activity metadata mismatch");
  const paths = new Set(allPaths(b).map(pathKey));
  i.affected_services.forEach((s) =>
    paths.add(
      pathKey({
        node_ids: [i.incident_id, s.id],
        edges: [
          {
            type: "AFFECTS",
            source_id: i.incident_id,
            target_id: s.id,
            traversal_direction: "FORWARD",
          },
        ],
      }),
    ),
  );
  const ids = new Set(Object.keys(i.entity_kinds));
  r.tool_trace.forEach((s, n) => {
    if (
      s.step_number !== n + 1 ||
      s.subject_ids.some((id) => !ids.has(id)) ||
      new Set(s.result.entity_ids).size !== s.result.entity_ids.length ||
      s.result.entity_ids.some((id) => !ids.has(id)) ||
      s.result.graph_paths.some((p) => !paths.has(pathKey(p)))
    )
      throw new Error("Agent native proof outside snapshot");
    s.result.records.forEach((v) => {
      const evidence = i.evidence.find((e) => e.evidence_id === v.entity_id);
      const deployment = i.candidates.find(
        (c) => c.deployment_id === v.entity_id,
      );
      const timestamp =
        evidence?.evidence_observed_at ??
        deployment?.deployment_occurred_at ??
        (v.entity_id === i.incident_id ? i.incident_time : null);
      if (
        !timestamp ||
        canonical(timestamp) !== canonical(v.timestamp) ||
        !s.result.entity_ids.includes(v.entity_id) ||
        (evidence &&
          (v.provenance_status !== evidence.provenance_status ||
            v.verification_status !== evidence.verification_status ||
            v.temporal_classification !== evidence.temporal_classification)) ||
        (deployment &&
          v.temporal_classification !== deployment.temporal_classification)
      )
        throw new Error("Agent record mismatch");
    });
    s.result.comparisons.forEach((p) => {
      if (!i.contradictions.some((c) => canonical(c) === canonical(p)))
        throw new Error("Agent comparison mismatch");
    });
  });
  validateScope(
    {
      ...b,
      explanation: {
        ...b.explanation,
        claims: r.validated_claims,
        mode_executed: r.validated_claims.length ? "DETERMINISTIC" : "NONE",
      },
    },
    false,
  );
  const bytes = new TextEncoder().encode(canonical(canonicalAgent(r)));
  const hash = Array.from(
    new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    (n) => n.toString(16).padStart(2, "0"),
  ).join("");
  if (hash !== r.canonical_fingerprint)
    throw new Error("Agent canonical fingerprint mismatch");
  return r;
}
