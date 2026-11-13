import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import {
  explanationSchema,
  validateScope,
  type Bundle,
  type Claim,
  type Explanation,
} from "./contracts";
import { requestJSON } from "./api";

const capabilities = z.strictObject({
  models: z.array(z.string().max(128)).max(32),
  truncated: z.boolean(),
  status: z.enum(["AVAILABLE", "UNAVAILABLE"]),
  code: z.string().max(64).nullable(),
});
const resultSchema = z.strictObject({
  source_fingerprint: z.string().regex(/^[a-f0-9]{64}$/),
  explanation: explanationSchema,
});

export function LocalSelection({
  bundle,
  onClaim,
}: {
  bundle: Bundle;
  onClaim: (claim: Claim) => void;
}) {
  const [models, setModels] = useState<string[] | null>(null),
    [model, setModel] = useState(""),
    [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [report, setReport] = useState<Explanation | null>(null);
  const controller = useRef<AbortController | null>(null),
    inFlight = useRef(false),
    mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      controller.current?.abort();
    };
  }, []);
  async function action(selection: boolean) {
    if (
      inFlight.current ||
      (selection && (!confirmed || !models?.includes(model)))
    )
      return;
    inFlight.current = true;
    setBusy(true);
    setNotice("");
    controller.current = new AbortController();
    try {
      const raw = await requestJSON(
        selection ? "/console/selection" : "/console/models/capabilities",
        controller.current.signal,
        selection
          ? {
              incident_id: bundle.investigation.incident_id,
              options: bundle.investigation.options,
              source_fingerprint: bundle.source_fingerprint,
              model_id: model,
              confirmed: true,
            }
          : { action: "LIST_INSTALLED_MODELS" },
      );
      if (!mounted.current || controller.current.signal.aborted) return;
      if (!selection) {
        const c = capabilities.parse(raw);
        setModels(c.models);
        setNotice(
          c.status === "UNAVAILABLE"
            ? `Local Ollama unavailable (${c.code}). Offline view retained.`
            : c.models.length
              ? "Choose an installed model; none is selected automatically."
              : "No eligible installed model. Nothing will be downloaded.",
        );
      } else {
        const r = resultSchema.parse(raw);
        if (
          r.source_fingerprint !== bundle.source_fingerprint ||
          r.explanation.mode_requested !== "OLLAMA"
        )
          throw new Error("Context changed");
        validateScope({ ...bundle, explanation: r.explanation }, false);
        const e = r.explanation;
        if (
          e.mode_executed === "OLLAMA" &&
          (!e.ai_generated_selection || e.model?.model_id !== model)
        )
          throw new Error("Model metadata mismatch");
        if (
          e.mode_executed === "NONE" &&
          (e.ai_generated_selection || e.claims.length)
        )
          throw new Error("Rejected result has claims");
        setReport(e);
        setNotice(
          e.mode_executed === "OLLAMA"
            ? "Accepted opaque-ID selection. Statements still use server templates; accuracy is not established."
            : `No accepted AI selection: ${e.explanation_status} ${e.rejection_codes.join(", ")}. No fallback was labelled AI.`,
        );
      }
    } catch (e) {
      if (mounted.current && !controller.current?.signal.aborted)
        setNotice(
          e instanceof Error && e.name === "ApiError"
            ? e.message
            : "Local action failed or context cannot be verified. Offline view retained.",
        );
    } finally {
      inFlight.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <section className="local-selection card" aria-labelledby="local-title">
      <h2 id="local-title">Optional local claim selection</h2>
      <p>
        Default: Deterministic · Offline · Not AI-generated. A local model
        selects prevalidated claim IDs, never diagnoses a cause or writes
        factual prose.
      </p>
      <button disabled={busy} onClick={() => void action(false)}>
        Compare with local AI selection
      </button>
      {models && (
        <div className="local-controls">
          <label>
            Installed local model
            <select
              aria-label="Installed local model"
              disabled={busy}
              value={model}
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
            I confirm one local selection for this snapshot. No download.
          </label>
          <button
            disabled={busy || !confirmed || !model}
            onClick={() => void action(true)}
          >
            Run confirmed local selection
          </button>
        </div>
      )}
      {busy && (
        <p role="status">
          Local action running. The provider deadline is bounded.
        </p>
      )}
      {busy && (
        <button
          onClick={() => {
            controller.current?.abort();
            setNotice(
              "Client wait cancelled. Server/provider work may continue until its deadline.",
            );
          }}
        >
          Cancel client wait
        </button>
      )}
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      {report && (
        <div className="selection-comparison">
          <div>
            <h3>Deterministic selection</h3>
            <p>
              {bundle.explanation.validated_claim_count} validated claims · Not
              AI-generated
            </p>
            {bundle.explanation.claims.map((c) => (
              <p key={c.claim_id}>
                <code>{c.claim_type}</code>
              </p>
            ))}
          </div>
          <div>
            <h3>Local selection result</h3>
            <p>
              Requested: {report.mode_requested} · Executed:{" "}
              {report.mode_executed}
            </p>
            <p>
              AI-generated selection: {String(report.ai_generated_selection)} ·
              Model: {report.model?.model_id ?? "None"}
            </p>
            <p>
              {report.explanation_status} · {report.validated_claim_count}{" "}
              claims · {report.validated_citation_count} citations
            </p>
            {report.claims.map((c) => (
              <button key={c.claim_id} onClick={() => onClaim(c)}>
                Inspect local claim {c.claim_type}: {c.statement}
              </button>
            ))}
            <p>NOT_ESTABLISHED · External truth NOT_PERFORMED</p>
            <code className="break">{report.investigation_fingerprint}</code>
          </div>
        </div>
      )}
    </section>
  );
}
