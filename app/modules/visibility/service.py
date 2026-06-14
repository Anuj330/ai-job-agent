from __future__ import annotations

import re
from collections import Counter

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.model import Job
from app.modules.resumes.model import Resume
from app.modules.visibility.schemas import KeywordDemand, VisibilityRequest, VisibilityResult


def _normalize(value: str) -> str:
    """Lowercase and collapse punctuation so "Node.js" and "node js" compare equal."""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _keyword_present(normalized_keyword: str, normalized_resume: str) -> bool:
    if not normalized_keyword:
        return False
    return normalized_keyword in normalized_resume


def build_visibility_result(
    request: VisibilityRequest, resume_text: str, postings_skills: list[list[str]]
) -> VisibilityResult:
    """Rank the keywords recruiters search for (mined from real postings) by demand,
    then score how many the resume already covers. Pure compute — easy to test."""
    total = len(postings_skills)
    if total == 0:
        return VisibilityResult(
            target_role=request.target_role,
            location=request.location,
            analyzed_postings=0,
            visibility_score=0,
            recommendations=[
                "No scraped postings matched this role yet. Run a scrape for "
                f'"{request.target_role}" so the optimizer can learn what recruiters search for.'
            ],
        )

    # Document frequency: count how many postings list each keyword (deduped per posting).
    counts: Counter[str] = Counter()
    display: dict[str, str] = {}
    for skills in postings_skills:
        seen: set[str] = set()
        for raw in skills:
            key = _normalize(raw)
            if not key or key in seen:
                continue
            seen.add(key)
            counts[key] += 1
            display.setdefault(key, raw.strip())

    top = counts.most_common(request.top_keywords)
    normalized_resume = _normalize(resume_text)

    present: list[KeywordDemand] = []
    missing: list[KeywordDemand] = []
    present_weight = 0
    total_weight = 0
    for key, postings in top:
        total_weight += postings
        demand = KeywordDemand(
            keyword=display.get(key, key),
            demand_pct=round(postings / total * 100, 1),
            postings=postings,
        )
        if _keyword_present(key, normalized_resume):
            present.append(demand)
            present_weight += postings
        else:
            missing.append(demand)

    score = round(present_weight / total_weight * 100) if total_weight else 0

    return VisibilityResult(
        target_role=request.target_role,
        location=request.location,
        analyzed_postings=total,
        visibility_score=score,
        present_keywords=present,
        missing_keywords=missing,
        recommendations=_recommendations(request, score, missing, total),
    )


def _recommendations(
    request: VisibilityRequest, score: int, missing: list[KeywordDemand], total: int
) -> list[str]:
    tips: list[str] = []
    if missing:
        top_missing = ", ".join(item.keyword for item in missing[:5])
        tips.append(
            "Add these high-demand keywords to your resume and Naukri skills "
            f"section: {top_missing}."
        )
        leader = missing[0]
        tips.append(
            f'"{leader.keyword}" appears in {leader.demand_pct}% of {total} '
            f'"{request.target_role}" postings — recruiters search it directly, so '
            "missing it pushes you down the list."
        )
    if score >= 80:
        tips.append(
            "Strong keyword coverage. Focus on profile freshness and completeness "
            "to hold the top spot."
        )
    tips.append(
        "Update your Naukri profile at least weekly — recently-updated profiles rank higher in "
        "recruiter searches."
    )
    tips.append(
        "Complete every searchable field (skills, current/preferred location, total experience, "
        "notice period) so filters don't exclude you before ranking even applies."
    )
    return tips


class VisibilityService:
    async def analyze(self, db: AsyncSession, request: VisibilityRequest) -> VisibilityResult:
        resume_text = await self._resolve_resume_text(db, request)
        jobs = await self._fetch_market_jobs(db, request)
        postings_skills = [list(job.skills or []) for job in jobs]
        return build_visibility_result(request, resume_text, postings_skills)

    @staticmethod
    async def _resolve_resume_text(db: AsyncSession, request: VisibilityRequest) -> str:
        if request.resume_id is not None:
            resume = await db.get(Resume, request.resume_id)
            if resume is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found")
            text = resume.content
        else:
            text = request.resume_text or ""
        if len(text.strip()) < 20:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Resume content is too short to analyze"
            )
        return text

    async def _fetch_market_jobs(
        self, db: AsyncSession, request: VisibilityRequest
    ) -> list[Job]:
        pattern = f"%{request.target_role}%"
        stmt = select(Job).where(
            or_(Job.title.ilike(pattern), Job.description.ilike(pattern))
        )
        if request.location:
            stmt = stmt.where(Job.location.ilike(f"%{request.location}%"))
        stmt = stmt.limit(request.sample_size)
        return list(await db.scalars(stmt))


def get_visibility_service() -> VisibilityService:
    return VisibilityService()
