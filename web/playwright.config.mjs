import { defineConfig } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const python = resolve(
  root,
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python",
);
export default defineConfig({
  testDir: "./e2e",
  testMatch: "*.spec.mjs",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30000,
  expect: { timeout: 7000 },
  outputDir: "../.verification/overnight/playwright-results",
  reporter: [
    ["list"],
    ["json", { outputFile: "../.verification/overnight/playwright.json" }],
  ],
  use: {
    baseURL: "http://127.0.0.1:8765",
    viewport: { width: 1440, height: 900 },
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: ["judge", "missing", "adversarial", "empty", "caps"].map(
    (profile, n) => ({
      command: `"${python}" web/e2e/backend.py --port ${8765 + n} --profile ${profile}`,
      cwd: root,
      url: `http://127.0.0.1:${8765 + n}/`,
      timeout: 20000,
      reuseExistingServer: false,
      gracefulShutdown: { signal: "SIGTERM", timeout: 2000 },
    }),
  ),
});
