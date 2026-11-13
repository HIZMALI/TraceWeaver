// Controlled component tests, distinct from the real-model browser evidence.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { LocalSelection } from "../LocalSelection";
import { bundleSchema } from "../contracts";
import input from "./fixtures/INC-001.json";
import { requestJSON } from "../api";
vi.mock("../api", () => ({ requestJSON: vi.fn() }));
const request = vi.mocked(requestJSON),
  bundle = bundleSchema.parse(input);
beforeEach(() => {
  request.mockReset();
});
async function choose() {
  fireEvent.click(
    screen.getByRole("button", { name: "Compare with local AI selection" }),
  );
  await screen.findByRole("combobox");
  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "unit-local:1" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
}
const caps = {
  models: ["unit-local:1"],
  truncated: false,
  status: "AVAILABLE",
  code: null,
};
it("never probes capabilities on mount", () => {
  render(<LocalSelection bundle={bundle} onClaim={vi.fn()} />);
  expect(request).not.toHaveBeenCalled();
});
it("requires model choice and explicit confirmation after direct capability click", async () => {
  request.mockResolvedValue(caps);
  render(<LocalSelection bundle={bundle} onClaim={vi.fn()} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Compare with local AI selection" }),
  );
  await screen.findByRole("combobox");
  expect(screen.getByRole("combobox")).toHaveValue("");
  expect(
    screen.getByRole("button", { name: "Run confirmed local selection" }),
  ).toBeDisabled();
  expect(request).toHaveBeenCalledTimes(1);
});
it("prevents repeated clicks while capability request is in flight", () => {
  request.mockImplementation(() => new Promise(() => {}));
  render(<LocalSelection bundle={bundle} onClaim={vi.fn()} />);
  const button = screen.getByRole("button", {
    name: "Compare with local AI selection",
  });
  fireEvent.click(button);
  fireEvent.click(button);
  expect(request).toHaveBeenCalledTimes(1);
});
it("shows explicit unavailable state and preserves offline mode", async () => {
  request.mockResolvedValue({
    models: [],
    truncated: false,
    status: "UNAVAILABLE",
    code: "OLLAMA_CONNECTION_UNAVAILABLE",
  });
  render(<LocalSelection bundle={bundle} onClaim={vi.fn()} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Compare with local AI selection" }),
  );
  await screen.findByText(/Local Ollama unavailable/);
  expect(screen.getByText(/Default: Deterministic/)).toBeVisible();
});
it("rejects a selection from a changed fingerprint without proof buttons", async () => {
  request
    .mockResolvedValueOnce(caps)
    .mockResolvedValueOnce({
      source_fingerprint: "0".repeat(64),
      explanation: bundle.explanation,
    });
  render(<LocalSelection bundle={bundle} onClaim={vi.fn()} />);
  await choose();
  fireEvent.click(
    screen.getByRole("button", { name: "Run confirmed local selection" }),
  );
  await screen.findByText(/Local action failed/);
  expect(
    screen.queryByRole("button", { name: /Inspect local claim/ }),
  ).not.toBeInTheDocument();
});
it("sends exact snapshot and selected model only after confirmation", async () => {
  request
    .mockResolvedValueOnce(caps)
    .mockResolvedValueOnce({
      source_fingerprint: bundle.source_fingerprint,
      explanation: {
        ...bundle.explanation,
        mode_requested: "OLLAMA",
        mode_executed: "NONE",
        ai_generated_selection: false,
        claims: [],
        validated_claim_count: 0,
        validated_citation_count: 0,
        explanation_status: "MODEL_OUTPUT_REJECTED",
        rejection_codes: ["MODEL_UNKNOWN_CLAIM"],
      },
    });
  render(<LocalSelection bundle={bundle} onClaim={vi.fn()} />);
  await choose();
  fireEvent.click(
    screen.getByRole("button", { name: "Run confirmed local selection" }),
  );
  await screen.findByText(/No accepted AI selection/);
  expect(request.mock.calls[1][2]).toEqual({
    incident_id: "INC-001",
    options: bundle.investigation.options,
    source_fingerprint: bundle.source_fingerprint,
    model_id: "unit-local:1",
    confirmed: true,
  });
  expect(
    screen.queryByRole("button", { name: /Inspect local claim/ }),
  ).not.toBeInTheDocument();
});
it("aborts client wait on unmount", async () => {
  request.mockImplementation(
    (_path, signal) =>
      new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        );
      }),
  );
  const view = render(<LocalSelection bundle={bundle} onClaim={vi.fn()} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Compare with local AI selection" }),
  );
  view.unmount();
  await waitFor(() => expect(request.mock.calls[0][1].aborted).toBe(true));
});
