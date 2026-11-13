// Historical tests use both cwd-relative and source-relative screenshot paths.
// Run the unchanged assertions in an owned current-source copy, preserving both capture families.
import { spawnSync } from "node:child_process";
import { mkdtemp, mkdir, copyFile, cp, symlink } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const parent = resolve(root, ".verification/sprint06");
await mkdir(parent, { recursive: true });
const out = await mkdtemp(resolve(parent, "browser-")),
  cwd = resolve(out, "web");
await mkdir(cwd);
const source = resolve(out, "current-source");
const inventory = spawnSync(
  "git",
  ["ls-files", "-co", "--exclude-standard", "-z"],
  {
    cwd: root,
    encoding: "utf8",
    windowsHide: true,
  },
);
if (inventory.status !== 0)
  throw new Error("Cannot inventory current source; no browser tests started");
for (const name of new Set(inventory.stdout.split("\0").filter(Boolean))) {
  const target = resolve(source, name);
  await mkdir(dirname(target), { recursive: true });
  await copyFile(resolve(root, name), target);
}
await cp(
  resolve(root, "src/traceweaver/web_static"),
  resolve(source, "src/traceweaver/web_static"),
  { recursive: true },
);
for (const relative of [
  ".venv",
  "web/node_modules",
  ".verification/overnight/browsers",
]) {
  const target = resolve(source, relative);
  await mkdir(dirname(target), { recursive: true });
  await symlink(
    resolve(root, relative),
    target,
    process.platform === "win32" ? "junction" : "dir",
  );
}
const env = {
  ...process.env,
  TRACEWEAVER_TEST_OUTPUT: out,
  PYTHONPATH: resolve(source, "src"),
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
    resolve(source, "web/playwright.sprint06.config.mjs"),
    ...process.argv.slice(2),
  ],
  { cwd, env, windowsHide: true, stdio: "inherit", timeout: 600000 },
);
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
