// CONTROLLED transport failure; graph/API/native snapshot and browser interaction are real.
import { test, expect } from "@playwright/test";
import { spawn, spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "../.."),
  base = "http://127.0.0.1:8777";
let server;
test.beforeAll(async () => {
  server = spawn(
    resolve(
      root,
      process.platform === "win32"
        ? ".venv/Scripts/python.exe"
        : ".venv/bin/python",
    ),
    ["web/e2e/recovery_backend.py", "--port", "8777"],
    {
      cwd: root,
      env: { ...process.env, PYTHONPATH: resolve(root, "src") },
      windowsHide: true,
      stdio: "ignore",
    },
  );
  await expect
    .poll(
      async () => {
        try {
          return (await fetch(base + "/health")).ok;
        } catch {
          return false;
        }
      },
      { timeout: 15000 },
    )
    .toBe(true);
});
test.afterAll(() => {
  if (server?.exitCode === null) {
    if (process.platform === "win32")
      spawnSync("taskkill", ["/PID", String(server.pid), "/T", "/F"], {
        windowsHide: true,
      });
    else server.kill("SIGTERM");
  }
});
test("CONTROLLED timeout after actual native snapshot is visibly a transport failure", async ({
  page,
}) => {
  await page.goto(base + "/?incident=INC-001");
  await expect(page.locator(".react-flow__edge")).toHaveCount(14);
  await page.getByText("Explore investigation steps", { exact: true }).click();
  await page.getByText("Rehearse graph investigation", { exact: true }).click();
  await expect(page.getByTestId("agent-report")).toBeVisible();
  await page
    .getByRole("button", { name: /Inspect tool step 2 trace_deployment/ })
    .click();
  await expect(
    page.getByRole("region", { name: "Selected native tool step" }),
  ).toBeVisible();
  await page.getByText("Agent investigation (local)", { exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Selected native tool step" }),
  ).toHaveCount(0);
  await page
    .getByLabel("Agent installed model")
    .selectOption("controlled-recovery:1");
  await page
    .getByLabel(
      "I confirm one local agent action for this snapshot. No download.",
    )
    .check();
  const response = page.waitForResponse((r) =>
    r.url().endsWith("/console/agent/investigate"),
  );
  await page.getByText("Run confirmed local agent", { exact: true }).click();
  const result = await response;
  expect(result.status()).toBe(200);
  const report = await result.json();
  expect(report.native_query_count).toBe(7);
  expect(report.tool_trace).toEqual([]);
  expect(report.rejection_codes).toEqual(["OLLAMA_TIMEOUT"]);
  expect(report.ai_generated_selection).toBe(false);
  await expect(page.getByText(/^Transport deadline reached/)).toBeVisible();
  await expect(page.getByTestId("agent-report")).toContainText(
    "AI-directed tools: false",
  );
  await expect(page.getByTestId("agent-report")).toContainText(
    "NOT_ESTABLISHED",
  );
  await expect(page.getByTestId("agent-report")).toContainText("NOT_PERFORMED");
  await expect(
    page.getByRole("region", { name: "Selected native tool step" }),
  ).toHaveCount(0);
});
