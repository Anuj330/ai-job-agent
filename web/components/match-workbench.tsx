"use client";

import { useState, type CSSProperties } from "react";

import type { JobListing, MatchAnalysis, ResumeRecord } from "../lib/types";
import { scoreColor } from "../lib/format";

type Status = "idle" | "loading" | "result" | "error";

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

export function MatchWorkbench({ jobs, resumes }: { jobs: JobListing[]; resumes: ResumeRecord[] }) {
  const [resumeId, setResumeId] = useState("");
  const [jobId, setJobId] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<MatchAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    const resume = resumes.find((r) => r.id === resumeId);
    const job = jobs.find((j) => j.id === jobId);
    if (!resume || !job) {
      setError("Pick a resume and a job to compare.");
      setStatus("idle");
      return;
    }
    setError(null);
    setStatus("loading");
    setResult(null);
    try {
      const response = await fetch("/api/backend/ai/match", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          resume_text: resume.content,
          job_description: job.description ?? `${job.title} at ${job.company}`,
        }),
      });
      if (!response.ok) throw new Error(`Analysis failed: ${response.status}`);
      setResult((await response.json()) as MatchAnalysis);
      setStatus("result");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to analyze match");
      setStatus("error");
    }
  }

  const job = jobs.find((j) => j.id === jobId);
  const color = result ? scoreColor(result.match_score) : "var(--accent)";
  const verdict = result
    ? result.match_score >= 80
      ? "Strong"
      : result.match_score >= 60
        ? "Moderate"
        : "Low"
    : "";

  return (
    <section className="panel">
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div className="icon-tile">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 2 4 14h6l-1 8 9-12h-6z" />
          </svg>
        </div>
        <div>
          <h2 className="panel-title" style={{ fontSize: 21 }}>
            Match scores workbench
          </h2>
          <p className="panel-sub">Compare a resume against any role for an AI fit breakdown.</p>
        </div>
      </div>

      <div className="wb-grid">
        <div className="wb-inputs">
          <div>
            <label className="field-label">Resume</label>
            <div className="select-wrap" style={{ display: "flex" }}>
              <select className="field-select" value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
                <option value="">Pick a resume…</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
              <Chevron />
            </div>
          </div>
          <div>
            <label className="field-label">Job</label>
            <div className="select-wrap" style={{ display: "flex" }}>
              <select className="field-select" value={jobId} onChange={(e) => setJobId(e.target.value)}>
                <option value="">Pick a job…</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} — {j.company}
                  </option>
                ))}
              </select>
              <Chevron />
            </div>
          </div>
          <button type="button" className="btn btn-accent" onClick={run} disabled={status === "loading"}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 2 4 14h6l-1 8 9-12h-6z" />
            </svg>
            {status === "loading" ? "Analyzing…" : "Run analysis"}
          </button>
          {error ? (
            <div className="error-chip">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              {error}
            </div>
          ) : null}
        </div>

        <div className="result-box">
          {status === "idle" || status === "error" ? (
            <div className="result-center">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.5 }}>
                <path d="M3 3v18h18" />
                <path d="m7 14 4-4 3 3 5-6" />
              </svg>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>No analysis yet</div>
              <div style={{ fontSize: 13, maxWidth: "30ch" }}>
                Select a resume and a job, then run the analysis to see the fit breakdown.
              </div>
            </div>
          ) : null}

          {status === "loading" ? (
            <div className="result-center" style={{ gap: 14 }}>
              <span className="spinner" />
              <div style={{ fontSize: 13.5 }}>Analyzing fit against the role…</div>
            </div>
          ) : null}

          {status === "result" && result ? (
            <div className="wb-result">
              <div className="wb-score-row">
                <div className="wb-score" style={{ color }}>
                  {result.match_score}
                  <small>/100</small>
                </div>
                <div style={{ flex: 1, minWidth: 150 }}>
                  <div className="meter-head">
                    <span style={{ fontWeight: 600, color }}>{verdict} match</span>
                    <span style={{ color: "var(--muted)" }}>
                      {job ? `${job.title} · ${job.company}` : ""}
                    </span>
                  </div>
                  <div className="meter-track">
                    <div
                      className="meter-fill"
                      style={{ width: `${result.match_score}%`, background: color } as CSSProperties}
                    />
                  </div>
                </div>
              </div>

              <div className="wb-cols">
                <div>
                  <div className="subhead">Missing skills</div>
                  <div className="tag-list">
                    {(result.missing_skills.length ? result.missing_skills : ["None — full overlap"]).map((s) => (
                      <span key={s} className="tag-danger">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="subhead">ATS keywords</div>
                  <div className="tag-list">
                    {result.ats_keyword_recommendations.map((s) => (
                      <span key={s} className="tag-green">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="wb-cols">
                <div>
                  <div className="subhead">Resume improvements</div>
                  <ul className="bullets">
                    {result.resume_improvement_suggestions.map((it) => (
                      <li key={it}>
                        <span className="mk" style={{ color: "var(--accent)" }}>
                          →
                        </span>
                        {it}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="subhead">Interview focus</div>
                  <ul className="bullets">
                    {result.interview_focus_areas.map((it) => (
                      <li key={it}>
                        <span className="mk" style={{ color: "var(--green)" }}>
                          ◆
                        </span>
                        {it}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
