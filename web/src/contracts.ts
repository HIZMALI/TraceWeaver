import { z } from "zod";

const id = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const claimId = z.string().regex(/^C-[a-f0-9]{24}$/);
export const temporal = z.enum([
  "BEFORE",
  "AT_ONSET",
  "AFTER",
  "OUTSIDE_WINDOW",
  "UNKNOWN",
]);
export const edgeTypes = [
  "AFFECTS",
  "DEPENDS_ON",
  "TARGETS",
  "INCLUDES_CHANGE",
  "HAS_EVIDENCE",
  "OBSERVED_ON",
  "RAISED_FOR",
] as const;
const edge = z.strictObject({
  type: z.enum(edgeTypes),
  source_id: id,
  target_id: id,
  traversal_direction: z.enum(["FORWARD", "REVERSE"]),
});
export const pathSchema = z
  .strictObject({
    node_ids: z.array(id).min(2).max(7),
    edges: z.array(edge).min(1).max(6),
  })
  .superRefine((p, ctx) => {
    if (p.node_ids.length !== p.edges.length + 1)
      ctx.addIssue({ code: "custom", message: "Invalid path length" });
    p.edges.forEach((e, i) => {
      const reverse = e.traversal_direction === "REVERSE";
      if (
        (reverse && e.type !== "TARGETS") ||
        e.source_id !== p.node_ids[reverse ? i + 1 : i] ||
        e.target_id !== p.node_ids[reverse ? i : i + 1]
      )
        ctx.addIssue({
          code: "custom",
          message: "Stored direction does not match path",
        });
    });
  });
const label = z.strictObject({
  text: z.string().max(160),
  status: z.enum(["RETURNED_TEXT", "WITHHELD", "SHORTENED"]),
});
const time = z.strictObject({
  utc: z.string().max(40).nullable(),
  original: z.string().max(96).nullable(),
  warning_code: z.string().max(64).nullable(),
  original_withheld: z.boolean(),
});
const finding = z.strictObject({
  code: z.string().max(64),
  count: z.number().int().nonnegative(),
  entity_ids: z.array(id).max(20),
  references_omitted: z.boolean(),
});
export const optionsSchema = z.strictObject({
  pre_minutes: z.number().int().min(0).max(1440),
  post_minutes: z.number().int().min(0).max(1440),
  max_candidates: z.number().int().min(1).max(100),
  max_evidence: z.number().int().min(1).max(100),
});
const provenance = z.enum(["TRACEABLE", "INCOMPLETE", "INVALID"]);
const verification = z.enum([
  "SYNTHETIC",
  "UNVERIFIED_EXTERNAL",
  "NOT_AVAILABLE",
]);
const status = z.enum([
  "READY_FOR_REVIEW",
  "PARTIAL_CONTEXT",
  "INSUFFICIENT_EVIDENCE",
]);
const truncation = z
  .record(z.string().max(32), z.boolean())
  .refine((v) => Object.keys(v).length <= 8);
