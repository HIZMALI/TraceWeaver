import { expect, it } from "vitest";
import { agentOutcome } from "../agent-outcome";
import type { AgentReport } from "../agent-contracts";
const base = {
  agent_status: "MODEL_OUTPUT_REJECTED",
  rejection_codes: [],
  ai_directed_tools: false,
  ai_generated_selection: false,
} satisfies Pick<
  AgentReport,
  | "agent_status"
  | "rejection_codes"
  | "ai_directed_tools"
  | "ai_generated_selection"
>;
it("distinguishes a transport timeout from invalid schema despite the preserved legacy status", () => {
  expect(
    agentOutcome({ ...base, rejection_codes: ["OLLAMA_TIMEOUT"] }),
  ).toMatch(/^Transport deadline reached/);
});
it("keeps daemon availability failure explicit and offers no hidden fallback", () => {
  expect(agentOutcome({ ...base, agent_status: "MODEL_UNAVAILABLE" })).toMatch(
    /^Local Ollama unavailable/,
  );
});
it("identifies actual native tools without falsely claiming accepted final selection", () => {
  expect(agentOutcome({ ...base, ai_directed_tools: true })).toMatch(
    /^Tool-only partial/,
  );
});
it("labels accepted IDs only when admission metadata says so, never as causal truth", () => {
  expect(
    agentOutcome({
      ...base,
      ai_directed_tools: true,
      ai_generated_selection: true,
    }),
  ).toMatch(/final claim IDs admitted.*unestablished/);
});
it("keeps explicit abstention separate from a model-selected factual explanation", () => {
  expect(
    agentOutcome({
      ...base,
      agent_status: "ABSTAINED",
      ai_directed_tools: true,
    }),
  ).toMatch(/^Model abstained/);
});
