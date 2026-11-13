import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

for (const [width, height, name] of [
  [1440, 900, "desktop"],
  [1024, 768, "tablet"],
  [390, 844, "phone"],
  [720, 900, "200-percent-reflow"],
]) {
  test(`sprint07 first action and exact native path at ${name}`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const posts = [];
    page.on("request", (r) => {
      if (r.method() === "POST") posts.push(r.url());
    });
    await page.goto("/?incident=INC-001");
    const start = page.getByRole("button", {
      name: "Explore the verified path",
    });
    await expect(start).toBeInViewport();
    await start.focus();
    await page.keyboard.press("Enter");
    if (width < 900)
      await page
        .getByRole("button", { name: "Inspector", exact: true })
        .click();
    const proof = page.getByRole("region", { name: "Selected candidate" });
    await expect(proof).toContainText("CHG-001");
    await expect(proof).toContainText("Reverse traversal");
    if (width < 900)
      await page.getByRole("button", { name: "Graph", exact: true }).click();
    await expect(page.locator(".react-flow__edge")).toHaveCount(14);
    await expect(
      page.locator(
        '[aria-label="TARGETS stored DEP-001 to SVC-AUTH, traversed in reverse"]',
      ),
    ).toHaveCount(1);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    expect(posts).toEqual([]);
    const scan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(scan.violations).toEqual([]);
    const shots = resolve("../docs/screenshots/sprint07");
    await mkdir(shots, { recursive: true });
    await page.screenshot({ path: resolve(shots, name + ".png") });
  });
}
