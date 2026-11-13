// Real installed-wheel browser proof. Live inference requires the explicit third argument.
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, writeFile } from "node:fs/promises";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(
  root,
  ".verification/overnight/browsers",
);
const { chromium, expect } =
  await import("../web/node_modules/@playwright/test/index.mjs");
const base = process.argv[2],
  live = process.argv[3] === "--live-qwen3-confirmed";
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base))
  throw new Error("Numeric loopback required");
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  const errors = [],
    posts = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (r.method() === "POST") posts.push(new URL(r.url()).pathname);
  });
  await page.goto(base + "/?incident=INC-001");
  await expect(page.locator(".react-flow__edge")).toHaveCount(14);
  await expect(page.getByTestId("causal-status")).toHaveText("NOT_ESTABLISHED");
  expect(posts).toEqual([]);
  await page.getByText("Explore investigation steps", { exact: true }).click();
  const offlineResponse = page.waitForResponse((r) =>
    r.url().endsWith("/console/agent/rehearse"),
  );
  await page.getByText("Rehearse graph investigation", { exact: true }).click();
  const response = await offlineResponse;
  expect(response.status()).toBe(200);
  const offline = await response.json();
  await expect(page.getByTestId("agent-report")).toBeVisible();
  expect(offline.tool_trace).toHaveLength(4);
  expect(offline.ai_directed_tools).toBe(false);
  await page
    .getByRole("button", { name: /Inspect tool step 2 trace_deployment/ })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected native tool step" }),
  ).toContainText("Reverse traversal");
  const result = {
    browser: browser.version(),
    real_packaged_ui: true,
    native_edges: 14,
    initial_ai_calls: 0,
    offline_tools: offline.tool_trace.map((s) => s.tool_name),
    offline_claims: offline.validated_claims.length,
    offline_citations: offline.validated_citation_count,
    live: { status: "NOT_REQUESTED", level: null },
  };
  if (live) {
    await page
      .getByText("Agent investigation (local)", { exact: true })
      .click();
    const select = page.getByLabel("Agent installed model");
    await expect(select).toBeVisible();
    const models = await select.locator("option").allTextContents();
    if (!models.includes("qwen3:8b"))
      result.live = { status: "BLOCKED_DEPENDENCY", level: "L0" };
    else {
      await select.selectOption("qwen3:8b");
      await page
        .getByLabel(
          "I confirm one local agent action for this snapshot. No download.",
        )
        .check();
      const actual = page.waitForResponse(
        (r) => r.url().endsWith("/console/agent/investigate"),
        { timeout: 110000 },
      );
      await page
        .getByText("Run confirmed local agent", { exact: true })
        .click();
      const native = await actual;
      expect(native.status()).toBe(200);
      const report = await native.json();
      await expect(page.getByTestId("agent-report")).toBeVisible();
      const factual = report.validated_claims.filter(
        (c) => c.claim_type !== "NO_CAUSAL_VERDICT",
      );
      const proof = factual.some((c) =>
        c.citations.some((x) => ["GRAPH_PATH", "EVIDENCE"].includes(x.kind)),
      );
      const level =
        report.tool_trace.length >= 2 && factual.length && proof
          ? "L3"
          : report.tool_trace.length && factual.length && proof
            ? "L2"
            : report.tool_trace.length
              ? "L1"
              : "L0";
      result.live = {
        status: report.agent_status,
        level,
        model: report.model_executed,
        tool_names: report.tool_trace.map((s) => s.tool_name),
        native_queries: report.native_query_count,
        model_interactions: report.model_interactions,
        noncaution_claims: factual.length,
        total_claims: report.validated_claims.length,
        citations: report.validated_citation_count,
        ai_directed_tools: report.ai_directed_tools,
        ai_generated_selection: report.ai_generated_selection,
        codes: report.rejection_codes,
        warnings: report.proposal_warnings,
        elapsed_ms: report.elapsed_ms,
        source_fingerprint: report.source_fingerprint,
        database_digest: report.database_digest,
      };
      await writeFile(
        resolve(root, ".verification/sprint06b/installed-live-report.json"),
        JSON.stringify(report, null, 2) + "\n",
        { flag: "wx" },
      );
      const shots = resolve(root, "docs/screenshots/sprint06b");
      await mkdir(shots, { recursive: true });
      await page.evaluate(() =>
        window.scrollTo(
          0,
          document
            .querySelector('[data-testid="agent-report"]')
            .getBoundingClientRect().top +
            scrollY -
            60,
        ),
      );
      await page.screenshot({
        path: resolve(shots, "01-installed-observed-agent.png"),
      });
      const selected = report.validated_claims.find((c) =>
        c.citations.some((x) => x.kind === "GRAPH_PATH"),
      );
      if (selected) {
        await page.getByText(/Admitted claim citations/).click();
        await page
          .locator(".agent-claim")
          .filter({ hasText: selected.statement })
          .click();
        await expect(
          page.getByRole("region", { name: "Selected claim" }),
        ).toContainText("GRAPH_PATH");
        await page.getByText("Focus selected paths", { exact: true }).click();
        await page.evaluate(() => window.scrollTo(0, 320));
        await page.screenshot({
          path: resolve(shots, "02-installed-admitted-proof.png"),
        });
      }
    }
  }
  expect(errors).toEqual([]);
  result.page_errors = errors.length;
  result.posts = posts;
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
