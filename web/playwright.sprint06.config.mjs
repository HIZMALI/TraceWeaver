import { defineConfig } from "@playwright/test";
import base from "./playwright.config.mjs";
import { resolve } from "node:path";
const out = process.env.TRACEWEAVER_TEST_OUTPUT;
if (!out)
  throw new Error(
    "Run npm run test:e2e to allocate an owned screenshot workspace.",
  );
export default defineConfig({
  ...base,
  outputDir: resolve(out, "results"),
  reporter: [
    ["list"],
    ["json", { outputFile: resolve(out, "playwright.json") }],
  ],
});
