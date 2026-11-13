import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  ArrowRight,
  BookOpen,
  Database,
  GitBranch,
  Info,
  Layers3,
  Menu,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import { ApiError, getBundle, getIncidents } from "./api";
import type { Bundle, Claim, Incident, Options, Path, Time } from "./contracts";
import { edgeTypes } from "./contracts";
import { GraphCanvas } from "./GraphCanvas";
import { LocalSelection } from "./LocalSelection";
import {
  candidateKey,
  defaultFilters,
  edgeKey,
  filterGraph,
  graphFromBundle,
  pairKey,
  selectionExists,
  selectionPaths,
  type Filters,
  type Graph,
} from "./graph";
import {
  navigationURL,
  parseNavigation,
  utcText,
  type Navigation,
} from "./navigation";

const tabs = [
  "Candidates",
  "Evidence",
  "Timeline",
  "Observations",
  "Gaps",
] as const;
type DetailTab = (typeof tabs)[number];
type Loaded = { bundle: Bundle; graph: Graph };
function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
function EventTime({ time }: { time: Time }) {
  return (
    <span className="event-time">
      <span>{utcText(time)}</span>
      {time.original && time.original !== time.utc && (
        <small>Original: {time.original}</small>
      )}
      {time.original_withheld && <small>Original value withheld</small>}
    </span>
  );
}
function PathList({
  paths,
  onSelect,
}: {
  paths: Path[];
  onSelect: (s: string) => void;
}) {
  return (
    <div className="path-list">
      {paths.length === 0 ? (
        <p className="muted">
          This selection has no graph-path citation. Inspect its typed citations
          below.
        </p>
      ) : (
        paths.slice(0, 60).map((p, n) => (
          <div className="path-proof" key={n}>
            <div className="path-order">
              {p.node_ids.map((id, i) => (
                <span key={id + "-" + i}>
                  <button onClick={() => onSelect("node:" + id)}>{id}</button>
                  {i < p.edges.length && (
                    <ArrowRight size={12} aria-label="next in traversal" />
                  )}
                </span>
              ))}
            </div>
            {p.edges.map((e, i) => (
              <div className="edge-proof" key={i}>
                <button onClick={() => onSelect("edge:" + edgeKey(e))}>
                  {e.type}
                </button>
                <code>
                  {e.source_id} → {e.target_id}
                </code>
                <span>
                  {e.traversal_direction === "REVERSE"
                    ? "Reverse traversal"
                    : "Forward traversal"}
                </span>
              </div>
            ))}
          </div>
        ))
      )}
      {paths.length > 60 && (
        <p className="notice">
          Showing 60 of {paths.length} returned paths. Select an item to narrow
          the view.
        </p>
      )}
    </div>
  );
}

function CitationRows({
  claim,
  onSelect,
}: {
  claim: Claim;
  onSelect: (s: string) => void;
}) {
  return (
    <div className="citation-list">
      {claim.citations.map((c, n) => (
        <article className="citation" key={n}>
          <Badge>{c.kind}</Badge>
          <div className="reference-ids">
            {c.entity_ids.map((id) => (
              <code key={id}>{id}</code>
            ))}
          </div>
          {c.graph_path && (
            <PathList paths={[c.graph_path]} onSelect={onSelect} />
          )}
          {c.event_utc && (
            <p>
              {c.event_utc}{" "}
              {c.temporal_classification && (
                <Badge>{c.temporal_classification}</Badge>
              )}
            </p>
          )}
          {c.provenance_status && (
            <p>
              Metadata: <Badge>{c.provenance_status}</Badge> Source:{" "}
              <Badge>{c.verification_status}</Badge>
            </p>
          )}
          {c.source_ref_withheld && (
            <p className="muted">Source reference withheld</p>
          )}
          {c.classification && (
            <p>
              <Badge tone="amber">{c.classification}</Badge>
              <small>
                {c.overlap_start} — {c.overlap_end}
              </small>
            </p>
          )}
          {c.code && (
            <p>
              {c.code}
              {c.count !== null && ` · count ${c.count}`}
            </p>
          )}
        </article>
      ))}
    </div>
  );
}

