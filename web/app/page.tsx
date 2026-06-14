import Link from "next/link";
import type { CSSProperties } from "react";

import { JobListings } from "../components/job-listings";
import { MatchWorkbench } from "../components/match-workbench";
import { ThemeToggle } from "../components/theme-toggle";
import { loadDashboardData } from "../lib/api";
import { relativeTime, statusMeta } from "../lib/format";
import type { ApplicationRecord, CoverLetterRecord, ResumeRecord } from "../lib/types";

function badgeStyle(color: string): CSSProperties {
  if (color === "muted") {
    return { ["--sb" as string]: "var(--muted)", ["--sb-soft" as string]: "var(--pill)" } as CSSProperties;
  }
  return {
    ["--sb" as string]: `var(--${color})`,
    ["--sb-soft" as string]: `var(--${color}-soft)`,
  } as CSSProperties;
}

function VisibilityIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="7.5" />
      <path d="m20 20-3.4-3.4" />
      <path d="M11 8v3l2 1.4" />
    </svg>
  );
}

export default async function HomePage() {
  const { jobs, resumes, coverLetters, applications, stats } = await loadDashboardData();

  const counts = {
    jobs: stats?.jobs ?? jobs.length,
    resumes: stats?.resumes ?? resumes.length,
    cover_letters: stats?.cover_letters ?? coverLetters.length,
    applications: stats?.applications ?? applications.length,
  };
  const pulse = stats?.pulse ?? {
    jobs_analyzed_pct: 0,
    resumes_optimized_pct: 0,
    applications_submitted_pct: 0,
  };
  const health = Math.round(
    (pulse.jobs_analyzed_pct + pulse.resumes_optimized_pct + pulse.applications_submitted_pct) / 3,
  );

  const metrics = [
    { value: counts.jobs, label: "Job listings scraped" },
    { value: counts.resumes, label: "Resumes on file" },
    { value: counts.cover_letters, label: "Cover letters" },
    { value: counts.applications, label: "Applications tracked" },
  ];
  const bars = [
    { label: "Jobs analyzed", pct: pulse.jobs_analyzed_pct, color: "var(--accent)" },
    { label: "Resumes optimized", pct: pulse.resumes_optimized_pct, color: "var(--warn)" },
    { label: "Applications submitted", pct: pulse.applications_submitted_pct, color: "var(--green)" },
  ];

  return (
    <main className="page">
      <div className="shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-logo">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2Z" />
                <path d="M12 12.5 9 11v3l3 1.5 3-1.5v-3Z" />
              </svg>
            </div>
            <div>
              <div className="brand-kicker">Operational cockpit</div>
              <h1 className="brand-title">AI Job Agent</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <Link className="pill-link" href="/visibility">
              <VisibilityIcon />
              Recruiter visibility
            </Link>
            <span className="status-pill">
              <span className="status-dot" />
              <span>Live dashboard</span>
              <span className="divider" />
              <strong>{counts.jobs} jobs loaded</strong>
            </span>
            <ThemeToggle />
          </div>
        </header>

        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">Talent workflow dashboard</span>
            <h1>Track the funnel from listing to application.</h1>
            <p>
              Your AI agent scrapes Naukri, LinkedIn, Bayt &amp; Indeed, scores every role against
              your resumes, and drafts the paperwork. This is the command center over that pipeline.
            </p>
            <div className="hero-actions">
              <a className="btn btn-accent" href="#jobs">
                Review jobs
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </a>
              <a className="btn btn-outline" href="#applications">
                Open tracking
              </a>
              <Link className="btn btn-outline" href="/visibility">
                Check visibility
                <VisibilityIcon />
              </Link>
            </div>
          </div>

          <div className="hero-side">
            <div className="metric-grid">
              {metrics.map((m) => (
                <div className="metric" key={m.label}>
                  <div className="metric-value">{m.value}</div>
                  <div className="metric-label">{m.label}</div>
                </div>
              ))}
            </div>
            <div className="pulse-card">
              <div className="pulse-head">
                <div>
                  <div className="pulse-eyebrow">Pipeline pulse</div>
                  <div className="pulse-sub">Healthy &amp; moving forward</div>
                </div>
                <div className="pulse-score">{health}%</div>
              </div>
              <div className="bars">
                {bars.map((bar) => (
                  <div key={bar.label}>
                    <div className="bar-head">
                      <span className="lbl">{bar.label}</span>
                      <span className="val">{bar.pct}%</span>
                    </div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${bar.pct}%`, background: bar.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <JobListings jobs={jobs} totalJobs={counts.jobs} />

        <MatchWorkbench jobs={jobs} resumes={resumes} />

        <section id="applications" className="lower-grid">
          <ApplicationsPanel applications={applications} />
          <ResumesPanel resumes={resumes} />
          <CoverLettersPanel coverLetters={coverLetters} />
        </section>

        <footer className="footer-note">
          Data refreshed live from the FastAPI backend · scraping Naukri, LinkedIn, Bayt &amp; Indeed
          · rendered fresh each load.
        </footer>
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const meta = statusMeta(status);
  return (
    <span className="status-badge" style={badgeStyle(meta.color)}>
      {meta.label}
    </span>
  );
}

function ApplicationsPanel({ applications }: { applications: ApplicationRecord[] }) {
  return (
    <div className="mini-panel">
      <div className="mini-head">
        <h2>Application tracking</h2>
        <span className="count-pill">{applications.length}</span>
      </div>
      <div className="mini-list">
        {applications.length ? (
          applications.map((a) => (
            <div className="item-card" key={a.id}>
              <div className="item-row">
                <div style={{ minWidth: 0 }}>
                  <div className="item-title">{a.job_title ?? "Application"}</div>
                  <div className="item-sub">{a.company ?? "Unknown company"}</div>
                </div>
                <StatusBadge status={a.status} />
              </div>
              <div className="item-foot">
                <span className="when">
                  {a.applied_at ? `Applied ${relativeTime(a.applied_at)}` : "Not applied yet"}
                </span>
                {a.notes ? <span className="notes">{a.notes}</span> : null}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-line">No applications tracked yet.</div>
        )}
      </div>
    </div>
  );
}

function ResumesPanel({ resumes }: { resumes: ResumeRecord[] }) {
  return (
    <div className="mini-panel">
      <div className="mini-head">
        <h2>Optimized resumes</h2>
        <span className="count-pill">{resumes.length}</span>
      </div>
      <div className="mini-list">
        {resumes.length ? (
          resumes.map((r) => (
            <div className="resume-row" key={r.id}>
              <div className="doc-tile">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <path d="M14 2v6h6M9 13h6M9 17h4" />
                </svg>
              </div>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div className="item-title">{r.name}</div>
                <div className="item-sub">
                  {r.owner_email} · updated {relativeTime(r.updated_at)}
                </div>
              </div>
              <StatusBadge status={r.status} />
            </div>
          ))
        ) : (
          <div className="empty-line">No resumes uploaded yet.</div>
        )}
      </div>
    </div>
  );
}

function CoverLettersPanel({ coverLetters }: { coverLetters: CoverLetterRecord[] }) {
  return (
    <div className="mini-panel">
      <div className="mini-head">
        <h2>Generated cover letters</h2>
        <span className="count-pill">{coverLetters.length}</span>
      </div>
      <div className="mini-list">
        {coverLetters.length ? (
          coverLetters.map((c) => {
            const title =
              c.company && c.job_title ? `${c.company} — ${c.job_title}` : c.title || "Cover letter";
            return (
              <div className="item-card" key={c.id}>
                <div className="item-row">
                  <div className="item-title" style={{ minWidth: 0 }}>
                    {title}
                  </div>
                  <StatusBadge status={c.status} />
                </div>
                <div className="item-sub">Generated {relativeTime(c.created_at)}</div>
                <p className="clamp-2" style={{ fontSize: 12.5 }}>
                  {c.content}
                </p>
              </div>
            );
          })
        ) : (
          <div className="empty-line">No cover letters generated yet.</div>
        )}
      </div>
    </div>
  );
}
