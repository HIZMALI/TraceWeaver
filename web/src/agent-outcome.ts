import type { AgentReport } from "./agent-contracts";

export function agentOutcome(
  report: Pick<
    AgentReport,
    | "agent_status"
    | "rejection_codes"
    | "ai_generated_selection"
    | "ai_directed_tools"
  >,
): string {
  if (report.rejection_codes.includes("OLLAMA_TIMEOUT"))
    return "Transport deadline reached (OLLAMA_TIMEOUT). No model response was admitted. Native steps, if any, remain visible; offline rehearsal is available explicitly.";
  if (report.agent_status === "MODEL_UNAVAILABLE")
    return "Local Ollama unavailable. No accepted AI result or automatic fallback. Offline rehearsal remains available.";
  if (report.ai_generated_selection)
    return "Local-model tools and final claim IDs admitted. Cause and source truth remain unestablished.";
  if (report.agent_status === "ABSTAINED")
    return "Model abstained. No AI-selected factual statements; native checks and the server caution remain visible.";
  if (report.ai_directed_tools)
    return `Tool-only partial: ${report.agent_status}. Native steps ran, but no final AI selection was admitted. No automatic fallback.`;
  return `No accepted final AI selection: ${report.agent_status}. No automatic fallback.`;
}
