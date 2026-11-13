import { defineConfig } from "@playwright/test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = process.env.TRACEWEAVER_PUBLIC_TEST_OUTPUT;
if (!output)
  throw new Error("Use npm run test:public for an owned output directory");
const external = process.env.TRACEWEAVER_PUBLIC_BASE_URL;
if (
  external &&
  !/^https:\/\/[a-z0-9.-]+$|^http:\/\/127\.0\.0\.1:\d+$/.test(external)
)
  throw new Error(
    "Public verification requires an HTTPS origin or numeric loopback test origin",
  );
const python = resolve(
  root,
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python",
);

export default defineConfig({
  testDir: "./e2e",
  testMatch: "public-demo.public.mjs",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: external ? 90000 : 30000,
  expect: { timeout: external ? 20000 : 7000 },
  outputDir: resolve(output, "results"),
  reporter: [
    ["list"],
    ["json", { outputFile: resolve(output, "playwright.json") }],
  ],
  use: {
    baseURL: external ?? "http://127.0.0.1:8775",
    viewport: { width: 1440, height: 900 },
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: external
    ? undefined
    : {
        command: `"${python}" web/e2e/public_backend.py --port 8775`,
        cwd: root,
        url: "http://127.0.0.1:8775/health",
        timeout: 20000,
        reuseExistingServer: false,
        gracefulShutdown: { signal: "SIGTERM", timeout: 2000 },
      },
});
