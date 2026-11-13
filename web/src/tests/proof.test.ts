// Recorded native API inputs are unit-test data, never browser/backend substitutes.
import { describe, expect, it, vi } from "vitest";
import incInput from "./fixtures/INC-001.json";
import caseInput from "./fixtures/CASE-INC.json";
import {
  bundleSchema,
  canonical,
  pathSchema,
  validateScope,
  verifyBundle,
} from "../contracts";
import {
  graphFromBundle,
  selectionPaths,
  selectionExists,
  filterGraph,
  defaultFilters,
  edgeKey,
  candidateKey,
  pairKey,
} from "../graph";
import {
  defaults,
  parseNavigation,
  navigationURL,
  utcText,
} from "../navigation";
import { boundedJSON, requestJSON, getBundle } from "../api";

const inc = () => bundleSchema.parse(structuredClone(incInput));
const cases = () => bundleSchema.parse(structuredClone(caseInput));
describe("native-recorded proof input contracts", () => {
  it.each([incInput, caseInput])(
    "verifies Python canonical digest and semantic scope",
    async (raw) => {
      expect((await verifyBundle(raw)).read_only).toBe(true);
    },
  );
  it("rejects changed display data without an updated digest", async () => {
    const b = inc();
    b.investigation.title.text = "Changed";
    await expect(verifyBundle(b)).rejects.toThrow("snapshot");
  });
  it("rejects an explanation from another incident", () => {
    const b = inc();
    b.explanation.incident_id = "CASE-INC";
    expect(() => validateScope(b)).toThrow("snapshot");
  });
  it("rejects source fingerprint mismatch", () => {
    const b = inc();
    b.source_fingerprint = "0".repeat(64);
    expect(() => validateScope(b)).toThrow("snapshot");
  });
  it("rejects candidate scope from another incident", () => {
    const b = inc();
    b.investigation.candidates[0].graph_paths[0].node_ids[0] = "CASE-INC";
    expect(() => validateScope(b)).toThrow("scope");
  });
  it("rejects valid evidence identity on a forged path", () => {
    const b = inc();
    b.investigation.evidence[0].graph_paths[0].node_ids[0] = "CASE-INC";
    expect(() => validateScope(b)).toThrow("scope");
  });
  it("rejects a citation path with a valid identity but wrong target", () => {
    const b = inc();
    const x = b.explanation.claims.find(
      (c) => c.claim_type === "DEPLOYMENT_CONNECTED",
    )!.citations[0];
    x.graph_path!.node_ids[1] = "SVC-AUTH";
    expect(() => validateScope(b)).toThrow("Citation path");
  });
  it("rejects a citation with the wrong event time", () => {
    const b = inc();
    b.explanation.claims.find(
      (c) => c.claim_type === "DEPLOYMENT_BEFORE_ONSET",
    )!.citations[1].event_utc = "2026-11-10T10:06:00Z";
    expect(() => validateScope(b)).toThrow("Citation time");
  });
  it("rejects forged provenance status", () => {
    const b = inc();
    b.explanation.claims
      .find((c) => c.claim_type === "EVIDENCE_REPORTED")!
      .citations.find((c) => c.kind === "PROVENANCE")!.provenance_status =
      "INVALID";
    expect(() => validateScope(b)).toThrow("provenance");
  });
  it("rejects root cause language in the structured verdict", () => {
    const b: unknown = {
      ...inc(),
      explanation: { ...inc().explanation, causal_conclusion: "PROVEN" },
    };
    expect(() => bundleSchema.parse(b)).toThrow();
  });
  it("rejects raw source references", () => {
    const b = inc() as unknown as {
      explanation: { claims: { citations: { source_ref: unknown }[] }[] };
    };
    b.explanation.claims[0].citations[0].source_ref = "https://private.invalid";
    expect(() => bundleSchema.parse(b)).toThrow();
  });
  it("does not accept an AI result as deterministic output", () => {
    const b = inc();
    b.explanation.ai_generated_selection = true;
    expect(() => validateScope(b)).toThrow("deterministic");
  });
  it("rejects unknown root fields", () => {
    expect(() =>
      bundleSchema.parse({ ...inc(), raw_properties: { secret: "unit-only" } }),
    ).toThrow();
  });
  it("rejects reversed stored TARGETS endpoints", () => {
    const p = structuredClone(inc().investigation.candidates[0].graph_paths[0]);
    const edge = p.edges.at(-1)!;
    [edge.source_id, edge.target_id] = [edge.target_id, edge.source_id];
    expect(() => pathSchema.parse(p)).toThrow("direction");
  });
  it("rejects REVERSE on HAS_EVIDENCE", () => {
    const p = inc().investigation.evidence[0].graph_paths[0];
    p.edges[0].traversal_direction = "REVERSE";
    expect(() => pathSchema.parse(p)).toThrow();
  });
  it("rejects path length mismatch", () => {
    const p = inc().investigation.evidence[0].graph_paths[0];
    p.node_ids.push("EXTRA");
    expect(() => pathSchema.parse(p)).toThrow("length");
  });
  it("canonicalizes Unicode exactly like Python ASCII JSON", () => {
    expect(canonical({ z: "ö😀", a: 1 })).toBe(
      '{\n  "a": 1,\n  "z": "\\u00f6\\ud83d\\ude00"\n}\n',
    );
  });
});
describe("returned graph and selection", () => {
  it("keeps native stable IDs and persisted TARGETS direction", () => {
    const g = graphFromBundle(inc());
    const e = g.edges.find(
      (e) => e.type === "TARGETS" && e.source === "DEP-001",
    );
    expect(e).toMatchObject({ target: "SVC-AUTH", reverse: true });
    expect(g.nodes.find((n) => n.id === "DEP-001")?.kind).toBe("Deployment");
  });
  it("deduplicates repeated citation/source edges", () => {
    const g = graphFromBundle(inc());
    expect(g.edges).toHaveLength(14);
    expect(new Set(g.edges.map((e) => e.id)).size).toBe(14);
  });
  it("rejects an inferred Service kind when native labels differ", () => {
    const b = inc();
    b.investigation.entity_kinds["SVC-AUTH"] = "Evidence";
    expect(() => graphFromBundle(b)).toThrow("kind");
  });
  it("retains both paths for candidate and change drilldown", () => {
    const b = inc(),
      c = b.investigation.candidates[0];
    expect(
      selectionPaths(
        b,
        "candidate:" + candidateKey(c.deployment_id, c.target_service_id),
      ),
    ).toEqual([...c.graph_paths, ...c.changes.map((x) => x.graph_path)]);
  });
  it("highlights every returned path in a selected claim", () => {
    const b = cases(),
      c = b.explanation.claims.find(
        (c) => c.citations.filter((x) => x.graph_path).length > 0,
      )!;
    expect(selectionPaths(b, "claim:" + c.claim_id)).toEqual(
      c.citations.flatMap((x) => (x.graph_path ? [x.graph_path] : [])),
    );
  });
  it("keeps an orphan as its actual incident/evidence path", () => {
    const b = cases(),
      p = selectionPaths(b, "evidence:CASE-E-ORPHAN");
    expect(p).toHaveLength(1);
    expect(p[0].node_ids).toEqual(["CASE-INC", "CASE-E-ORPHAN"]);
  });
  it("comparison selection uses only its actual matched service", () => {
    const b = cases(),
      c = b.investigation.contradictions.find(
        (c) => c.classification === "CONFLICTING_OBSERVATIONS",
      )!;
    const p = selectionPaths(b, "comparison:" + pairKey(c.evidence_ids));
    expect(p).toHaveLength(2);
    expect(p.every((p) => p.node_ids.at(-1) === "CASE-API")).toBe(true);
  });
  it("unknown deep link has no invented graph selection", () => {
    const b = inc();
    expect(
      selectionExists(b, graphFromBundle(b), "evidence:CASE-E-FAILED"),
    ).toBe(false);
    expect(selectionPaths(b, "node:MISSING")).toEqual([]);
  });
  it("edge selection compares exact type and persisted endpoints", () => {
    const b = inc(),
      g = graphFromBundle(b),
      e = g.edges.find((e) => e.type === "TARGETS")!;
    expect(selectionPaths(b, "edge:" + e.id).length).toBeGreaterThan(0);
    expect(
      selectionPaths(
        b,
        "edge:" +
          edgeKey({ type: e.type, source_id: e.target, target_id: e.source }),
      ),
    ).toEqual([]);
  });
  it.each(["Evidence", "Deployment", "Service"])(
    "visual %s filter retains no dangling edges",
    (kind) => {
      const b = cases(),
        g = filterGraph(graphFromBundle(b), b, { ...defaultFilters, kind });
      expect(g.nodes.every((n) => n.kind === kind)).toBe(true);
      expect(
        g.edges.every(
          (e) =>
            g.nodes.some((n) => n.id === e.source) &&
            g.nodes.some((n) => n.id === e.target),
        ),
      ).toBe(true);
    },
  );
  it("AFTER filter never labels unknown evidence as BEFORE", () => {
    const b = cases(),
      g = filterGraph(graphFromBundle(b), b, {
        ...defaultFilters,
        temporal: "AFTER",
      });
    expect(g.nodes.some((n) => n.id === "CASE-E-NAIVE")).toBe(false);
  });
  it("provenance filter keeps source truth unverified", () => {
    const b = inc(),
      g = filterGraph(graphFromBundle(b), b, {
        ...defaultFilters,
        provenance: "TRACEABLE",
      });
    expect(
      g.nodes
        .filter((n) => n.kind === "Evidence")
        .every(
          (n) =>
            b.investigation.evidence.find((e) => e.evidence_id === n.id)
              ?.provenance_status === "TRACEABLE",
        ),
    ).toBe(true);
    expect(b.explanation.external_verification_status).toBe("NOT_PERFORMED");
  });
  it("visual filters never modify source or its digest", () => {
    const b = cases(),
      before = canonical(b);
    filterGraph(graphFromBundle(b), b, {
      ...defaultFilters,
      kind: "Evidence",
      assessment: "INVESTIGATE",
    });
    expect(canonical(b)).toBe(before);
  });
  it("layout remains stable between normalization runs", () => {
    const b = cases();
    expect(graphFromBundle(b)).toEqual(graphFromBundle(b));
  });
});
describe("bounded navigation, time and transport", () => {
  it.each([
    ["INC-001", { ...defaults, max_evidence: 1 }, incInput, false],
    ["INC-001", defaults, caseInput, false],
    ["INC-001", defaults, incInput, true],
  ] as const)(
    "binds coherent native response to requested incident/options %#",
    async (id, options, body, valid) => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(new Response(JSON.stringify(body))),
      );
      try {
        const response = getBundle(id, options, new AbortController().signal);
        if (valid)
          expect((await response).investigation.incident_id).toBe("INC-001");
        else await expect(response).rejects.toThrow("requested");
      } finally {
        vi.unstubAllGlobals();
      }
    },
  );
  it("defaults to the actual documented demo", () => {
    expect(parseNavigation("")).toEqual({
      incident: "INC-001",
      selection: "",
      options: defaults,
      warnings: [],
    });
  });
  it.each(["-1", "1441", "1e3", "0 OR 1=1", ""])(
    "rejects invalid window %s",
    (value) => {
      const n = parseNavigation("?pre_minutes=" + encodeURIComponent(value));
      expect(n.options.pre_minutes).toBe(120);
      expect(n.warnings).toHaveLength(1);
    },
  );
  it("accepts zero width windows without guessing time", () => {
    expect(
      parseNavigation("?pre_minutes=0&post_minutes=0").options,
    ).toMatchObject({ pre_minutes: 0, post_minutes: 0 });
    expect(utcText({ utc: null, warning_code: "TIME_NAIVE" })).toBe(
      "Unknown · TIME_NAIVE",
    );
  });
  it("rejects Cypher/HTML incident parameters", () => {
    const n = parseNavigation(
      "?incident=" + encodeURIComponent("<script> MATCH (n)"),
    );
    expect(n.incident).toBe("INC-001");
    expect(n.warnings).toHaveLength(1);
  });
  it("round trips incident, selection and effective options", () => {
    const n = parseNavigation(
      "?incident=CASE-INC&selection=evidence:CASE-E-NAIVE&max_evidence=5",
    );
    expect(parseNavigation(navigationURL(n).slice(1))).toEqual(n);
  });
  it("rejects invalid selection types and control characters", () => {
    expect(parseNavigation("?selection=script:alert").selection).toBe("");
    expect(parseNavigation("?selection=node:bad%0A").selection).toBe("");
  });
  it("limits deep JSON before parsing", () => {
    expect(() => boundedJSON("[".repeat(21) + "0" + "]".repeat(21))).toThrow(
      "depth",
    );
  });
  it("ignores quoted brackets when counting depth", () => {
    expect(boundedJSON('{"text":"[[[\\\""}')).toEqual({ text: '[[["' });
  });
  it("limits huge strings before parsing", () => {
    expect(() =>
      boundedJSON(JSON.stringify("x".repeat(2 * 1024 * 1024))),
    ).toThrow("byte");
  });
  it("reports safe server errors without exposing response prose", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("private path", { status: 503 })),
    );
    try {
      await expect(
        requestJSON("/unit", new AbortController().signal),
      ).rejects.toThrow("Graph database unavailable");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
