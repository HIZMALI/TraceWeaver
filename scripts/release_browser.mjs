// Actual installed-wheel browser checks. No provider fixtures or substituted graph responses.
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, writeFile } from "node:fs/promises";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
process.env.PLAYWRIGHT_BROWSERS_PATH ??= resolve(
  root,
  ".verification/overnight/browsers",
);
const { chromium, expect } =
  await import("../web/node_modules/@playwright/test/index.mjs");
const [base, output] = process.argv.slice(2);
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base) || !output)
  throw new Error(
    "Usage: release_browser.mjs numeric-loopback-origin new-output",
  );
// Existing evidence is never overwritten; this verifier is offline only.
await mkdir(output);
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
  });
  const errors = [],
    foreign = [],
    posts = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (new URL(r.url()).origin !== base) foreign.push(r.url());
    if (r.method() === "POST") posts.push(new URL(r.url()).pathname);
  });
  await page.goto(base + "/?incident=INC-001");
  await expect(page.getByTestId("causal-status")).toHaveText("NOT_ESTABLISHED");
  await expect(page.locator(".react-flow__edge")).toHaveCount(14);
  expect(posts).toEqual([]);
  await page.getByRole("button", { name: /Focus proof DEP-001/ }).click();
  await expect(
    page.getByRole("region", { name: "Selected candidate" }),
  ).toContainText("SVC-AUTH");
  await expect(
    page.getByRole("region", { name: "Selected candidate" }),
  ).toContainText("Reverse traversal");
  await page
    .getByRole("button", { name: /Inspect claim DEPLOYMENT_BEFORE_ONSET/ })
    .first()
    .click();
  await expect(
    page.getByRole("region", { name: "Selected claim" }),
  ).toContainText("GRAPH_PATH");
  await page.getByRole("tab", { name: /Evidence/ }).click();
  await page
    .getByRole("button", { name: "Inspect evidence EVD-001", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected evidence" }),
  ).toContainText("TRACEABLE");
  await page.goto(base + "/?incident=CASE-INC");
  await page.getByRole("tab", { name: /Observations/ }).click();
  await expect(
    page.getByRole("button", { name: /Inspect CONFLICTING_OBSERVATIONS/ }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("button", { name: /Inspect UNDETERMINED/ }),
  ).toHaveCount(2);
  await page.getByRole("tab", { name: /Gaps/ }).click();
  await expect(
    page.getByText("UNKNOWN_EVENT_TIMES", { exact: true }).first(),
  ).toBeVisible();
  await page.goto(base + "/?incident=INC-001");
  await page.getByText("Explore investigation steps", { exact: true }).click();
  const offlineResponse = page.waitForResponse((r) =>
    r.url().endsWith("/console/agent/rehearse"),
  );
  await page.getByText("Rehearse graph investigation", { exact: true }).click();
  const response = await offlineResponse;
  expect(response.status()).toBe(200);
  const offline = await response.json();
  expect(offline.tool_trace).toHaveLength(4);
  expect(offline.ai_directed_tools).toBe(false);
  expect(offline.model_interactions).toBe(0);
  await page
    .getByRole("button", { name: /Inspect tool step 2 trace_deployment/ })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected native tool step" }),
  ).toContainText("Reverse traversal");
  const result = {
    browser: browser.version(),
    initial_posts: 0,
    native_edges: 14,
    offline_tools: offline.tool_trace.map((t) => t.tool_name),
    offline_queries: offline.native_query_count,
    offline_claims: offline.validated_claims.length,
    offline_citations: offline.validated_citation_count,
    live: { status: "NOT_RUN", level: null },
  };
  await page.reload();
  await expect(page.getByTestId("causal-status")).toBeVisible();
  await expect(page.getByTestId("agent-report")).toHaveCount(0);
  expect(errors).toEqual([]);
  expect(foreign).toEqual([]);
  result.posts = posts;
  result.page_errors = errors.length;
  result.foreign_requests = foreign.length;
  await writeFile(
    resolve(output, "browser.json"),
    JSON.stringify(result, null, 2),
    { flag: "wx" },
  );
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
