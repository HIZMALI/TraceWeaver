import { afterEach, expect, it, vi } from "vitest";
import { isPublicDemo } from "../deployment";
import { requestJSON } from "../api";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  history.replaceState({}, "", "/");
});

it("recognizes only the explicit public build mode", () => {
  vi.stubEnv("MODE", "public");
  expect(isPublicDemo()).toBe(true);
});

it("keeps the ordinary production build local", () => {
  vi.stubEnv("MODE", "production");
  expect(isPublicDemo()).toBe(false);
});

it("keeps development local", () => {
  vi.stubEnv("MODE", "development");
  expect(isPublicDemo()).toBe(false);
});

it("cannot enable local capabilities through a query argument", () => {
  vi.stubEnv("MODE", "public");
  history.replaceState({}, "", "/?mode=local&public=false");
  expect(isPublicDemo()).toBe(true);
});

it("cannot enable public capabilities through a local query argument", () => {
  vi.stubEnv("MODE", "production");
  history.replaceState({}, "", "/?mode=public");
  expect(isPublicDemo()).toBe(false);
});

it("explains public backpressure without calling it a local model action", async () => {
  vi.stubEnv("MODE", "public");
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("{}", { status: 429 })),
  );
  await expect(
    requestJSON("/console/incidents", new AbortController().signal),
  ).rejects.toThrow("Public demo is busy. Try again shortly.");
});

it("preserves the local action error contract", async () => {
  vi.stubEnv("MODE", "production");
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("{}", { status: 429 })),
  );
  await expect(
    requestJSON("/console/selection", new AbortController().signal, {}),
  ).rejects.toThrow("A local action is already running");
});
