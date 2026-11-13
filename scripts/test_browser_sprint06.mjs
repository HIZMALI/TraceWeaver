// Existing tests use cwd-relative screenshots: isolate their writes while testing current source.
import { spawnSync } from "node:child_process";
import { mkdtemp, mkdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const parent = resolve(root, ".verification/sprint06");
await mkdir(parent, { recursive: true });
const out = await mkdtemp(resolve(parent, "browser-")),
  cwd = resolve(out, "web");
await mkdir(cwd);
const env = {
  ...process.env,
  TRACEWEAVER_TEST_OUTPUT: out,
  PYTHONPATH: resolve(root, "src"),
  PLAYWRIGHT_BROWSERS_PATH:
    process.env.PLAYWRIGHT_BROWSERS_PATH ??
    resolve(root, ".verification/overnight/browsers"),
};
console.log("Owned browser evidence: " + out);
const result = spawnSync(
  process.execPath,
  [
    resolve(root, "web/node_modules/@playwright/test/cli.js"),
    "test",
    "--config",
    resolve(root, "web/playwright.sprint06.config.mjs"),
    ...process.argv.slice(2),
  ],
  { cwd, env, windowsHide: true, stdio: "inherit", timeout: 600000 },
);
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
