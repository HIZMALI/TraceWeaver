import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AgentPanel } from "../AgentPanel";
import { agentSchema, verifyAgent } from "../agent-contracts";
import { bundleSchema } from "../contracts";
import { requestJSON } from "../api";
import native from "./fixtures/sprint06-rehearsal.json";
import input from "./fixtures/sprint06-bundle.json";
vi.mock("../api", () => ({ requestJSON: vi.fn() }));
const request = vi.mocked(requestJSON),
  bundle = bundleSchema.parse(input);
afterEach(() => vi.resetAllMocks());
function mount() {
  const step = vi.fn(),
    claim = vi.fn();
  const ui = render(
    <AgentPanel bundle={bundle} onStep={step} onClaim={claim} />,
  );
  return { ...ui, step, claim };
}
function open() {
  fireEvent.click(
    screen.getByRole("button", { name: "Explore investigation steps" }),
  );
}

it("verifies an actual native report and its exact canonical fingerprint", async () => {
  expect((await verifyAgent(native, bundle)).tool_trace[1].subject_ids).toEqual(
    ["DEP-001", "SVC-AUTH"],
  );
});
it.each([
  ["source_fingerprint", "0".repeat(64)],
  ["incident_id", "INC-002"],
  ["ai_directed_tools", true],
  ["validated_citation_count", 0],
  ["causal_conclusion", "PROVEN"],
  ["external_verification_status", "VERIFIED"],
  ["canonical_fingerprint", "0".repeat(64)],
])(
  "rejects altered %s rather than displaying unsupported proof",
  async (field, value) => {
    await expect(
      verifyAgent({ ...native, [field]: value }, bundle),
    ).rejects.toThrow();
  },
);
it("rejects fabricated stored direction before cross-highlighting", async () => {
  const r = structuredClone(native);
  r.tool_trace[1].result.graph_paths[0].edges[0].source_id = "DEP-001";
  await expect(verifyAgent(r, bundle)).rejects.toThrow();
});
it("rejects extra provider prose in a strict report", () => {
  expect(
    agentSchema.safeParse({ ...native, diagnosis: "Model says cause" }).success,
  ).toBe(false);
});
it("never contacts capabilities or inference on initial render or expansion", () => {
  mount();
  expect(request).not.toHaveBeenCalled();
  open();
  expect(request).not.toHaveBeenCalled();
  expect(screen.getByText(/Default: Deterministic/)).toBeVisible();
});
it("executes explicit offline action with exact snapshot and no model", async () => {
  request.mockResolvedValue(native);
  mount();
  open();
  fireEvent.click(screen.getByText("Rehearse graph investigation"));
  await screen.findByTestId("agent-report");
  expect(request.mock.calls[0][0]).toBe("/console/agent/rehearse");
  expect(request.mock.calls[0][2]).toEqual({
    incident_id: "INC-001",
    options: bundle.investigation.options,
    source_fingerprint: bundle.source_fingerprint,
    intent: "TRACE_DEPENDENCY_PATH",
    confirmed: true,
  });
  expect(screen.getByText(/AI-directed tools: false/)).toBeVisible();
});
it("requires separate installed-model choice and confirmation", async () => {
  request.mockResolvedValue({
    models: ["unit-local:1"],
    truncated: false,
    status: "AVAILABLE",
    code: null,
  });
  mount();
  open();
  fireEvent.click(screen.getByText("Agent investigation (local)"));
  const run = await screen.findByText("Run confirmed local agent");
  expect(run).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Agent installed model"), {
    target: { value: "unit-local:1" },
  });
  expect(run).toBeDisabled();
  fireEvent.click(screen.getByRole("checkbox"));
  expect(run).toBeEnabled();
  expect(request).toHaveBeenCalledTimes(1);
});
it("shows unavailable models and keeps manual offline rehearsal available", async () => {
  request.mockResolvedValue({
    models: [],
    truncated: false,
    status: "UNAVAILABLE",
    code: "OLLAMA_CONNECTION_UNAVAILABLE",
  });
  mount();
  open();
  fireEvent.click(screen.getByText("Agent investigation (local)"));
  expect(await screen.findByText(/Local Ollama unavailable/)).toBeVisible();
  expect(screen.getByText("Rehearse graph investigation")).toBeEnabled();
  expect(screen.getByText("Run confirmed local agent")).toBeDisabled();
});
it("focuses only returned native step and admitted claim callbacks", async () => {
  request.mockResolvedValue(native);
  const ui = mount();
  open();
  fireEvent.click(screen.getByText("Rehearse graph investigation"));
  await screen.findByTestId("agent-report");
  fireEvent.click(screen.getByRole("button", { name: /Inspect tool step 2/ }));
  expect(ui.step.mock.calls[0][0]).toEqual(native.tool_trace[1]);
  fireEvent.click(screen.getByText(/Admitted claim citations/));
  fireEvent.click(
    screen
      .getAllByRole("button")
      .find((b) => b.textContent?.startsWith("NO_CAUSAL_VERDICT"))!,
  );
  expect(ui.claim.mock.calls[0][0].claim_type).toBe("NO_CAUSAL_VERDICT");
});
it("blocks duplicate client actions while a real request is pending", () => {
  request.mockReturnValue(new Promise(() => {}));
  mount();
  open();
  const run = screen.getByText("Rehearse graph investigation");
  fireEvent.click(run);
  fireEvent.click(run);
  expect(request).toHaveBeenCalledTimes(1);
  expect(run).toBeDisabled();
});
it("cancels a late report without displaying it as completed", async () => {
  let finish!: (v: unknown) => void;
  request.mockReturnValue(
    new Promise((r) => {
      finish = r;
    }),
  );
  mount();
  open();
  fireEvent.click(screen.getByText("Rehearse graph investigation"));
  fireEvent.click(screen.getByText("Cancel agent wait"));
  finish(native);
  await waitFor(() =>
    expect(screen.getByText("Rehearse graph investigation")).toBeEnabled(),
  );
  expect(screen.queryByTestId("agent-report")).not.toBeInTheDocument();
  expect(screen.getByText(/Server\/provider work may continue/)).toBeVisible();
});
it("rejects stale responses visibly and never substitutes an offline report", async () => {
  request.mockResolvedValue({ ...native, source_fingerprint: "0".repeat(64) });
  mount();
  open();
  fireEvent.click(screen.getByText("Rehearse graph investigation"));
  expect(await screen.findByText(/snapshot cannot be verified/)).toBeVisible();
  expect(screen.queryByTestId("agent-report")).not.toBeInTheDocument();
  expect(request).toHaveBeenCalledTimes(1);
});