function Inspector({
  data,
  selection,
  onSelect,
  localClaim,
}: {
  data: Loaded;
  selection: string;
  onSelect: (s: string) => void;
  localClaim?: Claim | null;
}) {
  const { bundle: b, graph } = data;
  const i = b.investigation;
  const [kind, ...rest] = selection.split(":"),
    id = rest.join(":");
  const claim =
    localClaim ??
    b.explanation.claims.find((c) => kind === "claim" && c.claim_id === id);
  const candidate = i.candidates.find(
    (c) =>
      kind === "candidate" &&
      candidateKey(c.deployment_id, c.target_service_id) === id,
  );
  const evidence = i.evidence.find(
    (e) => kind === "evidence" && e.evidence_id === id,
  );
  const comparison = i.contradictions.find(
    (c) => kind === "comparison" && pairKey(c.evidence_ids) === id,
  );
  const node = graph.nodes.find((n) => kind === "node" && n.id === id),
    edge = graph.edges.find((e) => kind === "edge" && e.id === id);
  const paths = localClaim
      ? localClaim.citations.flatMap((c) =>
          c.graph_path ? [c.graph_path] : [],
        )
      : selectionPaths(b, selection),
    exists = !!localClaim || selectionExists(b, graph, selection);
  const linked = b.explanation.claims.filter((c) =>
    node
      ? c.referenced_entity_ids.includes(node.id) ||
        c.citations.some((x) => x.graph_path?.node_ids.includes(node.id))
      : edge
        ? c.citations.some((x) =>
            x.graph_path?.edges.some((e) => edgeKey(e) === edge.id),
          )
        : false,
  );
  return (
    <aside className="inspector card" aria-label="Proof inspector">
      <header className="panel-title">
        <h2 className="panel-heading">
          <ShieldCheck size={16} /> Proof inspector
        </h2>
        <span className="tiny mono">SNAPSHOT BOUND</span>
      </header>
      <div className="inspector-content">
        {!selection && (
          <div className="inspector-intro">
            <GitBranch size={26} />
            <h3>Follow the proof</h3>
            <p>
              Select a graph item, candidate, evidence record or
              server-validated claim to inspect its exact support.
            </p>
          </div>
        )}
        {selection && !exists && (
          <p role="status" className="notice amber">
            Selection unavailable in this returned scope. No ghost path is
            displayed.
          </p>
        )}
        {claim && (
          <section aria-label="Selected claim">
            <div className="eyebrow">SERVER-RETURNED CLAIM</div>
            <h3>{claim.claim_type.replaceAll("_", " ")}</h3>
            <p className="claim-statement">{claim.statement}</p>
            <code className="break">{claim.claim_id}</code>
            <p className="support-label">{claim.support_status}</p>
            <p className="muted">
              Support is scoped context, not independently verified truth.
            </p>
            <CitationRows claim={claim} onSelect={onSelect} />
          </section>
        )}
        {candidate && (
          <section aria-label="Selected candidate">
            <div className="eyebrow">CONNECTED CANDIDATE</div>
            <h3>{candidate.deployment_id}</h3>
            <p>{candidate.name.text}</p>
            <Badge>{candidate.temporal_classification}</Badge>
            <p>
              Target <code>{candidate.target_service_id}</code> · depth{" "}
              {candidate.dependency_depth}
            </p>
            <EventTime time={candidate.deployment_occurred_at} />
            <p className="notice">
              {candidate.candidate_assessment}. Temporal precedence is not
              causation.
            </p>
            <PathList paths={paths} onSelect={onSelect} />
            <h4>Returned changes</h4>
            {candidate.changes.length ? (
              candidate.changes.map((c) => (
                <button
                  className="reference-button"
                  key={c.change_id}
                  onClick={() => onSelect("node:" + c.change_id)}
                >
                  {c.change_id} · {c.name.text}
                </button>
              ))
            ) : (
              <p>
                No change links returned. This is not proof that no change
                exists.
              </p>
            )}
          </section>
        )}
        {evidence && (
          <section aria-label="Selected evidence">
            <div className="eyebrow">INCIDENT-SCOPED EVIDENCE</div>
            <h3>{evidence.evidence_id}</h3>
            <Badge>{evidence.provenance_status}</Badge>{" "}
            <Badge>{evidence.verification_status}</Badge>
            <p>Source reference withheld</p>
            <EventTime time={evidence.evidence_observed_at} />
            {!evidence.observed_service_ids.length && (
              <p className="notice amber">
                No returned OBSERVED_ON link. The orphan evidence remains
                visible.
              </p>
            )}
            <PathList paths={paths} onSelect={onSelect} />
            {evidence.warnings.map((w) => (
              <p className="notice" key={w.code}>
                {w.code}
              </p>
            ))}
          </section>
        )}
        {comparison && (
          <section aria-label="Selected comparison">
            <div className="eyebrow">STRUCTURED OBSERVATIONS</div>
            <h3>
              {comparison.classification === "UNDETERMINED"
                ? "Undetermined comparison"
                : "Conflicting observations"}
            </h3>
            <Badge tone="amber">{comparison.classification}</Badge>
            <p>{comparison.observed_states.join(" / ")}</p>
            <p>
              Service <code>{comparison.service_id}</code>
            </p>
            <p>
              Signal: {comparison.signal_key.text} · environment:{" "}
              {comparison.environment.text}
            </p>
            <p>
              UTC overlap: {comparison.overlap_window.start} —{" "}
              {comparison.overlap_window.end}
            </p>
            {comparison.evidence_ids.map((e) => (
              <button
                className="reference-button"
                key={e}
                onClick={() => onSelect("evidence:" + e)}
              >
                {e}
              </button>
            ))}
            <p className="muted">
              Comparable states are not independent source truth or incident
              causality.
            </p>
            <PathList paths={paths} onSelect={onSelect} />
          </section>
        )}
        {node && (
          <section aria-label="Selected node">
            <div className="eyebrow">RETURNED GRAPH NODE</div>
            <h3>{node.id}</h3>
            <Badge>{node.kind}</Badge>
            <p>{node.name}</p>
            <h4>Why it appears</h4>
            <p>
              This stable ID occurs on the returned paths below. No relationship
              is inferred from its name.
            </p>
            <PathList paths={paths} onSelect={onSelect} />
          </section>
        )}
        {edge && (
          <section aria-label="Selected edge">
            <div className="eyebrow">PERSISTED RELATIONSHIP</div>
            <h3>{edge.type}</h3>
            <p>Stored direction</p>
            <code className="break">
              {edge.source} → {edge.target}
            </code>
            <p>
              {edge.reverse
                ? "This stored edge is traversed in REVERSE in a returned path. Its arrow is not reversed."
                : "Forward traversal in returned paths."}
            </p>
            <PathList paths={paths} onSelect={onSelect} />
          </section>
        )}
        {linked.length > 0 && (
          <section>
            <h4>Cited by server claims</h4>
            {linked.map((c) => (
              <button
                className="reference-button"
                key={c.claim_id}
                onClick={() => onSelect("claim:" + c.claim_id)}
              >
                {c.claim_type}
              </button>
            ))}
          </section>
        )}
        <section className="claims-section">
          <div className="section-heading">
            <h3>Validated explanation</h3>
            <span className="count">{b.explanation.claims.length}</span>
          </div>
          <p className="mode-label">
            Deterministic · Offline · Not AI-generated
          </p>
          <Badge>{b.explanation.explanation_status}</Badge>
          <p className="muted">{b.explanation.overview}</p>
          <p className="tiny">
            {b.explanation.validated_claim_count} validated claims ·{" "}
            {b.explanation.validated_citation_count} citation entries.{" "}
            {b.explanation.truncation.selected_subset
              ? "Selected subset; not the whole catalog."
              : ""}
          </p>
          {b.explanation.claims.map((c, n) => (
            <button
              className={`claim-button ${claim?.claim_id === c.claim_id ? "active" : ""}`}
              key={c.claim_id}
              onClick={() => onSelect("claim:" + c.claim_id)}
            >
              <span className="sr-only">
                Inspect claim {c.claim_type} {c.claim_id}.{" "}
              </span>
              <span className="claim-number">
                {String(n + 1).padStart(2, "0")}
              </span>
              <span>
                <strong>{c.claim_type.replaceAll("_", " ")}</strong>
                <span>{c.statement}</span>
              </span>
              <ArrowRight size={13} />
            </button>
          ))}
        </section>
        <details className="snapshot-details">
          <summary>Snapshot and scope</summary>
          <p>Exact source fingerprint</p>
          <code className="break">{b.source_fingerprint}</code>
          <p>Published view digest</p>
          <code className="break">{b.view_fingerprint}</code>
          <p>
            Content hashes bind a snapshot; they do not authenticate source
            truth.
          </p>
        </details>
      </div>
    </aside>
  );
}

