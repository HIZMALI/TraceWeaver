// Real public ASGI/native Relate browser flow. No graph intercepts or simulated provider results.
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { resolve } from "node:path";

const output = process.env.TRACEWEAVER_PUBLIC_TEST_OUTPUT;
test.beforeEach(async ({ page, baseURL }) => {
  const errors = [],
    foreign = [],
    posts = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (new URL(r.url()).origin !== baseURL)
      foreign.push(new URL(r.url()).origin);
    if (r.method() !== "GET") posts.push(new URL(r.url()).pathname);
  });
  page.publicAudit = { errors, foreign, posts };
});
test.afterEach(async ({ page }) => {
  expect(page.publicAudit.errors).toEqual([]);
  expect(page.publicAudit.foreign).toEqual([]);
  expect(page.publicAudit.posts).toEqual([]);
});

async function open(page, incident = "INC-001", extra = "") {
  await page.goto(`/?incident=${incident}${extra}`);
  await expect(page.getByTestId("causal-status")).toHaveText("NOT_ESTABLISHED");
  await expect(
    page.getByRole("region", { name: "Public demo limits" }),
  ).toBeVisible();
  await expect(page.locator(".react-flow__edge").first()).toBeAttached();
}

test("public native INC-001 exact arrows, candidates and disabled local controls", async ({
  page,
}) => {
  await open(page);
  await expect(page.locator(".react-flow__edge")).toHaveCount(14);
  await expect(
    page.getByRole("button", { name: /Focus proof DEP-002/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Explore the verified path" }).click();
  const candidate = page.getByRole("region", { name: "Selected candidate" });
  await expect(candidate).toContainText("DEP-001");
  await expect(candidate).toContainText("Reverse traversal");
  await expect(candidate).toContainText("CHG-001");
  await expect(
    page.getByText("Compare with local AI selection", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Agent investigation (local)", { exact: true }),
  ).toHaveCount(0);
  await page.screenshot({
    path: resolve(output, "public-native-proof.png"),
    fullPage: true,
  });
});

test("public citation inspection uses existing admitted graph and temporal support", async ({
  page,
}) => {
  await open(page);
  await page
    .getByRole("button", { name: /Inspect claim DEPLOYMENT_BEFORE_ONSET/ })
    .first()
    .click();
  const claim = page.getByRole("region", { name: "Selected claim" });
  await expect(claim).toContainText("GRAPH_PATH");
  await expect(claim).toContainText("TEMPORAL");
  await expect(claim).toContainText("09:58");
  await expect(
    page.locator(".react-flow__node.selected").first(),
  ).toBeAttached();
});

test("public offline tools execute 23 genuine native queries without model or POST calls", async ({
  page,
}) => {
  await open(page);
  await page.getByText("Explore investigation steps", { exact: true }).click();
  await expect(
    page.getByText("Agent investigation (local)", { exact: true }),
  ).toHaveCount(0);
  const responsePromise = page.waitForResponse((r) =>
    r.url().includes("/public/rehearsal/INC-001?"),
  );
  await page.getByText("Rehearse graph investigation", { exact: true }).click();
  const response = await responsePromise;
  expect(response.request().method()).toBe("GET");
  expect(response.status()).toBe(200);
  const report = await response.json();
  expect(report.model_interactions).toBe(0);
  expect(report.ai_directed_tools).toBe(false);
  expect(report.ai_generated_selection).toBe(false);
  expect(report.tool_trace).toHaveLength(4);
  expect(report.native_query_count).toBe(23);
  expect(report.validated_claims).toHaveLength(8);
  expect(report.validated_citation_count).toBe(11);
  await expect(page.getByTestId("agent-report")).toBeVisible();
  await page
    .getByRole("button", { name: /Inspect tool step 2 trace_deployment/ })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected native tool step" }),
  ).toContainText("Reverse traversal");
  await page.screenshot({
    path: resolve(output, "public-native-tools.png"),
    fullPage: true,
  });
});

test("public CASE-INC has one conflict and two undetermined comparisons", async ({
  page,
}) => {
  await open(page, "CASE-INC");
  await page.getByRole("tab", { name: /Observations/ }).click();
  await expect(
    page.getByRole("button", { name: /Inspect CONFLICTING_OBSERVATIONS/ }),
  ).toHaveCount(1);
  await expect(
    page.getByRole("button", { name: /Inspect UNDETERMINED/ }),
  ).toHaveCount(2);
  await page
    .getByRole("button", { name: /Inspect CONFLICTING_OBSERVATIONS/ })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected comparison" }),
  ).toBeVisible();
  await page.screenshot({
    path: resolve(output, "public-case-comparisons.png"),
    fullPage: true,
  });
});

test("public deep linking and back navigation preserve real incident scope", async ({
  page,
}) => {
  await open(page, "INC-001", "&selection=node%3ADEP-001");
  await expect(
    page.getByRole("complementary", { name: "Proof inspector" }),
  ).toContainText("DEP-001");
  await page.getByRole("button", { name: /CASE-INC Synthetic/ }).click();
  await expect(page).toHaveURL(/incident=CASE-INC/);
  await expect(page.getByTestId("causal-status")).toHaveText("NOT_ESTABLISHED");
  await page.goBack();
  await expect(page).toHaveURL(/incident=INC-001/);
  await expect(page.locator(".react-flow__edge")).toHaveCount(14);
});

test("public timeline, evidence and gaps retain unknown/source truth boundaries", async ({
  page,
}) => {
  await open(page, "CASE-INC");
  await page.getByRole("tab", { name: /Evidence/ }).click();
  await expect(
    page.getByRole("button", { name: /Inspect evidence CASE-E-NAIVE/ }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: /Inspect evidence CASE-E-NAIVE/ })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected evidence" }),
  ).toContainText("Unknown");
  await page.getByRole("tab", { name: /Timeline/ }).click();
  await expect(page.getByRole("tabpanel")).toBeVisible();
  await page.getByRole("tab", { name: /Gaps/ }).click();
  await expect(
    page.getByText("UNKNOWN_EVENT_TIMES", { exact: true }).first(),
  ).toBeVisible();
});

test("public server itself rejects model, write and legacy API endpoints", async ({
  request,
}) => {
  for (const path of [
    "/console/models/capabilities",
    "/console/selection",
    "/console/agent/rehearse",
    "/console/agent/investigate",
    "/ingest",
    "/cypher",
    "/upload",
  ]) {
    const response = await request.post(path, { data: { confirmed: true } });
    expect(response.status()).toBe(404);
    expect(await response.json()).toEqual({ detail: "Not found" });
  }
  for (const path of [
    "/openapi.json",
    "/docs",
    "/incidents",
    "/data/traceweaver.rl",
  ]) {
    expect((await request.get(path)).status()).toBe(404);
  }
  expect(
    (await request.post("/console/incidents", { data: {} })).status(),
  ).toBe(405);
});

test("public assets, security headers and query admission are genuine", async ({
  page,
  request,
  baseURL,
}) => {
  const response = await page.goto("/?incident=INC-001");
  expect(response.status()).toBe(200);
  expect(response.headers()["content-security-policy"]).toContain(
    "connect-src 'self'",
  );
  expect(response.headers()["x-frame-options"]).toBe("DENY");
  const assets = await page
    .locator('script[src],link[rel="stylesheet"]')
    .evaluateAll((elements) =>
      elements.map((e) => e.getAttribute("src") ?? e.getAttribute("href")),
    );
  expect(assets).toHaveLength(2);
  for (const asset of assets) {
    const url = new URL(asset, baseURL);
    expect(url.origin).toBe(baseURL);
    if (baseURL.startsWith("https:")) expect(url.protocol).toBe("https:");
    expect((await request.get(url.href)).status()).toBe(200);
  }
  const bad = await request.get("/incidents/INC-001/dashboard?mode=ollama");
  expect(bad.status()).toBe(422);
  expect(await bad.json()).toEqual({ detail: "Invalid public options" });
});

for (const [name, width, height] of [
  ["desktop", 1440, 900],
  ["tablet", 768, 1024],
  ["phone", 390, 844],
]) {
  test(`public ${name} responsive keyboard and accessibility`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height });
    await open(page);
    await page
      .getByRole("button", { name: "Explore the verified path" })
      .focus();
    await page.keyboard.press("Enter");
    if (width < 900)
      await page
        .getByRole("button", { name: "Inspector", exact: true })
        .click();
    await expect(
      page.getByRole("region", { name: "Selected candidate" }),
    ).toContainText("DEP-001");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(result.violations).toEqual([]);
    await page.screenshot({
      path: resolve(output, `public-${name}.png`),
      fullPage: true,
    });
  });
}
