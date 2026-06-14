import type { JobSource } from "./types";

export const SOURCE_META: Record<JobSource, { label: string; color: string }> = {
  naukri: { label: "Naukri", color: "#f5803e" },
  linkedin: { label: "LinkedIn", color: "#4a8fe7" },
  bayt: { label: "Bayt", color: "#14b8a6" },
  indeed: { label: "Indeed", color: "#2557a7" },
};

export function sourceMeta(source: string): { label: string; color: string } {
  return SOURCE_META[source as JobSource] ?? { label: source, color: "var(--muted)" };
}

export function relativeTime(iso: string | null): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const hours = (Date.now() - then) / 36e5;
  if (hours < 0) return "just now";
  if (hours < 1) return "just now";
  if (hours < 24) return `${Math.round(hours)}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function trim(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export function salaryLabel(
  min: number | null,
  max: number | null,
  currency: string | null,
): string {
  if (min == null && max == null) return "Salary not shared";
  const lo = min ?? max ?? 0;
  const hi = max ?? min ?? 0;
  if (currency === "INR") return `₹${trim(lo / 1e5)}–${trim(hi / 1e5)} LPA`;
  if (currency === "USD") return `$${trim(lo / 1e3)}–${trim(hi / 1e3)}k`;
  if (currency === "AED") return `AED ${trim(lo / 1e3)}–${trim(hi / 1e3)}k`;
  if (currency) return `${currency} ${Math.round(lo).toLocaleString()}–${Math.round(hi).toLocaleString()}`;
  return "Salary not shared";
}

export function experienceLabel(job: {
  experience_min_years: number | null;
  experience_max_years: number | null;
  experience_level: string | null;
}): string {
  const { experience_min_years: lo, experience_max_years: hi, experience_level: lvl } = job;
  if (lo != null && hi != null) return `${trim(lo)}–${trim(hi)} yrs`;
  if (lo != null) return `${trim(lo)}+ yrs`;
  return lvl ?? "Not specified";
}

// Job-card / workbench thresholds: >=80 green, >=60 warn, else danger.
export function scoreColor(score: number): string {
  if (score >= 80) return "var(--green)";
  if (score >= 60) return "var(--warn)";
  return "var(--danger)";
}
export function scoreSoft(score: number): string {
  if (score >= 80) return "var(--green-soft)";
  if (score >= 60) return "var(--warn-soft)";
  return "var(--danger-soft)";
}

// Visibility gauge thresholds: >=80 green, >=50 warn, else danger.
export function visibilityColor(score: number): string {
  if (score >= 80) return "var(--green)";
  if (score >= 50) return "var(--warn)";
  return "var(--danger)";
}
export function visibilityVerdict(score: number): string {
  if (score >= 80) return "Highly visible to recruiters";
  if (score >= 50) return "Partially visible — room to climb";
  return "Low visibility — easy wins available";
}

// Keyword demand bar: >=70 danger (high demand), >=45 warn, else accent.
export function demandColor(pct: number): string {
  if (pct >= 70) return "var(--danger)";
  if (pct >= 45) return "var(--warn)";
  return "var(--accent)";
}

const STATUS_META: Record<string, { label: string; color: string }> = {
  interview: { label: "Interview", color: "warn" },
  applied: { label: "Applied", color: "accent" },
  offer: { label: "Offer", color: "green" },
  rejected: { label: "Rejected", color: "danger" },
  draft: { label: "Draft", color: "muted" },
  optimized: { label: "Optimized", color: "green" },
  ready: { label: "Ready", color: "green" },
  review: { label: "In review", color: "warn" },
  discovered: { label: "Discovered", color: "accent" },
};

export function statusMeta(status: string): { label: string; color: string } {
  return (
    STATUS_META[status.toLowerCase()] ?? {
      label: status.charAt(0).toUpperCase() + status.slice(1),
      color: "muted",
    }
  );
}
