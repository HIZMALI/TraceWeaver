// Vite replaces MODE at build time; URL parameters cannot enable local capabilities.
export function isPublicDemo(): boolean {
  return import.meta.env.MODE === "public";
}
