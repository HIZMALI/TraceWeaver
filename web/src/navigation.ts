import type { Options } from "./contracts";
export const defaults: Options = {
  pre_minutes: 120,
  post_minutes: 30,
  max_candidates: 100,
  max_evidence: 100,
};
export interface Navigation {
  incident: string;
  selection: string;
  options: Options;
  warnings: string[];
}
export function parseNavigation(search: string): Navigation {
  const p = new URLSearchParams(search),
    warnings: string[] = [];
  let incident = p.get("incident") ?? "INC-001";
  if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(incident)) {
    incident = "INC-001";
    warnings.push("Invalid incident parameter; using INC-001.");
  }
  const options = { ...defaults };
  (Object.keys(defaults) as (keyof Options)[]).forEach((k) => {
    const value = p.get(k);
    if (value === null) return;
    const n = Number(value),
      cap = k.startsWith("max_") ? 100 : 1440,
      min = k.startsWith("max_") ? 1 : 0;
    if (!/^\d{1,4}$/.test(value) || !Number.isInteger(n) || n < min || n > cap)
      warnings.push(`Invalid ${k}; using ${defaults[k]}.`);
    else options[k] = n;
  });
  let selection = p.get("selection") ?? "";
  if (
    selection.length > 512 ||
    /[\x00-\x1f]/.test(selection) ||
    !/^$|^(claim|candidate|evidence|comparison|node|edge):/.test(selection)
  ) {
    selection = "";
    warnings.push("Invalid selection parameter ignored.");
  }
  return { incident, selection, options, warnings };
}
export function navigationURL(n: Navigation): string {
  const p = new URLSearchParams({ incident: n.incident });
  if (n.selection) p.set("selection", n.selection);
  (Object.keys(defaults) as (keyof Options)[]).forEach((k) => {
    if (n.options[k] !== defaults[k]) p.set(k, String(n.options[k]));
  });
  return `/?${p}`;
}
export function utcText(value: {
  utc: string | null;
  warning_code?: string | null;
}): string {
  if (!value.utc)
    return `Unknown${value.warning_code ? " · " + value.warning_code : ""}`;
  return value.utc.replace("T", " ").replace("Z", " UTC");
}
