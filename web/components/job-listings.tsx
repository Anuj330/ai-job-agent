"use client";

import { useMemo, useState, type CSSProperties } from "react";

import type { JobListing } from "../lib/types";
import {
  experienceLabel,
  relativeTime,
  salaryLabel,
  scoreColor,
  scoreSoft,
  sourceMeta,
} from "../lib/format";

type Mode = "remote" | "hybrid" | "onsite";
type Sort = "newest" | "match" | "salary";

const MODES: Mode[] = ["remote", "hybrid", "onsite"];
const SOURCES = ["naukri", "linkedin", "bayt", "indeed"] as const;

const Chevron = () => (
  <svg
    className="chev"
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="m6 9 6 6 6-6" />
  </svg>
);

export function JobListings({ jobs, totalJobs }: { jobs: JobListing[]; totalJobs: number }) {
  const [query, setQuery] = useState("");
  const [modes, setModes] = useState<Mode[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [visaOnly, setVisaOnly] = useState(false);
  const [sort, setSort] = useState<Sort>("newest");
  const [view, setView] = useState<"grid" | "list">("grid");

  const toggle = <T,>(arr: T[], val: T): T[] =>
    arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = jobs.filter((job) => {
      if (q) {
        const hay = `${job.title} ${job.company} ${job.location ?? ""} ${job.skills.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (modes.length && (!job.work_mode || !modes.includes(job.work_mode))) return false;
      if (sources.length && !sources.includes(job.source)) return false;
      if (visaOnly && !job.visa_sponsorship) return false;
      return true;
    });
    list.sort((a, b) => {
      if (sort === "match") return (b.match_score ?? -1) - (a.match_score ?? -1);
      if (sort === "salary") return (b.salary_max ?? -1) - (a.salary_max ?? -1);
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
    return list;
  }, [jobs, query, modes, sources, visaOnly, sort]);

  const filtersActive = !!(query || modes.length || sources.length || visaOnly);
  const clearAll = () => {
    setQuery("");
    setModes([]);
    setSources([]);
    setVisaOnly(false);
  };

  const jobCols: CSSProperties = {
    ["--job-cols" as string]: view === "list" ? "1fr" : "repeat(auto-fill,minmax(330px,1fr))",
  };

  return (
    <section id="jobs" className="panel">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Job listings</h2>
          <p className="panel-sub">
            {filtered.length} of {totalJobs} roles · scored against your resumes
          </p>
        </div>
        <div className="listing-controls">
          <div className="search-box">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.2-3.2" />
            </svg>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search title, company or skill"
            />
          </div>
          <div className="select-wrap">
            <select value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
              <option value="newest">Newest first</option>
              <option value="match">Best match</option>
              <option value="salary">Top salary</option>
            </select>
            <Chevron />
          </div>
          <div className="view-toggle">
            <button
              type="button"
              title="Grid view"
              className={`view-btn ${view === "grid" ? "active" : ""}`}
              onClick={() => setView("grid")}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1.5" />
                <rect x="14" y="3" width="7" height="7" rx="1.5" />
                <rect x="3" y="14" width="7" height="7" rx="1.5" />
                <rect x="14" y="14" width="7" height="7" rx="1.5" />
              </svg>
            </button>
            <button
              type="button"
              title="List view"
              className={`view-btn ${view === "list" ? "active" : ""}`}
              onClick={() => setView("list")}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div className="chips">
        {MODES.map((mode) => (
          <button
            key={mode}
            type="button"
            className={`chip ${modes.includes(mode) ? "active" : ""}`}
            onClick={() => setModes((m) => toggle(m, mode))}
          >
            {mode.charAt(0).toUpperCase() + mode.slice(1)}
          </button>
        ))}
        {SOURCES.map((src) => (
          <button
            key={src}
            type="button"
            className={`chip ${sources.includes(src) ? "active" : ""}`}
            onClick={() => setSources((s) => toggle(s, src))}
          >
            <span className="chip-dot" style={{ background: sourceMeta(src).color }} />
            {sourceMeta(src).label}
          </button>
        ))}
        <button
          type="button"
          className={`chip ${visaOnly ? "active" : ""}`}
          onClick={() => setVisaOnly((v) => !v)}
        >
          Visa sponsored
        </button>
        {filtersActive ? (
          <button type="button" className="chip chip-clear" onClick={clearAll}>
            Clear all
          </button>
        ) : null}
      </div>

      {filtered.length > 0 ? (
        <div className="job-grid" style={jobCols}>
          {filtered.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      ) : (
        <div className="empty-block">
          <div className="t">No roles match those filters</div>
          <div className="s">Try removing a filter or clearing your search.</div>
          <button type="button" className="btn btn-outline" style={{ marginTop: 16 }} onClick={clearAll}>
            Clear filters
          </button>
        </div>
      )}
    </section>
  );
}

function JobCard({ job }: { job: JobListing }) {
  const meta = sourceMeta(job.source);
  const shown = job.skills.slice(0, 4);
  const more = job.skills.length > 4 ? job.skills.length - 4 : 0;
  const mode = job.work_mode;
  const modeColor = mode === "remote" ? "green" : mode === "hybrid" ? "accent" : "warn";
  const score = job.match_score;

  const badgeStyle =
    score != null
      ? ({ ["--sc" as string]: scoreColor(score), ["--sc-soft" as string]: scoreSoft(score) } as CSSProperties)
      : undefined;
  const modeStyle = {
    ["--tag" as string]: `var(--${modeColor})`,
    ["--tag-soft" as string]: `var(--${modeColor}-soft)`,
  } as CSSProperties;

  return (
    <article className="job-card">
      <div className="job-top">
        <div style={{ minWidth: 0 }}>
          <h3 className="job-title">{job.title}</h3>
          <div className="job-company">
            {job.company}
            {job.location ? ` · ${job.location}` : ""}
          </div>
        </div>
        {score != null ? (
          <div className="score-badge" style={badgeStyle}>
            <div className="num">{score}</div>
            <div className="lbl">fit</div>
          </div>
        ) : null}
      </div>

      <div className="job-meta">
        {mode ? (
          <span className="mode-tag" style={modeStyle}>
            {mode}
          </span>
        ) : null}
        <span className="source-tag">
          <span className="chip-dot" style={{ background: meta.color }} />
          {meta.label}
        </span>
        <span className="recency">{relativeTime(job.created_at)}</span>
      </div>

      <div className="skill-row">
        {shown.map((skill) => (
          <span key={skill} className="skill">
            {skill}
          </span>
        ))}
        {more ? <span className="skill-more">+{more} more</span> : null}
        <span className={`visa ${job.visa_sponsorship ? "yes" : "no"}`}>
          {job.visa_sponsorship ? "Visa sponsored" : "No visa"}
        </span>
      </div>

      <p className="clamp-2">{job.description ?? "No description provided yet."}</p>

      <div className="divider" />

      <div className="job-foot">
        <div className="job-stats">
          <div>
            <div className="stat-k">Comp</div>
            <div className="stat-v">{salaryLabel(job.salary_min, job.salary_max, job.salary_currency)}</div>
          </div>
          <div>
            <div className="stat-k">Experience</div>
            <div className="stat-v">{experienceLabel(job)}</div>
          </div>
        </div>
        <a className="btn-open" href={job.apply_url ?? job.source_url} target="_blank" rel="noreferrer">
          Open
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 4h6v6M20 4 10 14M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4" />
          </svg>
        </a>
      </div>
    </article>
  );
}
