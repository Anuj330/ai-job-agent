import Link from "next/link";

import { ThemeToggle } from "../../components/theme-toggle";
import { VisibilityView } from "../../components/visibility-view";
import { loadVisibilityData } from "../../lib/api";

export default async function VisibilityPage() {
  const { resumes, poolSize } = await loadVisibilityData();

  return (
    <main className="page">
      <div className="shell shell-narrow">
        <div className="vis-topbar">
          <Link className="pill-link" href="/">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
            Back to dashboard
          </Link>
          <ThemeToggle />
        </div>
        <VisibilityView resumes={resumes} poolSize={poolSize} />
      </div>
    </main>
  );
}
