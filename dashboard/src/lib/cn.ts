// Small UI helpers. Rebuilt: the original src/lib/ was dropped by the
// project's `lib/` gitignore rule.
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "—";
  return n.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return d.toLocaleString(undefined, {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
}

const ISO_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

export function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") {
    if (!Number.isFinite(v)) return "NaN";
    if (Number.isInteger(v)) return v.toLocaleString();
    return v.toLocaleString(undefined, { maximumFractionDigits: 6 });
  }
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "string") {
    if (ISO_RE.test(v)) {
      const d = new Date(v);
      if (!Number.isNaN(d.getTime())) return d.toISOString().replace("T", " ").replace(".000Z", "Z");
    }
    return v;
  }
  if (Array.isArray(v) || typeof v === "object") return JSON.stringify(v);
  return String(v);
}
