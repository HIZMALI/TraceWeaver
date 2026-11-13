import { incidentListSchema, verifyBundle, type Options } from "./contracts";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export function boundedJSON(raw: string): unknown {
  if (new TextEncoder().encode(raw).length > 2 * 1024 * 1024)
    throw new Error("Response exceeds browser byte limit");
  let depth = 0,
    quoted = false,
    escaped = false;
  for (const c of raw) {
    if (quoted) {
      if (escaped) escaped = false;
      else if (c === "\\") escaped = true;
      else if (c === '"') quoted = false;
    } else if (c === '"') quoted = true;
    else if (c === "{" || c === "[") {
      if (++depth > 20) throw new Error("Response depth limit");
    } else if (c === "}" || c === "]") depth--;
  }
  return JSON.parse(raw);
}
export async function requestJSON(
  path: string,
  signal: AbortSignal,
): Promise<unknown> {
  const response = await fetch(path, {
    signal,
    credentials: "omit",
    redirect: "error",
    headers: { Accept: "application/json" },
  });
  if (!response.ok)
    throw new ApiError(
      response.status,
      (
        {
          404: "Incident not found",
          422: "Invalid request options",
          503: "Graph database unavailable or incompatible",
          500: "Internal server error",
        } as Record<number, string>
      )[response.status] ?? "Request failed",
    );
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Empty response");
  const chunks: Uint8Array[] = [];
  let count = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    count += value.byteLength;
    if (count > 2 * 1024 * 1024) {
      await reader.cancel();
      throw new Error("Response exceeds browser byte limit");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(count);
  let offset = 0;
  for (const c of chunks) {
    bytes.set(c, offset);
    offset += c.byteLength;
  }
  return boundedJSON(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
}
export const getIncidents = async (signal: AbortSignal) =>
  incidentListSchema.parse(await requestJSON("/console/incidents", signal));
export const getBundle = async (
  incident: string,
  options: Options,
  signal: AbortSignal,
) =>
  verifyBundle(
    await requestJSON(
      `/incidents/${encodeURIComponent(incident)}/dashboard?${new URLSearchParams(Object.entries(options).map(([k, v]) => [k, String(v)]))}`,
      signal,
    ),
  );
