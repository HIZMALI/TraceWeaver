// Genuine native browser capture. Timed holds are reading time in the requested 115-second video.
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, copyFile, writeFile } from "node:fs/promises";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
process.env.PLAYWRIGHT_BROWSERS_PATH ??= resolve(
  root,
  ".verification/overnight/browsers",
);
const { chromium, expect } =
  await import("../web/node_modules/@playwright/test/index.mjs");
const [base, output, mode = "record"] = process.argv.slice(2);
if (
  !/^http:\/\/127\.0\.0\.1:\d+$/.test(base) ||
  !output ||
  !["record", "check-actions"].includes(mode)
)
  throw new Error(
    "Usage: record_judge_demo.mjs numeric-loopback new-output [record|check-actions]",
  );
await mkdir(output);
const record = mode === "record",
  browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1920, height: 960 },
  reducedMotion: "reduce",
  ...(record
    ? {
        recordVideo: {
          dir: resolve(output, "source"),
          size: { width: 1920, height: 960 },
        },
      }
    : {}),
});
const events = [],
  errors = [],
  foreign = [],
  posts = [],
  responses = [];
let video;
try {
  const page = await context.newPage();
  video = page.video();
  const start = performance.now();
  const elapsed = () => (performance.now() - start) / 1000;
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (new URL(r.url()).origin !== base) foreign.push(r.url());
    if (r.method() === "POST") posts.push(new URL(r.url()).pathname);
  });
  async function scene(at, title, caption, action) {
    if (record && elapsed() < at)
      await page.waitForTimeout((at - elapsed()) * 1000);
    if (record && elapsed() > at + 3)
      throw new Error("Action missed its reading-time cue: " + title);
    await action();
    events.push({ seconds: Number(elapsed().toFixed(3)), title, caption });
  }
  const details = async (name) => {
    await page.getByRole("tab", { name: new RegExp(name) }).click();
    await page
      .getByRole("tab", { name: new RegExp(name) })
      .scrollIntoViewIfNeeded();
  };
  await scene(
    0,
    "Incident and value",
    "TraceWeaver connects incident evidence in an embedded Relate graph. Synthetic demo; read-only. Connection is not cause.",
    async () => {
      await page.goto(base + "/?incident=INC-001");
      await expect(page.locator(".react-flow__edge")).toHaveCount(14);
      await expect(page.getByTestId("causal-status")).toHaveText(
        "NOT_ESTABLISHED",
      );
      expect(posts).toEqual([]);
    },
  );
  await scene(
    12,
    "Exact stored direction",
    "Payment depends on Auth. DEP-001 TARGETS Auth; that stored arrow is traversed in reverse. INCLUDES_CHANGE reaches CHG-001.",
    async () => {
      await page
        .getByRole("button", { name: "Explore the verified path" })
        .click();
      await page.getByRole("button", { name: "Focus selected paths" }).click();
      await expect(
        page.getByRole("region", { name: "Selected candidate" }),
      ).toContainText("Reverse traversal");
      await page.getByTestId("graph-canvas").scrollIntoViewIfNeeded();
    },
  );
  await scene(
    25,
    "Competing candidate",
    "DEP-002 directly targets Payment. Both deployment / target pairs remain candidates for investigation, never proven causes.",
    async () => {
      await page.getByRole("button", { name: /Focus proof DEP-002/ }).click();
      await expect(
        page.getByRole("region", { name: "Selected candidate" }),
      ).toContainText("SVC-PAYMENT");
      await page.getByTestId("graph-canvas").scrollIntoViewIfNeeded();
    },
  );
  await scene(
    37,
    "Admitted citation",
    "A server-admitted claim cites the exact GRAPH_PATH and 09:58 UTC time. The citation firewall validates support before template rendering.",
    async () => {
      await page
        .getByRole("button", { name: /Inspect claim DEPLOYMENT_BEFORE_ONSET/ })
        .first()
        .click();
      const claim = page.getByRole("region", { name: "Selected claim" });
      await expect(claim).toContainText("GRAPH_PATH");
      await expect(claim).toContainText("09:58");
      await page.locator(".inspector").evaluate((element) => {
        element.scrollTop = 0;
      });
      await claim.scrollIntoViewIfNeeded();
      await expect(claim).toBeInViewport();
    },
  );
  await scene(
    50,
    "Evidence quality",
    "EVD-001 has TRACEABLE metadata and SYNTHETIC source status. Metadata traceability does not authenticate source truth.",
    async () => {
      await details("Evidence");
      await page
        .getByRole("button", { name: "Inspect evidence EVD-001", exact: true })
        .click();
      await expect(
        page.getByRole("region", { name: "Selected evidence" }),
      ).toContainText("TRACEABLE");
      await page
        .getByRole("region", { name: "Selected evidence" })
        .scrollIntoViewIfNeeded();
    },
  );
  await scene(
    62,
    "Structured disagreement",
    "CASE-INC: HEALTHY and FAILED conflict in a matching structured context. Two DEGRADED comparisons remain UNDETERMINED.",
    async () => {
      await page.goto(base + "/?incident=CASE-INC");
      await details("Observations");
      await expect(
        page.getByRole("button", { name: /Inspect UNDETERMINED/ }),
      ).toHaveCount(2);
      await page
        .getByRole("button", { name: /Inspect CONFLICTING_OBSERVATIONS/ })
        .click();
      await page
        .getByRole("region", { name: "Selected comparison" })
        .scrollIntoViewIfNeeded();
    },
  );
  await scene(
    75,
    "Unknown stays unknown",
    "A timestamp without an explicit offset stays UNKNOWN. Missing evidence and bounded context are disclosed; no onset time is invented.",
    async () => {
      await details("Evidence");
      await page
        .getByRole("button", {
          name: "Inspect evidence CASE-E-NAIVE",
          exact: true,
        })
        .click();
      await expect(
        page.getByRole("region", { name: "Selected evidence" }),
      ).toContainText("Unknown");
      await page
        .getByRole("region", { name: "Selected evidence" })
        .scrollIntoViewIfNeeded();
    },
  );
  await scene(
    85,
    "Actual offline tools",
    "Run the fixed offline rehearsal now: 4 native tools, 23 Relate queries, 8 admitted claims and 11 citations. Both AI flags are false.",
    async () => {
      await page.goto(base + "/?incident=INC-001");
      await page
        .getByRole("button", {
          name: "Explore investigation steps",
          exact: true,
        })
        .click();
      const pending = page.waitForResponse((r) =>
        r.url().endsWith("/console/agent/rehearse"),
      );
      await page
        .getByRole("button", {
          name: "Rehearse graph investigation",
          exact: true,
        })
        .click();
      const r = await pending;
      expect(r.status()).toBe(200);
      const native = await r.json();
      expect(native.tool_trace).toHaveLength(4);
      expect(native.native_query_count).toBe(23);
      expect(native.validated_claims).toHaveLength(8);
      expect(native.validated_citation_count).toBe(11);
      expect(native.ai_directed_tools).toBe(false);
      expect(native.ai_generated_selection).toBe(false);
      responses.push(native);
      await page.getByTestId("agent-report").scrollIntoViewIfNeeded();
    },
  );
  await scene(
    99,
    "Native trace proof",
    "Inspect the executed trace_deployment step: actual stored edges and reverse traversal. This offline tool rehearsal is not AI-generated.",
    async () => {
      await page
        .getByRole("button", { name: /Inspect tool step 2 trace_deployment/ })
        .click();
      await expect(
        page.getByRole("region", { name: "Selected native tool step" }),
      ).toContainText("Reverse traversal");
      await page
        .getByRole("region", { name: "Selected native tool step" })
        .scrollIntoViewIfNeeded();
    },
  );
  await scene(
    107,
    "Limits and next checks",
    "Review remaining gaps and next checks. Cause: NOT_ESTABLISHED. External verification: NOT_PERFORMED. Local, offline, reproducible.",
    async () => {
      await details("Gaps");
      await expect(page.getByTestId("causal-status")).toHaveText(
        "NOT_ESTABLISHED",
      );
    },
  );
  if (record && elapsed() < 115)
    await page.waitForTimeout((115 - elapsed()) * 1000);
  expect(errors).toEqual([]);
  expect(foreign).toEqual([]);
  expect(posts).toEqual(["/console/agent/rehearse"]);
  await context.close();
  if (video)
    await copyFile(
      await video.path(),
      resolve(output, "native-judge-demo.webm"),
    );
  await writeFile(
    resolve(output, "capture.json"),
    JSON.stringify(
      {
        kind: "GENUINE_SILENT_BROWSER_CAPTURE",
        explanatory_captions: true,
        recorded: record,
        browser: browser.version(),
        events,
        posts,
        page_errors: errors,
        foreign_requests: foreign,
        native_report: responses[0],
      },
      null,
      2,
    ),
    { flag: "wx" },
  );
  console.log(
    JSON.stringify({
      recorded: record,
      events: events.length,
      posts,
      seconds: elapsed(),
    }),
  );
} finally {
  await context.close();
  await browser.close();
}
