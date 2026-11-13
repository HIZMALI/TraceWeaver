// Controlled component protocol fixture; live public graph evidence is tested separately in Chromium.
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AgentPanel } from "../AgentPanel";
import { requestJSON } from "../api";
import { bundleSchema } from "../contracts";
import bundle from "./fixtures/sprint06-bundle.json";
import rehearsal from "./fixtures/sprint06-rehearsal.json";

vi.mock("../api", () => ({ requestJSON: vi.fn() }));
afterEach(() => vi.unstubAllEnvs());

it("public rehearsal uses only its snapshot-bound GET and offers no local model controls", async () => {
  vi.stubEnv("MODE", "public");
  vi.mocked(requestJSON).mockResolvedValue(rehearsal);
  render(
    <AgentPanel
      bundle={bundleSchema.parse(bundle)}
      onStep={vi.fn()}
      onClaim={vi.fn()}
    />,
  );
  expect(requestJSON).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Explore investigation steps"));
  expect(screen.queryByText("Agent investigation (local)")).toBeNull();
  fireEvent.click(screen.getByText("Rehearse graph investigation"));
  await screen.findByTestId("agent-report");
  const [path, , body] = vi.mocked(requestJSON).mock.calls[0];
  expect(path).toMatch(/^\/public\/rehearsal\/INC-001\?/);
  expect(
    new URL(path, "https://demo.test").searchParams.get("source_fingerprint"),
  ).toBe(bundle.source_fingerprint);
  expect(body).toBeUndefined();
  expect(
    vi
      .mocked(requestJSON)
      .mock.calls.every(([url]) => !url.startsWith("/console/")),
  ).toBe(true);
});
