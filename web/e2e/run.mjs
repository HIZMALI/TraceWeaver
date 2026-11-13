import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const web = resolve(dirname(fileURLToPath(import.meta.url)), "..");
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(
  web,
  "../.verification/overnight/browsers",
);
const result = spawnSync(
  process.execPath,
  [
    resolve(web, "node_modules/@playwright/test/cli.js"),
    "test",
    ...process.argv.slice(2),
  ],
  {
    cwd: web,
    env: process.env,
    stdio: "inherit",
    windowsHide: true,
    timeout: 600000,
  },
);
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
