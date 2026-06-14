"use client";

import { useMemo, useState, type CSSProperties } from "react";

import type { ResumeRecord, VisibilityResult } from "../lib/types";
import { demandColor, visibilityColor, visibilityVerdict } from "../lib/format";

type Status = "idle" | "loading" | "result" | "empty" | "error";

const ARC = Math.PI * 82; // semicircle arc length ≈ 257.6

const Chevron = () => (
  <svg className="chev" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
    <path d="m6 9 6 6 6-6" />
  </svg>
);

export function VisibilityView({ resumes, poolSize }: { resumes: ResumeRecord[]; poolSize: number }) {
  const [resumeId, setResumeId] = useState(resumes[0]?.id ?? "");
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<VisibilityResult | null>(null);
  const [copied, setCopied] = useState(false);

  async function analyze() {
    if (role.trim().length < 2) {
      setStatus("error");
      return;
    }
    setStatus("loading");
    setCopied(false);
    try {
      const body: Record<string, unknown> = { target_role: role.trim() };
      if (resumeId) body.resume_id = resumeId;
      if (location.trim()) body.location = location.trim();
      const response = await fetch("/api/backend/ai/visibility", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(String(response.status));
      const data = (await response.json()) as VisibilityResult;
      setResult(data);
      setStatus(data.analyzed_postings === 0 ? "empty" : "result");
    } catch {
      setStatus("error");
    }
  }

  async function runScrape() {
    setStatus("loading");
    try {
      await fetch("/api/backend/scrapers/naukri/runs", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          keywords: role.trim(),
          location: location.trim() || "india",
          max_jobs: 25,
        }),
      });
    } catch {
      /* fire-and-forget; re-analyze regardless */
    }
    // Scrape runs async on the worker; give it time, then re-analyze once.
    window.setTimeout(analyze, 32000);
  }

  function copyText(text: string) {
    try {
      navigator.clipboard?.writeText(text);
    } catch {
      /* ignore */
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  const missing = useMemo(
    () => (result ? [...result.missing_keywords].sort((a, b) => b.demand_pct - a.demand_pct) : []),
    [result],
  );
  const present = useMemo(
    () => (result ? [...result.present_keywords].sort((a, b) => b.demand_pct - a.demand_pct) : []),
    [result],
  );

  const score = result?.visibility_score ?? 0;
  const color = visibilityColor(score);
  const gaugeDash = `${((score / 100) * ARC).toFixed(1)} ${ARC.toFixed(1)}`;
  const totalKw = (result?.present_keywords.length ?? 0) + (result?.missing_keywords.length ?? 0);

  return (
    <section className="vis-panel">
      <div className="vis-head">
        <div className="vis-head-left">
          <div className="vis-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="7.5" />
              <path d="m20 20-3.4-3.4" />
              <path d="M11 8v3l2 1.4" />
            </svg>
          </div>
          <div>
            <div className="vis-eyebrow">Recruiter visibility</div>
            <h2>How searchable are you?</h2>
          </div>
        </div>
        <div className="vis-pool">
          <span className="dot" />
          Mined from {poolSize.toLocaleString()} live postings
        </div>
      </div>

      <p className="vis-intro">
        Recruiters find candidates by searching keywords. We compare your resume against what the
        market actually asks for — so you can rank higher in candidate search.
      </p>

      <div className="vis-inputs">
        <div>
          <label className="field-label">Resume</label>
          <div className="select-wrap" style={{ display: "flex" }}>
            <select className="field-select" value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
              <option value="">Paste-free · pick a resume…</option>
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
          <label className="field-label">Target role</label>
          <input className="field-input" value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. python developer" />
        </div>
        <div>
          <label className="field-label">
            Location <span style={{ fontWeight: 400 }}>· optional</span>
          </label>
          <input className="field-input" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Bangalore" />
        </div>
        <button type="button" className="btn btn-accent" style={{ height: 43 }} onClick={analyze} disabled={status === "loading"}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 2 4 14h6l-1 8 9-12h-6z" />
          </svg>
          Analyze
        </button>
      </div>

      <div className="vis-body">
        {status === "idle" ? (
          <div className="vis-state">
            <div className="state-icon" style={{ background: "var(--accent-soft)", color: "var(--accent)" }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="7.5" />
                <path d="m20 20-3.4-3.4" />
              </svg>
            </div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>Check your recruiter visibility</div>
            <div style={{ fontSize: 13.5, maxWidth: "38ch", lineHeight: 1.5 }}>
              Pick a resume and a target role, then hit Analyze to see which in-demand keywords you
              are missing.
            </div>
          </div>
        ) : null}

        {status === "loading" ? (
          <div className="vis-state">
            <span className="spinner" style={{ width: 38, height: 38 }} />
            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>Analyzing market demand…</div>
            <div style={{ fontSize: 13 }}>Scanning live postings for “{role}”</div>
          </div>
        ) : null}

        {status === "error" ? (
          <div className="vis-state">
            <div className="state-icon" style={{ background: "var(--danger-soft)", color: "var(--danger)" }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v4.5M12 16h.01" />
              </svg>
            </div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>Couldn’t reach the analysis service</div>
            <div style={{ fontSize: 13.5, maxWidth: "36ch", lineHeight: 1.5 }}>
              Enter a target role and try again — check your connection if it keeps failing.
            </div>
            <button type="button" className="btn btn-outline" onClick={analyze}>
              Retry
            </button>
          </div>
        ) : null}

        {status === "empty" ? (
          <div className="vis-state">
            <div className="state-icon" style={{ background: "var(--warn-soft)", color: "var(--warn)" }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-7l-2-2H5a2 2 0 0 0-2 2Z" />
              </svg>
            </div>
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>No postings matched “{role}”</div>
            <div style={{ fontSize: 13.5, maxWidth: "38ch", lineHeight: 1.5 }}>
              We don’t have enough scraped data for this role yet. Run a scrape for it, then
              re-analyze.
            </div>
            <button type="button" className="btn btn-accent" onClick={runScrape}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
                <path d="M21 3v5h-5" />
              </svg>
              Run a scrape
            </button>
          </div>
        ) : null}

        {status === "result" && result ? (
          <div className="vis-result">
            <div className="vis-col">
              <div className="gauge-card">
                <div className="gauge-wrap">
                  <svg width="200" height="128" viewBox="0 0 200 128">
                    <path d="M18 116 A82 82 0 0 1 182 116" fill="none" stroke="var(--border)" strokeWidth="14" strokeLinecap="round" />
                    <path
                      d="M18 116 A82 82 0 0 1 182 116"
                      fill="none"
                      stroke={color}
                      strokeWidth="14"
                      strokeLinecap="round"
                      strokeDasharray={gaugeDash}
                      style={{ transition: "stroke-dasharray .9s cubic-bezier(.2,.8,.2,1)" }}
                    />
                  </svg>
                  <div className="gauge-center">
                    <div className="gauge-score" style={{ color }}>
                      {score}
                    </div>
                    <div className="gauge-lbl">visibility</div>
                  </div>
                </div>
                <div className="gauge-verdict" style={{ color }}>
                  {visibilityVerdict(score)}
                </div>
                <div className="gauge-sub">
                  {result.analyzed_postings} postings analyzed · {present.length} of {totalKw} in-demand
                  keywords covered
                </div>
              </div>

              <div className="rec-card">
                <div className="rec-head">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 11l3 3L22 4" />
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                  </svg>
                  <div className="subhead" style={{ marginBottom: 0 }}>
                    Recommendations
                  </div>
                </div>
                <ul className="rec-list">
                  {result.recommendations.map((rec) => (
                    <li key={rec}>
                      <span className="rec-check">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M5 12l5 5L20 7" />
                        </svg>
                      </span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="vis-col">
              <div className="missing-card">
                <div className="missing-head">
                  <div>
                    <h3>
                      <span className="dot" style={{ background: "var(--danger)" }} />
                      Fix these to rank up
                    </h3>
                    <div className="sub">
                      Keywords recruiters search for — missing from your resume, highest demand
                      first.
                    </div>
                  </div>
                  <button
                    type="button"
                    className="copy-btn"
                    style={{ color: copied ? "var(--green)" : "var(--pill-text)" }}
                    onClick={() => copyText(missing.map((m) => m.keyword).join(", "))}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="9" y="9" width="11" height="11" rx="2" />
                      <path d="M5 15V5a2 2 0 0 1 2-2h10" />
                    </svg>
                    {copied ? "Copied!" : "Copy all"}
                  </button>
                </div>

                <div className="kw-list">
                  {missing.map((kw, i) => {
                    const dc = demandColor(kw.demand_pct);
                    return (
                      <button key={kw.keyword} type="button" className="kw-row" onClick={() => copyText(kw.keyword)} title="Click to copy">
                        <div className="kw-top">
                          <div className="kw-name-wrap">
                            <span className="kw-rank">{i + 1}</span>
                            <span className="kw-name">{kw.keyword}</span>
                          </div>
                          <div className="kw-demand">
                            <span className="pct" style={{ color: dc }}>
                              {kw.demand_pct}%
                            </span>
                            <span className="lbl">demand</span>
                          </div>
                        </div>
                        <div className="kw-bar-row">
                          <div className="kw-bar-track">
                            <div className="kw-bar-fill" style={{ width: `${kw.demand_pct}%`, background: dc } as CSSProperties} />
                          </div>
                          <span className="kw-postings">{kw.postings} postings</span>
                        </div>
                      </button>
                    );
                  })}
                  {missing.length === 0 ? (
                    <div className="empty-line">No gaps — your resume covers the top keywords.</div>
                  ) : null}
                </div>
              </div>

              <div className="covered-card">
                <div className="covered-head">
                  <span className="dot" style={{ background: "var(--green)" }} />
                  <h3>Already covered</h3>
                  <span style={{ fontSize: 11.5, color: "var(--muted)" }}>· {present.length} keywords</span>
                </div>
                <div className="covered-wrap">
                  {present.map((kw) => (
                    <div key={kw.keyword} className="covered-pill">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M5 12l5 5L20 7" />
                      </svg>
                      <span className="name">{kw.keyword}</span>
                      <span className="pct">{kw.demand_pct}%</span>
                    </div>
                  ))}
                  {present.length === 0 ? <div className="empty-line">None covered yet.</div> : null}
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
