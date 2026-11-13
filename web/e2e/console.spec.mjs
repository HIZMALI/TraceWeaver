import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const shots = resolve("../docs/screenshots");
async function open(page, id = "INC-001", base = "") {
  await page.goto(`${base}/?incident=${id}`);
  await expect(page.getByTestId("causal-status")).toHaveText("NOT_ESTABLISHED");
  await expect(page.locator(".react-flow__edge").first()).toBeAttached();
}
async function shot(page, name) {
  await mkdir(shots, { recursive: true });
  await page.evaluate(() => {
    document.activeElement?.blur();
    window.scrollTo(0, 0);
  });
  await page.screenshot({
    path: resolve(shots, name + ".png"),
    fullPage: true,
  });
}
test.afterEach(async ({ page }) => {
  await expect(page.locator("body")).not.toContainText("Internal React error");
});

test("actual native INC-001 arrows and competing candidates", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await open(page);
  await expect(page.locator(".react-flow__edge")).toHaveCount(14);
  await expect(
    page.getByRole("button", {
      name: "Inspect candidate DEP-001 on SVC-AUTH",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Inspect candidate DEP-002 on SVC-PAYMENT",
      exact: true,
    }),
  ).toBeVisible();
  expect(
    await page
      .locator(
        '[aria-label="TARGETS stored DEP-001 to SVC-AUTH, traversed in reverse"]',
      )
      .count(),
  ).toBe(1);
  await shot(page, "01-connected-context");
  expect(errors).toEqual([]);
});
test("candidate shows reverse traversal and included change proof", async ({
  page,
}) => {
  await open(page);
  await page
    .getByRole("button", {
      name: "Inspect candidate DEP-001 on SVC-AUTH",
      exact: true,
    })
    .click();
  const inspector = page.getByRole("complementary", {
    name: "Proof inspector",
  });
  await expect(
    inspector.getByRole("heading", { name: "DEP-001", exact: true }),
  ).toBeVisible();
  await expect(inspector).toContainText("CHG-001");
  await expect(inspector).toContainText("Reverse traversal");
  await expect(
    page.getByRole("button", { name: "Focus selected paths" }),
  ).toBeVisible();
});
test("actual admitted claim and typed citation drilldown", async ({ page }) => {
  await open(page);
  await page
    .getByRole("button", { name: /Inspect claim DEPLOYMENT_BEFORE_ONSET/ })
    .click();
  const claim = page.getByRole("region", { name: "Selected claim" });
  await expect(claim).toContainText("TEMPORAL");
  await expect(claim).toContainText("09:58");
  await expect(
    page.locator(".react-flow__node.selected").first(),
  ).toBeAttached();
  await shot(page, "02-claim-proof");
});
test("CASE-INC preserves one conflict and two undetermined pairs", async ({
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
  ).toContainText("CASE-API");
  await shot(page, "03-structured-disagreement");
});
test("naive timestamp remains unknown with warning", async ({ page }) => {
  await open(page, "CASE-INC");
  await page.getByRole("tab", { name: /Evidence/ }).click();
  await page
    .getByRole("button", { name: "Inspect evidence CASE-E-NAIVE", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected evidence" }),
  ).toContainText("Unknown");
});
test("orphan evidence has no invented observed service", async ({ page }) => {
  await open(page, "CASE-INC");
  await page.getByRole("tab", { name: /Evidence/ }).click();
  await page
    .getByRole("button", {
      name: "Inspect evidence CASE-E-ORPHAN",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected evidence" }),
  ).toContainText("INCOMPLETE");
  await expect(page.locator(".react-flow__node.selected")).toHaveCount(2);
});
test("gaps and next checks are genuine server outputs", async ({ page }) => {
  await open(page, "CASE-INC");
  await page.getByRole("tab", { name: /Gaps/ }).click();
  await expect(page.getByRole("tabpanel")).toContainText("Next checks");
  await shot(page, "04-gaps-next-checks");
});
test("visual node filter changes only visible graph", async ({ page }) => {
  await open(page);
  await page
    .getByRole("combobox", { name: "Node kind", exact: true })
    .selectOption("Evidence");
  await expect(page.locator(".react-flow__node")).toHaveCount(4);
  await expect(page.locator(".react-flow__edge")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: /Inspect candidate DEP-001/ }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reset filters", exact: true })
    .click();
  await expect(page.locator(".react-flow__edge")).toHaveCount(14);
});
test("edge type filter retains actual TARGETS edges only", async ({ page }) => {
  await open(page);
  await page
    .getByRole("combobox", { name: "Edge type", exact: true })
    .selectOption("TARGETS");
  await expect(page.locator(".react-flow__edge")).toHaveCount(2);
});
test("time filter excludes unknown and before deployments from AFTER", async ({
  page,
}) => {
  await open(page, "CASE-INC");
  await page
    .getByRole("combobox", { name: "Time class", exact: true })
    .selectOption("AFTER");
  await expect(
    page.locator('.react-flow__node[data-id="CASE-DEP-AFTER"]'),
  ).toHaveCount(1);
  await expect(
    page.locator('.react-flow__node[data-id="CASE-DEP-INVALID"]'),
  ).toHaveCount(0);
});
test("deep link restores actual selected evidence", async ({ page }) => {
  await page.goto("/?incident=CASE-INC&selection=evidence:CASE-E-NAIVE");
  await expect(
    page.getByRole("region", { name: "Selected evidence" }),
  ).toContainText("CASE-E-NAIVE");
});
test("stale deep link warns without ghost proof", async ({ page }) => {
  await page.goto("/?incident=INC-001&selection=evidence:CASE-E-FAILED");
  await expect(page.getByTestId("causal-status")).toBeVisible();
  await expect(
    page.getByRole("complementary", { name: "Proof inspector" }),
  ).toContainText("Selection unavailable in this returned scope");
  await expect(page.locator(".react-flow__node.selected")).toHaveCount(0);
});
test("back and forward preserve incident scope", async ({ page }) => {
  await open(page);
  const nav = page.getByRole("navigation", { name: "Returned incidents" });
  await nav.getByRole("button").filter({ hasText: "CASE-INC" }).click();
  await expect(
    page.getByRole("button", { name: /Inspect candidate CASE-DEP-BEFORE/ }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("button", { name: /Inspect candidate DEP-001/ }),
  ).toBeVisible();
  await page.goForward();
  await expect(
    page.getByRole("button", { name: /Inspect candidate CASE-DEP-BEFORE/ }),
  ).toBeVisible();
});
test("rapid incident navigation never keeps prior candidate scope", async ({
  page,
}) => {
  await open(page);
  await page.evaluate(() => {
    history.pushState({}, "", "/?incident=CASE-INC");
    dispatchEvent(new PopStateEvent("popstate"));
    history.pushState({}, "", "/?incident=INC-001");
    dispatchEvent(new PopStateEvent("popstate"));
  });
  await expect(
    page.getByRole("button", { name: /Inspect candidate DEP-001/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Inspect candidate CASE-DEP/ }),
  ).toHaveCount(0);
});
test("no model request on ordinary load or GET query injection", async ({
  page,
}) => {
  const posts = [];
  page.on("request", (r) => {
    if (r.method() === "POST") posts.push(r.url());
  });
  await page.goto("/?incident=INC-001&mode=ollama&model=qwen3:8b");
  await expect(page.getByTestId("causal-status")).toBeVisible();
  expect(posts).toEqual([]);
});
test("safe actual native adversarial store withholds HTML/private metadata", async ({
  page,
}) => {
  await open(page, "INC-001", "http://127.0.0.1:8767");
  expect(await page.evaluate(() => window.__injected)).toBeUndefined();
  await expect(page.locator("h1")).toHaveText("Metadata withheld");
  expect(await page.locator("body").innerText()).not.toContain("onerror");
});
test("real missing store shows generic recoverable error", async ({ page }) => {
  await page.goto("http://127.0.0.1:8766/?incident=INC-001");
  await expect(page.locator("h1")).toContainText("Graph database unavailable");
  await shot(page, "06-safe-unavailable");
});
test("actual missing incident shows 404 without placeholder facts", async ({
  page,
}) => {
  await page.goto("/?incident=DOES-NOT-EXIST");
  await expect(page.locator("h1")).toHaveText("Incident not found");
  await expect(page.getByTestId("graph-canvas")).toHaveCount(0);
});
test("insufficient evidence abstains using a real isolated Relate store", async ({
  page,
}) => {
  await open(page, "EV-NONE", "http://127.0.0.1:8768");
  await expect(page.locator("body")).toContainText("ABSTAINED");
});
test("actual high degree store visibly discloses caps", async ({ page }) => {
  await open(page, "EV-CAPS", "http://127.0.0.1:8769");
  await expect(page.locator(".scope-banner")).toContainText("Source caps reached");
  await expect(page.locator(".graph-footer")).toContainText("Display cap omitted");
  expect(await page.locator(".react-flow__node").count()).toBeLessThanOrEqual(
    300,
  );
});
test("keyboard tabs and accessible path alternative work", async ({ page }) => {
  await open(page);
  await page.getByRole("tab", { name: /Candidates/ }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: /Evidence/ })).toBeFocused();
  await page
    .getByText("Accessible path list · traversal order and stored directions", {
      exact: true,
    })
    .click();
  await expect(page.locator(".accessible-paths")).toContainText("TARGETS");
});
test("help dialog manages keyboard focus and escape", async ({ page }) => {
  await open(page);
  await page.getByRole("button", { name: "About this console" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
});
test("axe desktop has no accessibility violations", async ({ page }) => {
  await open(page);
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
for (const [name, width, height] of [
  ["desktop", 1440, 900],
  ["compact", 1024, 768],
  ["tablet", 768, 1024],
  ["phone", 390, 844],
]) {
  test(`responsive ${name} ${width}x${height} without page overflow`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height });
    await open(page);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    if (width < 900) {
      await page
        .getByRole("button", { name: "Inspector", exact: true })
        .click();
      await expect(
        page.getByRole("complementary", { name: "Proof inspector" }),
      ).toBeVisible();
      await page.getByRole("button", { name: "Details", exact: true }).click();
      await expect(page.getByRole("tab", { name: /Candidates/ })).toBeVisible();
    }
    if (name === "phone") await shot(page, "05-phone-records");
  });
}
test("200 percent equivalent reflow retains readable controls", async ({
  page,
}) => {
  await page.setViewportSize({ width: 720, height: 450 });
  await open(page);
  await page.getByRole("button", { name: "Details", exact: true }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
});
