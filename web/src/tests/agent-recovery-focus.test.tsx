import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { AgentPanel } from "../AgentPanel";
import { bundleSchema } from "../contracts";
import { requestJSON } from "../api";
import bundle from "./fixtures/sprint06-bundle.json";
import rehearsal from "./fixtures/sprint06-rehearsal.json";
vi.mock("../api", () => ({ requestJSON: vi.fn() }));
it("clears prior transient proof on each explicit action before fetching without a page-load action", async () => {
  const start = vi.fn(),
    step = vi.fn();
  vi.mocked(requestJSON).mockImplementation(async (path) => {
    expect(start).toHaveBeenCalled();
    return path.endsWith("rehearse")
      ? rehearsal
      : {
          models: [],
          truncated: false,
          status: "UNAVAILABLE",
          code: "OLLAMA_CONNECTION_UNAVAILABLE",
        };
  });
  render(
    <AgentPanel
      bundle={bundleSchema.parse(bundle)}
      onStep={step}
      onClaim={vi.fn()}
      onActionStart={start}
    />,
  );
  expect(start).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Explore investigation steps"));
  expect(start).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Rehearse graph investigation"));
  await screen.findByTestId("agent-report");
  fireEvent.click(screen.getByRole("button", { name: /Inspect tool step 2/ }));
  expect(step).toHaveBeenCalledTimes(1);
  expect(start).toHaveBeenCalledTimes(1);
  fireEvent.click(
    screen.getByText("Agent investigation (local)", { exact: true }),
  );
  await screen.findByText(/Local Ollama unavailable/);
  expect(start).toHaveBeenCalledTimes(2);
});
