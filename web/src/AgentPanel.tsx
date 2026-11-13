import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { requestJSON } from "./api";
import {
  intents,
  verifyAgent,
  type AgentReport,
  type AgentStep,
} from "./agent-contracts";
import type { Bundle, Claim } from "./contracts";

const capabilities = z.strictObject({
  models: z.array(z.string().max(128)).max(32),
  truncated: z.boolean(),
  status: z.enum(["AVAILABLE", "UNAVAILABLE"]),
  code: z.string().max(64).nullable(),
});
const purpose = {
  get_incident_scope:
    "Check native incident membership and affected-service scope.",
  trace_deployment:
    "Inspect a connected candidate's stored dependency and reverse TARGETS path.",
  inspect_evidence:
    "Inspect returned UTC, provenance metadata and observed-service membership.",
  compare_observations:
    "Check a structured same-context observation pair, including unknowns.",
  inspect_gaps:
    "Re-read the bounded investigation and expose remaining missing context.",
};
export function AgentPanel({
  bundle,
  onStep,
  onClaim,
}: {
  bundle: Bundle;
  onStep: (s: AgentStep) => void;
  onClaim: (c: Claim) => void;
}) {
  const [open, setOpen] = useState(false),
    [intent, setIntent] = useState<(typeof intents)[number]>(
      "TRACE_DEPENDENCY_PATH",
    );
  const [models, setModels] = useState<string[] | null>(null),
    [model, setModel] = useState(""),
    [confirmed, setConfirmed] = useState(false),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [report, setReport] = useState<AgentReport | null>(null);
  const controller = useRef<AbortController | null>(null),
    mounted = useRef(true),
    inFlight = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      controller.current?.abort();
    };
  }, []);
  async function action(kind: "models" | "offline" | "model") {
    if (
      inFlight.current ||
      (kind === "model" && (!confirmed || !models?.includes(model)))
    )
      return;
    const current = new AbortController();
    controller.current = current;
    inFlight.current = true;
    setBusy(true);
    setNotice("");
    setReport(null);
    try {
      const raw = await requestJSON(
        kind === "models"
          ? "/console/models/capabilities"
          : kind === "offline"
            ? "/console/agent/rehearse"
            : "/console/agent/investigate",
        current.signal,
        kind === "models"
          ? { action: "LIST_INSTALLED_MODELS" }
          : {
              incident_id: bundle.investigation.incident_id,
              options: bundle.investigation.options,
              source_fingerprint: bundle.source_fingerprint,
              intent,
              confirmed: true,
              ...(kind === "model" ? { model_id: model } : {}),
            },
      );
      if (!mounted.current || current.signal.aborted) return;
      if (kind === "models") {
        const c = capabilities.parse(raw);
        setModels(c.models);
        setModel("");
        setConfirmed(false);
        setNotice(
          c.status === "UNAVAILABLE"
            ? `Local Ollama unavailable (${c.code}). Rehearsal remains available.`
            : c.models.length
              ? "Choose an installed model. No model is selected automatically."
              : "No eligible model installed. No download.",
        );
      } else {
        const r = await verifyAgent(raw, bundle);
        if (!mounted.current || current.signal.aborted) return;
        if (
          r.intent !== intent ||
          (kind === "offline"
            ? r.mode_executed !== "DETERMINISTIC_TOOL_REHEARSAL"
            : r.model_requested !== model ||
              (r.model_executed !== null && r.model_executed !== model))
        )
          throw new Error("Action mismatch");
        setReport(r);
        setNotice(
          kind === "offline"
            ? "Deterministic native tool rehearsal · Offline · Not AI-generated."
            : r.ai_generated_selection
              ? "Local-model tools and final claim IDs admitted. Cause and source truth remain unestablished."
              : `No accepted final AI selection: ${r.agent_status}. Executed native steps, if any, remain visible; no automatic fallback.`,
        );
      }
    } catch (e) {
      if (mounted.current && !current.signal.aborted)
        setNotice(
          e instanceof Error && e.name === "ApiError"
            ? e.message
            : "Action failed or snapshot cannot be verified. Refresh before trying again.",
        );
    } finally {
      inFlight.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <section
      className="agent-panel card"
      id="investigation-steps"
      aria-label="Investigation steps"
    >
      <h2>
        Investigation steps <span className="badge">Experimental</span>
      </h2>
      <button aria-expanded={open} onClick={() => setOpen(!open)}>
        Explore investigation steps
      </button>
      {open && (
        <>
          <p>
            Default: Deterministic · Offline · Not AI-generated. Rehearsal
            executes bounded read-only Relate tools. It is distinct from the
            explanation and from optional local claim selection.
          </p>
          <label>
            Investigation intent
            <select
              aria-label="Investigation intent"
              value={intent}
              disabled={busy}
              onChange={(e) => {
                setIntent(e.target.value as typeof intent);
                setReport(null);
              }}
            >
              {intents.map((i) => (
                <option key={i}>{i}</option>
              ))}
            </select>
          </label>
          <div className="agent-actions">
            <button
              disabled={busy}
              className="primary-button"
              onClick={() => void action("offline")}
            >
              Rehearse graph investigation
            </button>
            <button disabled={busy} onClick={() => void action("models")}>
              Agent investigation (local)
            </button>
          </div>
          {models && (
            <div className="local-controls">
              <label>
                Agent installed model
                <select
                  aria-label="Agent installed model"
                  value={model}
                  disabled={busy}
                  onChange={(e) => {
                    setModel(e.target.value);
                    setConfirmed(false);
                    setReport(null);
                  }}
                >
                  <option value="">Choose a model</option>
                  {models.map((m) => (
                    <option key={m}>{m}</option>
                  ))}
                </select>
              </label>
              <label className="confirmation">
                <input
                  type="checkbox"
                  checked={confirmed}
                  disabled={busy || !model}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                I confirm one local agent action for this snapshot. No download.
              </label>
              <button
                disabled={busy || !model || !confirmed}
                onClick={() => void action("model")}
              >
                Run confirmed local agent
              </button>
            </div>
          )}
          {busy && (
            <div role="status">
              <p>Bounded local action running. Native tools are read-only.</p>
              <button
                onClick={() => {
                  controller.current?.abort();
                  setNotice(
                    "Client wait cancelled. Server/provider work may continue to its finite deadline; duplicate work is blocked.",
                  );
                }}
              >
                Cancel agent wait
              </button>
            </div>
          )}
          {notice && (
            <p role="status" className="notice">
              {notice}
            </p>
          )}
          {report && (
            <div className="agent-report" data-testid="agent-report">
              <p>
                <strong>{report.mode_executed}</strong> · {report.agent_status}
              </p>
              <p>
                AI-directed tools: {String(report.ai_directed_tools)} ·
                AI-selected claims: {String(report.ai_generated_selection)}
              </p>
              <p>
                {report.tool_trace.length} executed tools ·{" "}
                {report.native_query_count} native queries ·{" "}
                {report.validated_claims.length} admitted claims /{" "}
                {report.validated_citation_count} citations
              </p>
              <p>{report.no_cause_statement} External truth: NOT_PERFORMED.</p>
              {(report.source_truncated || report.model_subjects_truncated) && (
                <p className="notice amber">
                  Bounded source/subject context; omitted records may change the
                  review.
                </p>
              )}
              {report.rejection_codes.length > 0 && (
                <p className="notice amber">
                  {report.rejection_codes.join(" · ")}
                </p>
              )}
              {report.proposal_warnings.length > 0 && (
                <p>{report.proposal_warnings.join(" · ")}</p>
              )}
              <ol className="agent-steps">
                {report.tool_trace.map((s) => (
                  <li key={s.step_number}>
                    <button
                      onClick={() => onStep(s)}
                      aria-label={`Inspect tool step ${s.step_number} ${s.tool_name}`}
                    >
                      <strong>
                        {s.step_number}. {s.tool_name}
                      </strong>
                      <span>{s.subject_ids.join(" · ")}</span>
                      <small>
                        {s.result.status} · {s.native_query_count} native
                        queries · {s.result.graph_paths.length} proof paths
                      </small>
                    </button>
                    <p className="tiny">
                      {s.step_number < report.tool_trace.length
                        ? `Next recorded check: ${purpose[report.tool_trace[s.step_number].tool_name]} This describes the tool's scope, not the model's private reasoning.`
                        : "Native checks ended. Review citations and remaining gaps; no causal verdict."}
                    </p>
                    <details>
                      <summary>
                        Structured native result for step {s.step_number}
                      </summary>
                      <pre>{JSON.stringify(s, null, 2)}</pre>
                    </details>
                  </li>
                ))}
              </ol>
              <details>
                <summary>
                  Admitted claim citations ({report.validated_claims.length})
                </summary>
                {report.validated_claims.map((c) => (
                  <button
                    className="agent-claim"
                    key={c.claim_id}
                    onClick={() => onClaim(c)}
                  >
                    {c.claim_type} · {c.statement}
                  </button>
                ))}
              </details>
              <details>
                <summary>Report scope and runtime metadata</summary>
                <p>{report.synthetic_notice}</p>
                <p>
                  Elapsed {report.elapsed_ms} ms · Model interactions{" "}
                  {report.model_interactions} · Model{" "}
                  {report.model_executed ?? "none"}
                </p>
                <p>Gaps: {report.gap_codes.join(" · ") || "none returned"}</p>
                <p>Source {report.source_fingerprint}</p>
                <p>Canonical report {report.canonical_fingerprint}</p>
                <p>
                  Step focus is transient; URL links retain the selected native
                  node, not an executed agent run.
                </p>
              </details>
            </div>
          )}
        </>
      )}
    </section>
  );
}