const change = z.strictObject({
  change_id: id,
  name: label,
  graph_path: pathSchema,
});
export const candidateSchema = z.strictObject({
  deployment_id: id,
  target_service_id: id,
  name: label,
  dependency_depth: z.number().int().min(0).max(3),
  temporal_classification: temporal,
  candidate_assessment: z.enum([
    "INVESTIGATE",
    "INSUFFICIENT_DATA",
    "TEMPORALLY_EXCLUDED",
  ]),
  deployment_occurred_at: time,
  graph_paths: z.array(pathSchema).max(100),
  changes: z.array(change).max(100),
});
const evidence = z.strictObject({
  evidence_id: id,
  is_demo: z.boolean().nullable(),
  evidence_observed_at: time,
  temporal_classification: temporal,
  observed_service_ids: z.array(id).max(100),
  graph_paths: z.array(pathSchema).max(100),
  provenance_status: provenance,
  verification_status: verification,
  warnings: z.array(finding).max(100),
  source_reference: z.enum(["WITHHELD", "NOT_AVAILABLE"]),
});
const comparison = z.strictObject({
  evidence_ids: z.array(id).length(2),
  service_id: id,
  signal_key: label,
  environment: label,
  overlap_window: z.strictObject({
    start: z.string().max(40),
    end: z.string().max(40),
  }),
  observed_states: z.array(z.enum(["HEALTHY", "FAILED", "DEGRADED"])).length(2),
  classification: z.enum(["CONFLICTING_OBSERVATIONS", "UNDETERMINED"]),
});
const event = z.strictObject({
  kind: z.enum(["INCIDENT", "DEPLOYMENT", "EVIDENCE"]),
  entity_id: id,
  target_service_id: id.nullable(),
  timestamp: time,
  temporal_classification: temporal,
});
const investigation = z.strictObject({
  incident_id: id,
  is_demo: z.boolean().nullable(),
  title: label,
  severity: label,
  status: label,
  incident_time: time,
  options: optionsSchema,
  investigation_status: status,
  causal_conclusion: z.literal("NOT_ESTABLISHED"),
  entity_kinds: z
    .record(
      id,
      z.enum(["Incident", "Service", "Deployment", "Change", "Evidence"]),
    )
    .refine((v) => Object.keys(v).length <= 1000),
  affected_services: z.array(z.strictObject({ id, name: label })).max(100),
  candidates: z.array(candidateSchema).max(100),
  evidence: z.array(evidence).max(100),
  contradictions: z.array(comparison).max(100),
  timeline: z.array(event).max(100),
  evidence_gaps: z.array(finding).max(100),
  truncation,
  results_may_be_truncated: z.boolean(),
});
const citation = z.strictObject({
  kind: z.enum([
    "EVIDENCE",
    "GRAPH_PATH",
    "TEMPORAL",
    "CONTRADICTION",
    "GAP",
    "PROVENANCE",
    "INCIDENT",
  ]),
  entity_ids: z.array(id).min(1).max(12),
  graph_path: pathSchema.nullable(),
  event_utc: z.string().max(40).nullable(),
  temporal_classification: temporal.nullable(),
  provenance_status: provenance.nullable(),
  verification_status: verification.nullable(),
  source_ref: z.null(),
  source_ref_withheld: z.boolean(),
  classification: z
    .enum(["CONFLICTING_OBSERVATIONS", "UNDETERMINED"])
    .nullable(),
  overlap_start: z.string().max(40).nullable(),
  overlap_end: z.string().max(40).nullable(),
  code: z.string().max(64).nullable(),
  count: z.number().int().nonnegative().nullable(),
});
const claim = z.strictObject({
  claim_id: claimId,
  claim_type: z.enum([
    "INCIDENT_OBSERVED",
    "SERVICE_AFFECTED",
    "DEPLOYMENT_CONNECTED",
    "DEPLOYMENT_BEFORE_ONSET",
    "DEPLOYMENT_NOT_PRECEDING",
    "EVIDENCE_REPORTED",
    "STRUCTURED_CONFLICT",
    "COMPARISON_UNDETERMINED",
    "SOURCE_UNVERIFIED",
    "CONTEXT_GAP",
    "NO_CAUSAL_VERDICT",
  ]),
  statement: z.string().max(1024),
  referenced_entity_ids: z.array(id).min(1).max(12),
  citations: z.array(citation).min(1).max(12),
  support_status: z.literal("SUPPORTED_BY_RETURNED_CONTEXT"),
});
const summary = z.strictObject({
  scope: z.literal("RETURNED_EVIDENCE"),
  returned_candidates: z.number().int().nonnegative(),
  returned_evidence: z.number().int().nonnegative(),
  traceable_count: z.number().int().nonnegative(),
  incomplete_count: z.number().int().nonnegative(),
  invalid_count: z.number().int().nonnegative(),
  unverified_external_count: z.number().int().nonnegative(),
  not_evaluable_count: z.number().int().nonnegative(),
  conflict_count: z.number().int().nonnegative(),
  undetermined_count: z.number().int().nonnegative(),
});
export const explanationSchema = z.strictObject({
  contract_version: z.literal("1.0"),
  incident_id: id,
  is_demo: z.boolean().nullable(),
  mode_requested: z.enum(["DETERMINISTIC", "OLLAMA"]),
  mode_executed: z.enum(["DETERMINISTIC", "OLLAMA", "NONE"]),
  ai_generated_selection: z.boolean(),
  model: z
    .strictObject({
      provider: z.literal("OLLAMA_LOCAL"),
      model_id: z.string().max(128),
    })
    .nullable(),
  explanation_status: z.enum([
    "EXPLAINED",
    "PARTIAL_CONTEXT",
    "ABSTAINED",
    "MODEL_UNAVAILABLE",
    "MODEL_OUTPUT_REJECTED",
  ]),
  investigation_status: status,
  causal_conclusion: z.literal("NOT_ESTABLISHED"),
  investigation_fingerprint: digest,
  overview: z.string().max(2048),
  claims: z.array(claim).max(10),
  evidence_summary: summary,
  uncertainties: z
    .array(
      z.strictObject({
        code: z.string().max(64),
        entity_ids: z.array(id).max(12),
        count: z.number().int().nonnegative(),
        references_omitted: z.boolean(),
      }),
    )
    .max(20),
  next_checks: z.array(z.string().max(512)).max(8),
  limitations: z.array(z.string().max(512)).max(12),
  truncation: z.strictObject({
    investigation: truncation,
    catalog: z.boolean(),
    selected_subset: z.boolean(),
    uncertainties: z.boolean(),
    next_checks: z.boolean(),
    model_offer: z.boolean(),
  }),
  demo_notice: z.string().max(256),
  catalog_claim_count: z.number().int().min(1).max(128),
  generated_claim_count: z.number().int().min(1),
  validated_claim_count: z.number().int().max(10),
  validated_citation_count: z.number().int().max(120),
  rejection_codes: z.array(z.string().max(64)).max(8),
  external_verification_status: z.literal("NOT_PERFORMED"),
});
export const bundleSchema = z.strictObject({
  contract_version: z.literal("1.0"),
  source_fingerprint: digest,
  view_fingerprint: digest,
  read_only: z.literal(true),
  investigation,
  explanation: explanationSchema,
});
export const incidentListSchema = z.strictObject({
  contract_version: z.literal("1.0"),
  incidents: z
    .array(
      z.strictObject({
        id,
        title: z.string().max(160),
        severity: z.string().max(160),
        status: z.string().max(160),
        metadata_withheld: z.boolean(),
      }),
    )
    .max(100),
  results_may_be_truncated: z.boolean(),
  unsafe_identifiers_omitted: z.number().int().min(0).max(100),
});
export type Bundle = z.infer<typeof bundleSchema>;
export type Path = z.infer<typeof pathSchema>;
export type Candidate = z.infer<typeof candidateSchema>;
export type Explanation = z.infer<typeof explanationSchema>;
export type Claim = Explanation["claims"][number];
export type Time = z.infer<typeof time>;
export type Options = z.infer<typeof optionsSchema>;
export type Incident = z.infer<typeof incidentListSchema>["incidents"][number];

