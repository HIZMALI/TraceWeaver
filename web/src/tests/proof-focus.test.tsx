import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { bundleSchema } from "../contracts";
import { ProofFocus } from "../ProofFocus";
import input from "./fixtures/INC-001.json";

it("summarizes actual returned service and competing deployment identities", () => {
  const bundle = bundleSchema.parse(input);
  render(<ProofFocus bundle={bundle} onSelect={vi.fn()} />);
  expect(
    screen.getByRole("heading", { name: "Why this graph matters" }),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: /Focus proof DEP-001.*SVC-AUTH/ }),
  ).toBeVisible();
  expect(
    screen.getByRole("button", { name: /Focus proof DEP-002.*SVC-PAYMENT/ }),
  ).toBeVisible();
  expect(
    screen.getByText(/Returned scope: 2 pairs · 4 evidence/),
  ).toBeVisible();
});
it("links the exact pair to existing proof selection", () => {
  const select = vi.fn();
  render(<ProofFocus bundle={bundleSchema.parse(input)} onSelect={select} />);
  fireEvent.click(
    screen.getByRole("button", { name: /Focus proof DEP-001.*SVC-AUTH/ }),
  );
  expect(select).toHaveBeenCalledWith("candidate:DEP-001~SVC-AUTH");
});
it("never describes provenance or connectivity as causal authentication", () => {
  render(<ProofFocus bundle={bundleSchema.parse(input)} onSelect={vi.fn()} />);
  expect(screen.getByText(/Connection is not cause/)).toBeVisible();
  expect(screen.getByText(/External truth NOT_PERFORMED/)).toBeVisible();
});
it("handles empty returned service/candidate/evidence without invented facts", () => {
  const b = bundleSchema.parse(input);
  b.investigation.affected_services = [];
  b.investigation.candidates = [];
  b.investigation.evidence = [];
  render(<ProofFocus bundle={b} onSelect={vi.fn()} />);
  expect(screen.getByText(/No affected service returned/)).toBeVisible();
  expect(screen.getByText(/No candidate returned/)).toBeVisible();
  expect(screen.getByText(/No evidence returned/)).toBeVisible();
});
