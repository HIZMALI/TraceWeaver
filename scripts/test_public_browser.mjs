// All new evidence is written to a fresh owned directory, never historical captures.
import { spawnSync } from "node:child_process";
import { mkdtemp, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const parent = resolve(root, ".verification/public-demo");
await mkdir(parent, { recursive: true });
const output = await mkdtemp(resolve(parent, "browser-"));
const env = {
  ...process.env,
  TRACEWEAVER_PUBLIC_TEST_OUTPUT: output,
  PLAYWRIGHT_BROWSERS_PATH:
    process.env.PLAYWRIGHT_BROWSERS_PATH ??
    resolve(root, ".verification/overnight/browsers"),
};
console.log("Owned public browser evidence: " + output);
const result = spawnSync(
  process.execPath,
  [
    resolve(root, "web/node_modules/@playwright/test/cli.js"),
    "test",
    "--config",
    resolve(root, "web/playwright.public.config.mjs"),
    ...process.argv.slice(2),
  ],
  {
    cwd: resolve(root, "web"),
    env,
    stdio: "inherit",
    windowsHide: true,
    timeout: 600000,
  },
);
if (result.error) console.error("Public browser process did not complete");
process.exit(result.status ?? 1);
