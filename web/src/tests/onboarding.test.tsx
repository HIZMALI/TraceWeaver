import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { ProofFocus } from "../ProofFocus";
import { bundleSchema } from "../contracts";
import input from "./fixtures/sprint06-bundle.json";

it("first action selects the returned dependency candidate without hiding competing scope", () => {
  const bundle = bundleSchema.parse(input),
    select = vi.fn();
  render(<ProofFocus bundle={bundle} onSelect={select} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Explore the verified path" }),
  );
  expect(select).toHaveBeenCalledWith("candidate:DEP-001~SVC-AUTH");
  expect(
    screen.getByRole("button", { name: /Focus proof DEP-002/ }),
  ).toBeVisible();
  expect(screen.getByText(/Verified means an exact stored path/)).toBeVisible();
});

it("does not invent a starting path for an empty native candidate scope", () => {
  const bundle = bundleSchema.parse(input);
  bundle.investigation.candidates = [];
  render(<ProofFocus bundle={bundle} onSelect={vi.fn()} />);
  expect(
    screen.queryByRole("button", { name: "Explore the verified path" }),
  ).toBeNull();
  expect(
    screen.getByText("No candidate returned; no cause established."),
  ).toBeVisible();
});