function DetailPanel({
  data,
  tab,
  setTab,
  onSelect,
}: {
  data: Loaded;
  tab: DetailTab;
  setTab: (t: DetailTab) => void;
  onSelect: (s: string) => void;
}) {
  const b = data.bundle,
    i = b.investigation;
  return (
    <section className="details-card card" aria-label="Investigation records">
      <div
        className="detail-tabs"
        role="tablist"
        aria-label="Investigation views"
      >
        {tabs.map((t, n) => (
          <button
            id={`tab-${t}`}
            key={t}
            role="tab"
            aria-selected={tab === t}
            aria-controls={`panel-${t}`}
            tabIndex={tab === t ? 0 : -1}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                e.preventDefault();
                const next =
                  tabs[
                    (n + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) %
                      tabs.length
                  ];
                setTab(next);
                document.getElementById("tab-" + next)?.focus();
              }
            }}
            onClick={() => setTab(t)}
          >
            {t}
            <span>
              {t === "Candidates"
                ? i.candidates.length
                : t === "Evidence"
                  ? i.evidence.length
                  : t === "Timeline"
                    ? i.timeline.length
                    : t === "Observations"
                      ? i.contradictions.length
                      : i.evidence_gaps.length}
            </span>
          </button>
        ))}
      </div>
      <div
        role="tabpanel"
        id={`panel-${tab}`}
        aria-labelledby={`tab-${tab}`}
        tabIndex={0}
        className="detail-content"
      >
        {tab === "Candidates" && (
          <>
            <p className="muted">
              Competing deployment/target pairs from actual graph paths. No
              causal ranking.
            </p>
            <div className="candidate-grid">
              {i.candidates.map((c) => (
                <article
                  className="candidate-card"
                  key={candidateKey(c.deployment_id, c.target_service_id)}
                >
                  <div className="section-heading">
                    <Badge>{c.temporal_classification}</Badge>
                    <span className="tiny">Depth {c.dependency_depth}</span>
                  </div>
                  <button
                    className="record-link"
                    onClick={() =>
                      onSelect(
                        "candidate:" +
                          candidateKey(c.deployment_id, c.target_service_id),
                      )
                    }
                    aria-label={`Inspect candidate ${c.deployment_id} on ${c.target_service_id}`}
                  >
                    <strong>{c.deployment_id}</strong>
                    <ArrowRight size={14} />
                  </button>
                  <p>{c.name.text}</p>
                  <div className="tiny">
                    TARGETS <code>{c.target_service_id}</code>
                  </div>
                  <EventTime time={c.deployment_occurred_at} />
                  <div className="tiny muted">
                    {c.candidate_assessment} · {c.changes.length} returned
                    changes
                  </div>
                </article>
              ))}
            </div>
            {!i.candidates.length && (
              <p className="notice">
                No candidate paths returned. Missing context is not a causal
                verdict.
              </p>
            )}
          </>
        )}
        {tab === "Evidence" && (
          <>
            <p className="muted">
              Returned incident-scoped evidence. TRACEABLE describes metadata,
              not source authenticity.
            </p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Evidence ID</th>
                    <th>Metadata / source</th>
                    <th>Observation time (UTC)</th>
                    <th>Service links</th>
                  </tr>
                </thead>
                <tbody>
                  {i.evidence.map((e) => (
                    <tr key={e.evidence_id}>
                      <td>
                        <button
                          className="record-link"
                          onClick={() => onSelect("evidence:" + e.evidence_id)}
                          aria-label={`Inspect evidence ${e.evidence_id}`}
                        >
                          {e.evidence_id}
                        </button>
                      </td>
                      <td>
                        <Badge>{e.provenance_status}</Badge>
                        <small>{e.verification_status}</small>
                        <small>Source reference withheld</small>
                      </td>
                      <td>
                        <EventTime time={e.evidence_observed_at} />
                        <Badge>{e.temporal_classification}</Badge>
                      </td>
                      <td>
                        {e.observed_service_ids.length ? (
                          e.observed_service_ids.join(", ")
                        ) : (
                          <span className="amber-text">No OBSERVED_ON</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!i.evidence.length && (
              <p className="notice amber">
                No incident-scoped evidence returned. Explanation abstains.
              </p>
            )}
          </>
        )}
        {tab === "Timeline" && (
          <>
            <p className="muted">
              UTC event times only. Unknown/invalid values stay unknown;
              ingestion time is never substituted.
            </p>
            <ol className="timeline">
              {i.timeline.map((e, n) => (
                <li key={n}>
                  <span className="timeline-dot" />
                  <div>
                    <span className="tiny">{e.kind}</span>
                    <button
                      className="record-link"
                      onClick={() =>
                        onSelect(
                          e.kind === "EVIDENCE"
                            ? "evidence:" + e.entity_id
                            : e.kind === "DEPLOYMENT"
                              ? "candidate:" +
                                candidateKey(
                                  e.entity_id,
                                  e.target_service_id ?? "",
                                )
                              : "node:" + e.entity_id,
                        )
                      }
                    >
                      {e.entity_id}
                    </button>
                    <EventTime time={e.timestamp} />
                  </div>
                  <Badge>{e.temporal_classification}</Badge>
                </li>
              ))}
            </ol>
          </>
        )}
        {tab === "Observations" && (
          <>
            <p className="muted">
              Only same-service/signal/environment observations with overlapping
              valid intervals are compared.
            </p>
            {i.contradictions.map((c) => (
              <button
                className="comparison-card"
                key={pairKey(c.evidence_ids)}
                onClick={() =>
                  onSelect("comparison:" + pairKey(c.evidence_ids))
                }
                aria-label={`Inspect ${c.classification} ${c.evidence_ids.join(" and ")}`}
              >
                <div>
                  <Badge tone="amber">{c.classification}</Badge>
                  <strong>{c.observed_states.join(" / ")}</strong>
                </div>
                <p>{c.evidence_ids.join(" ↔ ")}</p>
                <small>
                  {c.service_id} · {c.signal_key.text} · {c.environment.text}
                </small>
              </button>
            ))}
            {!i.contradictions.length && (
              <p className="notice">
                No comparable conflicting or undetermined pairs returned. This
                does not independently verify the evidence.
              </p>
            )}
          </>
        )}
        {tab === "Gaps" && (
          <>
            <p className="muted">
              Actual source findings and deterministic next checks, not
              remediation instructions.
            </p>
            {i.evidence_gaps.map((g) => (
              <div className="gap-row" key={g.code}>
                <Info size={15} />
                <div>
                  <strong>{g.code}</strong>
                  <small>
                    {g.entity_ids.join(", ")}
                    {g.references_omitted ? " · references omitted" : ""}
                  </small>
                </div>
                <Badge>{g.count}</Badge>
              </div>
            ))}
            <h4>Next checks</h4>
            <ul className="next-checks">
              {b.explanation.next_checks.map((s, n) => (
                <li key={n}>{s}</li>
              ))}
            </ul>
            {b.explanation.truncation.next_checks && (
              <p className="notice">
                Next-check subset; details omitted by a bound.
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}

export function App() {
  const [localSelected, setLocalSelected] = useState<{
    source: string;
    claim: Claim;
  } | null>(null);
  const [nav, setNav] = useState<Navigation>(() =>
    parseNavigation(location.search),
  );
  const [incidents, setIncidents] = useState<Incident[]>([]),
    [listError, setListError] = useState(""),
    [listLoading, setListLoading] = useState(true);
  const [listNotice, setListNotice] = useState("");
  const [data, setData] = useState<Loaded | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [refresh, setRefresh] = useState(0);
  const [search, setSearch] = useState(""),
    [filters, setFilters] = useState<Filters>(defaultFilters),
    [tab, setTab] = useState<DetailTab>("Candidates");
  const [mobileView, setMobileView] = useState("graph"),
    [navOpen, setNavOpen] = useState(false),
    [guide, setGuide] = useState(-1);
  const help = useRef<HTMLDialogElement>(null);
  const sequence = useRef(0);
  const optionKey = JSON.stringify(nav.options);
  useEffect(() => {
    const onPop = () => setNav(parseNavigation(location.search));
    addEventListener("popstate", onPop);
    return () => removeEventListener("popstate", onPop);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setListLoading(true);
    setListError("");
    getIncidents(controller.signal)
      .then((v) => {
        setIncidents(v.incidents.sort((a, b) => a.id.localeCompare(b.id)));
        setListNotice(
          v.results_may_be_truncated || v.unsafe_identifiers_omitted > 0
            ? "Incident list is capped or unsupported identifiers were withheld."
            : "",
        );
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setListError(
            e instanceof ApiError ? e.message : "Incident list unavailable",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setListLoading(false);
      });
    return () => controller.abort();
  }, [refresh]);
  useEffect(() => {
    const controller = new AbortController(),
      request = ++sequence.current;
    setData(null);
    setLoading(true);
    setError("");
    setFilters(defaultFilters);
    getBundle(nav.incident, JSON.parse(optionKey) as Options, controller.signal)
      .then((bundle) => {
        const graph = graphFromBundle(bundle);
        if (!controller.signal.aborted && request === sequence.current)
          setData({ bundle, graph });
      })
      .catch((e) => {
        if (!controller.signal.aborted && request === sequence.current)
          setError(
            e instanceof ApiError
              ? e.message
              : e instanceof TypeError
                ? "Disconnected from local server"
                : "Cannot verify context. Cross-highlighting is disabled.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted && request === sequence.current)
          setLoading(false);
      });
    return () => controller.abort();
  }, [nav.incident, optionKey, refresh]);
  function navigate(next: Navigation) {
    history.pushState(null, "", navigationURL(next));
    setNav(next);
  }
  function select(s: string) {
    navigate({ ...nav, selection: s, warnings: [] });
    if (innerWidth < 900) setMobileView("inspector");
  }
  function incident(id: string) {
    navigate({ ...nav, incident: id, selection: "", warnings: [] });
    setNavOpen(false);
    setMobileView("graph");
    setTab("Candidates");
  }
  const shown = incidents.filter((i) =>
    (i.id + " " + i.title).toLowerCase().includes(search.toLowerCase()),
  );
  const visible = useMemo(
    () => (data ? filterGraph(data.graph, data.bundle, filters) : null),
    [data, filters],
  );
  const localClaim =
    data &&
    localSelected?.source === data.bundle.source_fingerprint &&
    nav.selection === "claim:" + localSelected.claim.claim_id
      ? localSelected.claim
      : null;
  const paths = localClaim
    ? localClaim.citations.flatMap((c) => (c.graph_path ? [c.graph_path] : []))
    : data
      ? selectionPaths(data.bundle, nav.selection)
      : [];
  const i = data?.bundle.investigation,
    e = data?.bundle.explanation;
  const activeTab = (name: string) => setMobileView(name);
  const guideSteps = [
    {
      title: "Follow the stored path",
      text: "Select DEP-001 and inspect Payment → Auth ← Deployment. TARGETS points from deployment to service.",
      action: () => {
        navigate({
          ...nav,
          incident: "INC-001",
          selection: "candidate:DEP-001~SVC-AUTH",
          warnings: [],
        });
        setMobileView("graph");
      },
    },
    {
      title: "Inspect an admitted statement",
      text: "Choose a server-returned claim in the inspector. Every highlighted edge is from its returned citation paths.",
      action: () => {
        if (e?.claims[0]) select("claim:" + e.claims[0].claim_id);
      },
    },
    {
      title: "Keep disagreement visible",
      text: "Open CASE-INC Observations: one HEALTHY/FAILED conflict and two undetermined DEGRADED comparisons.",
      action: () => {
        incident("CASE-INC");
        setTab("Observations");
        setMobileView("details");
      },
    },
    {
      title: "Finish with uncertainty",
      text: "Review gaps and next checks. Connected deployments are candidates, not proven causes. NOT_ESTABLISHED remains the conclusion.",
      action: () => {
        setTab("Gaps");
        setMobileView("details");
      },
    },
  ];
  return (
    <div className={`app ${navOpen ? "nav-open" : ""}`}>
      <a className="skip-link" href="#main">
        Skip to investigation
      </a>
      <aside className="sidebar" aria-label="Incident navigation">
        <a className="brand" href="/?incident=INC-001">
          <span className="brand-mark">
            <Network size={23} />
          </span>
          <span>
            Trace<span className="brand-light">Weaver</span>
            <small>CONNECTED INVESTIGATIONS</small>
          </span>
        </a>
        <div className="workspace-label">
          <span className="status-dot" /> LOCAL WORKSPACE{" "}
          <Badge>READ ONLY</Badge>
        </div>
        <div className="nav-section-title">
          INCIDENTS <span>{incidents.length} returned</span>
        </div>
        <label className="search">
          <Search size={15} />
          <input
            aria-label="Search returned incidents"
            value={search}
            onChange={(e) => setSearch(e.target.value.slice(0, 128))}
            placeholder="Find an incident…"
          />
        </label>
        <nav aria-label="Returned incidents">
          {listLoading && (
            <p role="status" className="muted">
              Loading incidents…
            </p>
          )}
          {listError && (
            <p role="alert" className="notice">
              {listError}
            </p>
          )}
          {listNotice && (
            <p className="notice" role="status">
              {listNotice}
            </p>
          )}
          {!listLoading && !listError && !shown.length && (
            <p className="muted">No returned incidents match.</p>
          )}
          {shown.map((item) => (
            <button
              className={`incident-button ${nav.incident === item.id ? "active" : ""}`}
              key={item.id}
              onClick={() => incident(item.id)}
              aria-current={nav.incident === item.id ? "page" : undefined}
            >
              <span className="incident-row">
                <span className="incident-dot" />
                <strong>{item.id}</strong>
                <ArrowRight size={13} />
              </span>
              <span className="incident-name">{item.title}</span>
              <span className="tiny">
                {item.severity} · {item.status}
              </span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="engine">
            <Database size={17} />
            <span>
              Powered by Relate<small>Embedded, persistent graph</small>
            </span>
          </div>
          <button
            className="quiet-button"
            onClick={() => help.current?.showModal()}
          >
            <BookOpen size={15} /> About this console
          </button>
          <p>
            Evidence-linked context.
            <br />
            No causal verdict.
          </p>
        </div>
      </aside>
      {navOpen && (
        <button
          className="nav-mask"
          aria-label="Close incident navigation"
          onClick={() => setNavOpen(false)}
        />
      )}
      <main id="main" className={`main mobile-${mobileView}`}>
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-nav-toggle"
              aria-label="Toggle incident navigation"
              aria-expanded={navOpen}
              onClick={() => setNavOpen(!navOpen)}
            >
              <Menu size={19} />
            </button>
            <span>WORKSPACE</span>
            <span>/</span>
            <strong>INCIDENT REVIEW</strong>
          </div>
          <div className="top-actions">
            <span className="connection">
              <span className="status-dot" /> LOCAL · READ ONLY
            </span>
            <button
              className="quiet-button"
              onClick={() => {
                setGuide(0);
                guideSteps[0].action();
              }}
            >
              <Layers3 size={14} /> Guided demo
            </button>
            <button
              className="icon-button"
              aria-label="Refresh current snapshot"
              onClick={() => setRefresh((v) => v + 1)}
            >
              <RefreshCw size={16} />
            </button>
          </div>
        </header>
        {nav.warnings.length > 0 && (
          <div role="status" className="notice amber">
            {nav.warnings.join(" ")}
          </div>
        )}
        {guide >= 0 && (
          <section className="guide card">
            <div>
              <span className="eyebrow">
                GUIDED DEMO · {guide + 1} / {guideSteps.length}
              </span>
              <h3>{guideSteps[guide].title}</h3>
              <p>{guideSteps[guide].text}</p>
            </div>
            <button
              className="primary-button"
              onClick={() => {
                if (guide < guideSteps.length - 1) {
                  const next = guide + 1;
                  setGuide(next);
                  guideSteps[next].action();
                } else setGuide(-1);
              }}
            >
              {guide < guideSteps.length - 1 ? "Next step" : "Finish"}
              <ArrowRight size={14} />
            </button>
            <button
              className="icon-button"
              aria-label="Close guided demo"
              onClick={() => setGuide(-1)}
            >
              <X size={16} />
            </button>
          </section>
        )}
        {loading && (
          <section className="loading-state" role="status" aria-live="polite">
            <span className="eyebrow">READING ACTUAL RELATE CONTEXT</span>
            <div className="skeleton wide" />
            <div className="skeleton" />
            <div className="skeleton graph-skeleton" />
            <p>Loading incident snapshot…</p>
          </section>
        )}
        {error && (
          <section className="error-state card" role="alert">
            <Database size={32} />
            <h1>{error}</h1>
            <p>
              No prepared graph or explanation is substituted. Check the local
              read-only server and selected incident.
            </p>
            <button
              className="primary-button"
              onClick={() => setRefresh((v) => v + 1)}
            >
              Try again
            </button>
          </section>
        )}
        {data && i && e && visible && (
          <>
            <section className="incident-heading">
              <div>
                <div className="eyebrow">
                  <span className="mono">{i.incident_id}</span>
                  <span> / </span>
                  {i.is_demo === true
                    ? "SYNTHETIC DEMO"
                    : i.is_demo === false
                      ? "NON-DEMO · UNVERIFIED"
                      : "DEMO STATUS UNKNOWN"}
                </div>
                <h1>{i.title.text}</h1>
                <div className="heading-meta">
                  <Badge tone="amber">{i.investigation_status}</Badge>
                  <span>
                    <Activity size={13} /> Onset{" "}
                    <EventTime time={i.incident_time} />
                  </span>
                </div>
              </div>
              <div className="verdict">
                <span>CAUSAL CONCLUSION</span>
                <strong data-testid="causal-status">NOT_ESTABLISHED</strong>
                <small>External truth: NOT_PERFORMED</small>
              </div>
            </section>
            <div className="scope-banner">
              <Info size={15} />
              <span>
                {i.is_demo === true ? "Synthetic data · " : ""}Returned context
                only.{" "}
                {i.results_may_be_truncated
                  ? "Source caps reached; omitted context may change this review."
                  : "Representative paths are partial, even when source caps are not reached."}{" "}
                Connection and temporal precedence do not establish causation.
              </span>
            </div>
            <section className="metrics" aria-label="Returned scope metrics">
              <div>
                <span>Candidate / target pairs</span>
                <strong>{i.candidates.length}</strong>
                <GitBranch size={18} />
              </div>
              <div>
                <span>Incident-scoped evidence</span>
                <strong>{i.evidence.length}</strong>
                <Layers3 size={18} />
              </div>
              <div>
                <span>Conflicts / undetermined</span>
                <strong>
                  {e.evidence_summary.conflict_count}
                  <small> / {e.evidence_summary.undetermined_count}</small>
                </strong>
                <Activity size={18} />
              </div>
              <div>
                <span>Validated claims / citations</span>
                <strong>
                  {e.validated_claim_count}
                  <small> / {e.validated_citation_count}</small>
                </strong>
                <ShieldCheck size={18} />
              </div>
            </section>
            <details className="options card">
              <summary>
                Investigation window &amp; caps{" "}
                <span>
                  −{nav.options.pre_minutes}m / +{nav.options.post_minutes}m ·{" "}
                  {nav.options.max_candidates} candidates ·{" "}
                  {nav.options.max_evidence} evidence
                </span>
              </summary>
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  const values = new FormData(event.currentTarget),
                    p = new URLSearchParams();
                  Object.keys(nav.options).forEach((k) =>
                    p.set(k, String(values.get(k))),
                  );
                  const parsed = parseNavigation("?" + p);
                  navigate({
                    ...nav,
                    selection: "",
                    options: parsed.options,
                    warnings: parsed.warnings,
                  });
                }}
              >
                {Object.entries(nav.options).map(([k, v]) => (
                  <label key={k}>
                    {k.replaceAll("_", " ")}
                    <input
                      name={k}
                      aria-label={k}
                      type="number"
                      min={k.startsWith("max_") ? 1 : 0}
                      max={k.startsWith("max_") ? 100 : 1440}
                      step="1"
                      defaultValue={v}
                      key={String(v)}
                    />
                  </label>
                ))}
                <button className="primary-button">
                  Apply bounded options
                </button>
              </form>
            </details>
            <div
              className="mobile-tabs"
              role="group"
              aria-label="Mobile workspace views"
            >
              {["graph", "inspector", "details"].map((t) => (
                <button
                  key={t}
                  aria-pressed={mobileView === t}
                  onClick={() => activeTab(t)}
                >
                  {t[0].toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
            <div className="workspace">
              <div className="workspace-center">
                <section className="graph-card card">
                  <header className="panel-title">
                    <span>
                      <Network size={17} /> Connected context
                    </span>
                    <span className="tiny">
                      {visible.nodes.length} nodes · {visible.edges.length}{" "}
                      edges
                    </span>
                  </header>
                  <div className="graph-subtitle">
                    PARTIAL RETURNED SUBGRAPH{" "}
                    <span>Stored arrows · read only</span>
                  </div>
                  <div className="filters" aria-label="Visual graph filters">
                    {(
                      [
                        {
                          key: "kind",
                          label: "Node kind",
                          values: [
                            "Incident",
                            "Service",
                            "Deployment",
                            "Change",
                            "Evidence",
                          ],
                        },
                        { key: "edge", label: "Edge type", values: edgeTypes },
                        {
                          key: "temporal",
                          label: "Time class",
                          values: [
                            "BEFORE",
                            "AT_ONSET",
                            "AFTER",
                            "OUTSIDE_WINDOW",
                            "UNKNOWN",
                          ],
                        },
                        {
                          key: "assessment",
                          label: "Candidate status",
                          values: [
                            "INVESTIGATE",
                            "INSUFFICIENT_DATA",
                            "TEMPORALLY_EXCLUDED",
                          ],
                        },
                        {
                          key: "provenance",
                          label: "Evidence metadata",
                          values: ["TRACEABLE", "INCOMPLETE", "INVALID"],
                        },
                      ] as {
                        key: keyof Filters;
                        label: string;
                        values: readonly string[];
                      }[]
                    ).map((f) => (
                      <label key={f.key}>
                        <span>{f.label}</span>
                        <select
                          aria-label={f.label}
                          value={filters[f.key]}
                          onChange={(event) =>
                            setFilters({
                              ...filters,
                              [f.key]: event.target.value,
                            })
                          }
                        >
                          <option value="ALL">All</option>
                          {f.values.map((v) => (
                            <option key={v}>{v}</option>
                          ))}
                        </select>
                      </label>
                    ))}
                    <button
                      className="filter-reset"
                      onClick={() => setFilters(defaultFilters)}
                    >
                      Reset filters
                    </button>
                  </div>
                  <GraphCanvas
                    key={data.bundle.source_fingerprint}
                    graph={visible}
                    paths={paths}
                    onSelect={select}
                  />
                  <div className="graph-footer">
                    <div className="legend">
                      {[
                        "Incident",
                        "Service",
                        "Deployment",
                        "Change",
                        "Evidence",
                      ].map((k) => (
                        <span key={k}>
                          <i className={"legend-" + k.toLowerCase()} />
                          {k}
                        </span>
                      ))}
                    </div>
                    <p className="tiny">
                      Hidden by visual filters:{" "}
                      {data.graph.nodes.length - visible.nodes.length} nodes /{" "}
                      {data.graph.edges.length - visible.edges.length} edges.
                      Data is not edited.
                    </p>
                    {(data.graph.omittedNodes > 0 ||
                      data.graph.omittedEdges > 0) && (
                      <p className="notice amber">
                        Display cap omitted {data.graph.omittedNodes} nodes /{" "}
                        {data.graph.omittedEdges} edges.
                      </p>
                    )}
                  </div>
                  <details className="accessible-paths">
                    <summary>
                      Accessible path list · traversal order and stored
                      directions
                    </summary>
                    <PathList
                      paths={paths.length ? paths : data.graph.paths}
                      onSelect={select}
                    />
                  </details>
                </section>
                <DetailPanel
                  data={data}
                  tab={tab}
                  setTab={setTab}
                  onSelect={select}
                />
                <LocalSelection
                  key={data.bundle.source_fingerprint}
                  bundle={data.bundle}
                  onClaim={(claim) => {
                    setLocalSelected({
                      source: data.bundle.source_fingerprint,
                      claim,
                    });
                    select("claim:" + claim.claim_id);
                  }}
                />
              </div>
              <Inspector
                data={data}
                selection={nav.selection}
                onSelect={select}
                localClaim={localClaim}
              />
            </div>
            <footer className="page-footer">
              <span>
                <Database size={12} /> Real Relate graph · deterministic
                citation firewall
              </span>
              <span>
                No source URL is followed. No graph editing. No model on page
                load.
              </span>
            </footer>
          </>
        )}
      </main>
      <dialog ref={help} aria-labelledby="help-title">
        <button
          className="icon-button dialog-close"
          aria-label="Close console help"
          onClick={() => help.current?.close()}
        >
          <X size={18} />
        </button>
        <Network size={28} />
        <h2 id="help-title">Inspect context. Keep uncertainty.</h2>
        <p>
          TraceWeaver reads a real embedded Relate graph. Returned paths carry
          exact stored directions. Statements come only from the server's
          citation-validated claims.
        </p>
        <p>
          Use Tab and Enter to select records, or the accessible path list below
          the graph. Arrow keys move between record tabs. Pan/zoom change only
          the view.
        </p>
        <p>
          TRACEABLE is metadata quality, not authenticated source truth. The
          default explanation is not AI-generated. No cause or fix is
          established.
        </p>
        <p>
          Protected stores remain read-only. Source references are withheld.
        </p>
      </dialog>
    </div>
  );
}
