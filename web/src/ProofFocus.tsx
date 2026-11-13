import type { Bundle } from "./contracts";
import { candidateKey } from "./graph";

export function ProofFocus({
  bundle,
  onSelect,
}: {
  bundle: Bundle;
  onSelect: (id: string) => void;
}) {
  const i = bundle.investigation;
  const focused =
    i.candidates.find((c) => c.dependency_depth > 0) ?? i.candidates[0];
  const path = focused?.changes[0]?.graph_path ?? focused?.graph_paths[0];
  return (
    <section className="proof-focus card" aria-labelledby="proof-focus-title">
      <div>
        <h2 id="proof-focus-title">Why this graph matters</h2>
        <p>
          Review connected incident evidence. Read-only Relate Cypher connects
          affected services, competing deployments and citation paths.
          Connection is not cause.
        </p>
        {focused && (
          <button
            className="primary-button"
            onClick={() =>
              onSelect(
                "candidate:" +
                  candidateKey(
                    focused.deployment_id,
                    focused.target_service_id,
                  ),
              )
            }
          >
            Explore the verified path
          </button>
        )}
        <p className="tiny muted">
          Verified means an exact stored path, not source truth or cause.
        </p>
      </div>
      <div>
        <strong>Affected service context</strong>
        {i.affected_services.length ? (
          i.affected_services.slice(0, 2).map((s) => (
            <button key={s.id} onClick={() => onSelect("node:" + s.id)}>
              {s.name.text} · {s.id}
            </button>
          ))
        ) : (
          <p>No affected service returned.</p>
        )}
      </div>
      <div>
        <strong>Competing deployment / target pairs</strong>
        {i.candidates.length ? (
          i.candidates.slice(0, 2).map((c) => (
            <button
              key={candidateKey(c.deployment_id, c.target_service_id)}
              onClick={() =>
                onSelect(
                  "candidate:" +
                    candidateKey(c.deployment_id, c.target_service_id),
                )
              }
            >
              <span className="sr-only">Focus proof </span>
              <b>{c.deployment_id}</b> → {c.target_service_id}{" "}
            </button>
          ))
        ) : (
          <p>No candidate returned; no cause established.</p>
        )}
      </div>
      {path && (
        <p className="proof-focus-path" aria-label="Native proof path">
          <strong>Stored direction: </strong>
          {path.node_ids.map((id, n) => (
            <span key={id + n}>
              {n > 0
                ? path.edges[n - 1].traversal_direction === "REVERSE"
                  ? " ← "
                  : " → "
                : ""}
              {id}
            </span>
          ))}
        </p>
      )}
      <p className="proof-focus-scope">
        Returned scope: {i.candidates.length} pairs · {i.evidence.length}{" "}
        evidence.{" "}
        {i.evidence[0]
          ? `${i.evidence[0].provenance_status} metadata / ${i.evidence[0].verification_status} source (first returned evidence).`
          : "No evidence returned."}{" "}
        External truth NOT_PERFORMED.
      </p>
    </section>
  );
}
