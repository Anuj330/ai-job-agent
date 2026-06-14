import type {
  ApplicationRecord,
  CoverLetterRecord,
  DashboardStats,
  JobListing,
  ResumeRecord,
} from "./types";

const DEFAULT_BACKEND_URL = "http://localhost:8000/api/v1";

export function backendBaseUrl(): string {
  return (
    process.env.BACKEND_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BACKEND_URL
  );
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return (await response.json()) as T;
}

/**
 * Per-card fit scores against the user's primary resume, computed server-side via the
 * deterministic batch endpoint (no per-card LLM calls). Missing scores ⇒ no badge.
 */
async function fetchMatchScores(
  base: string,
  jobs: JobListing[],
  resumes: ResumeRecord[],
): Promise<JobListing[]> {
  if (!resumes.length || !jobs.length) return jobs;
  try {
    const { scores } = await postJson<{ scores: Record<string, number> }>(
      `${base}/ai/match/batch`,
      { resume_id: resumes[0].id, job_ids: jobs.map((job) => job.id) },
    );
    return jobs.map((job) => ({ ...job, match_score: scores[job.id] ?? null }));
  } catch {
    return jobs;
  }
}

export async function loadDashboardData(): Promise<{
  jobs: JobListing[];
  resumes: ResumeRecord[];
  coverLetters: CoverLetterRecord[];
  applications: ApplicationRecord[];
  stats: DashboardStats | null;
}> {
  const base = backendBaseUrl();
  const [jobs, resumes, coverLetters, applications, stats] = await Promise.all([
    getJson<JobListing[]>(`${base}/jobs?limit=100`).catch(() => []),
    getJson<ResumeRecord[]>(`${base}/resumes`).catch(() => []),
    getJson<CoverLetterRecord[]>(`${base}/cover-letters`).catch(() => []),
    getJson<ApplicationRecord[]>(`${base}/applications`).catch(() => []),
    getJson<DashboardStats>(`${base}/stats`).catch(() => null),
  ]);

  const scoredJobs = await fetchMatchScores(base, jobs, resumes);
  return { jobs: scoredJobs, resumes, coverLetters, applications, stats };
}

export async function loadVisibilityData(): Promise<{
  resumes: ResumeRecord[];
  poolSize: number;
}> {
  const base = backendBaseUrl();
  const [resumes, stats] = await Promise.all([
    getJson<ResumeRecord[]>(`${base}/resumes`).catch(() => []),
    getJson<DashboardStats>(`${base}/stats`).catch(() => null),
  ]);
  return { resumes, poolSize: stats?.jobs ?? 0 };
}