export function canonical(value: unknown): string {
  function sorted(v: unknown): unknown {
    if (Array.isArray(v)) return v.map(sorted);
    if (v && typeof v === "object")
      return Object.fromEntries(
        Object.entries(v)
          .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
          .map(([k, x]) => [k, sorted(x)]),
      );
    return v;
  }
  return (
    JSON.stringify(sorted(value), null, 2).replace(
      /[\u007f-\uffff]/g,
      (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"),
    ) + "\n"
  );
}

export function allPaths(b: Bundle): Path[] {
  const i = b.investigation;
  return [
    ...i.candidates.flatMap((c) => [
      ...c.graph_paths,
      ...c.changes.map((x) => x.graph_path),
    ]),
    ...i.evidence.flatMap((e) => e.graph_paths),
  ];
}
export const pathKey = (p: Path) => canonical(p);

export function validateScope(b: Bundle): void {
  const i = b.investigation,
    e = b.explanation;
  if (
    b.source_fingerprint !== e.investigation_fingerprint ||
    i.incident_id !== e.incident_id ||
    i.is_demo !== e.is_demo ||
    e.evidence_summary.returned_evidence !== i.evidence.length ||
    e.evidence_summary.returned_candidates !== i.candidates.length
  )
    throw new Error("Context changed / cannot verify shared snapshot");
  const permitted = new Set(allPaths(b).map(pathKey));
  i.affected_services.forEach((s) =>
    permitted.add(
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
  i.candidates.forEach((c) =>
    c.graph_paths.forEach((p) => {
      if (
        p.node_ids[0] !== i.incident_id ||
        p.node_ids.at(-1) !== c.deployment_id ||
        p.node_ids.at(-2) !== c.target_service_id ||
        p.edges.at(-1)?.type !== "TARGETS" ||
        p.edges.at(-1)?.traversal_direction !== "REVERSE"
      )
        throw new Error("Invalid candidate scope");
    }),
  );
  i.evidence.forEach((e) =>
    e.graph_paths.forEach((p) => {
      if (
        p.node_ids[0] !== i.incident_id ||
        p.node_ids[1] !== e.evidence_id ||
        p.edges[0].type !== "HAS_EVIDENCE"
      )
        throw new Error("Invalid evidence scope");
    }),
  );
  e.claims.forEach((c) =>
    c.citations.forEach((x) => {
      if (x.graph_path && !permitted.has(pathKey(x.graph_path)))
        throw new Error("Citation path not in returned snapshot");
      if (x.kind === "TEMPORAL") {
        const candidate = i.candidates.find(
          (v) =>
            v.deployment_id === x.entity_ids[0] &&
            v.target_service_id === x.entity_ids[1],
        );
        if (
          !candidate ||
          candidate.deployment_occurred_at.utc !== x.event_utc ||
          candidate.temporal_classification !== x.temporal_classification
        )
          throw new Error("Citation time not in returned snapshot");
      }
      if (
        x.kind === "INCIDENT" &&
        (x.entity_ids[0] !== i.incident_id ||
          x.event_utc !== i.incident_time.utc)
      )
        throw new Error("Citation incident not in returned snapshot");
      if (x.kind === "EVIDENCE" || x.kind === "PROVENANCE") {
        const evidence = i.evidence.find(
          (v) => v.evidence_id === x.entity_ids[0],
        );
        if (
          !evidence ||
          (x.kind === "PROVENANCE" &&
            (x.provenance_status !== evidence.provenance_status ||
              x.verification_status !== evidence.verification_status))
        )
          throw new Error("Citation provenance not in returned snapshot");
      }
      if (
        x.kind === "CONTRADICTION" &&
        !i.contradictions.some(
          (v) =>
            canonical(v.evidence_ids) === canonical(x.entity_ids.slice(0, 2)) &&
            v.service_id === x.entity_ids[2] &&
            v.classification === x.classification &&
            v.overlap_window.start === x.overlap_start &&
            v.overlap_window.end === x.overlap_end,
        )
      )
        throw new Error("Citation comparison not in returned snapshot");
    }),
  );
  if (
    e.claims.at(-1)?.claim_type !== "NO_CAUSAL_VERDICT" ||
    e.ai_generated_selection ||
    e.mode_executed !== "DETERMINISTIC"
  )
    throw new Error("Unexpected deterministic report");
}

export async function verifyBundle(value: unknown): Promise<Bundle> {
  const b = bundleSchema.parse(value);
  validateScope(b);
  const bytes = new TextEncoder().encode(
    canonical({
      investigation: b.investigation,
      explanation: b.explanation,
      source_fingerprint: b.source_fingerprint,
    }),
  );
  const hash = Array.from(
    new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    (v) => v.toString(16).padStart(2, "0"),
  ).join("");
  if (hash !== b.view_fingerprint)
    throw new Error("Context changed / cannot verify shared snapshot");
  return b;
}
