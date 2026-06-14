from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobRankingWeights(BaseModel):
    skills_match: float = Field(default=0.30, ge=0)
    location: float = Field(default=0.15, ge=0)
    salary: float = Field(default=0.20, ge=0)
    experience: float = Field(default=0.15, ge=0)
    remote_availability: float = Field(default=0.10, ge=0)
    visa_sponsorship: float = Field(default=0.10, ge=0)

    def normalized(self) -> dict[str, float]:
        values = self.model_dump()
        total = sum(values.values())
        if total <= 0:
            raise ValueError("At least one ranking weight must be greater than zero")
        return {key: value / total for key, value in values.items()}


class JobRankingCandidateProfile(BaseModel):
    skills: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    current_location: str | None = None
    desired_salary: float | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    experience_years: float | None = Field(default=None, ge=0)
    remote_preference: Literal["remote", "hybrid", "onsite", "any"] = "any"
    requires_visa_sponsorship: bool = False


class JobRankingJob(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    title: str
    company: str
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    description: str | None = None
    experience_level: str | None = None
    experience_min_years: float | None = None
    experience_max_years: float | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    work_mode: Literal["remote", "hybrid", "onsite"] | None = None
    visa_sponsorship: bool | None = None


class JobRankingRequest(BaseModel):
    candidate: JobRankingCandidateProfile
    jobs: list[JobRankingJob] = Field(min_length=1)
    weights: JobRankingWeights = Field(default_factory=JobRankingWeights)

    @model_validator(mode="after")
    def validate_weights(self) -> "JobRankingRequest":
        self.weights.normalized()
        return self


class JobFactorScores(BaseModel):
    skills_match: float = Field(ge=0, le=1)
    location: float = Field(ge=0, le=1)
    salary: float = Field(ge=0, le=1)
    experience: float = Field(ge=0, le=1)
    remote_availability: float = Field(ge=0, le=1)
    visa_sponsorship: float = Field(ge=0, le=1)


class RankedJob(JobRankingJob):
    score: float = Field(ge=0, le=100)
    factors: JobFactorScores


class JobRankingResult(BaseModel):
    ranked_jobs: list[RankedJob]


class JobRankingService:
    EXPERIENCE_LEVEL_MAP: dict[str, float] = {
        "internship": 0,
        "trainee": 0,
        "fresher": 0,
        "entry level": 0,
        "junior": 1,
        "associate": 3,
        "mid": 4,
        "mid-senior level": 5,
        "senior": 6,
        "director": 9,
        "executive": 10,
    }

    REMOTE_SCORE_MAP: dict[str, dict[str, float]] = {
        "remote": {"remote": 1.0, "hybrid": 0.7, "onsite": 0.0},
        "hybrid": {"remote": 0.8, "hybrid": 1.0, "onsite": 0.3},
        "onsite": {"remote": 0.2, "hybrid": 0.6, "onsite": 1.0},
        "any": {"remote": 0.5, "hybrid": 0.5, "onsite": 0.5},
    }

    def rank_jobs(self, request: JobRankingRequest) -> JobRankingResult:
        weights = request.weights.normalized()
        ranked = [
            self._rank_job(job, request.candidate, weights)
            for job in request.jobs
        ]
        ranked.sort(
            key=lambda item: (
                item.score,
                item.factors.skills_match,
                item.factors.location,
                item.factors.salary,
                item.factors.experience,
            ),
            reverse=True,
        )
        return JobRankingResult(ranked_jobs=ranked)

    def _rank_job(
        self,
        job: JobRankingJob,
        candidate: JobRankingCandidateProfile,
        weights: dict[str, float],
    ) -> RankedJob:
        factor_scores = JobFactorScores(
            skills_match=self._skills_score(candidate.skills, job.skills),
            location=self._location_score(candidate, job),
            salary=self._salary_score(candidate, job),
            experience=self._experience_score(candidate, job),
            remote_availability=self._remote_score(candidate, job),
            visa_sponsorship=self._visa_score(candidate, job),
        )
        score = round(
            100
            * sum(
                getattr(factor_scores, key) * weight
                for key, weight in weights.items()
            ),
            2,
        )
        return RankedJob(**job.model_dump(), score=score, factors=factor_scores)

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = re.sub(r"[^a-z0-9+#./\s-]", " ", value.lower())
        return re.sub(r"\s+", " ", normalized).strip()

    @classmethod
    def _tokens(cls, values: Iterable[str]) -> set[str]:
        tokens: set[str] = set()
        for value in values:
            normalized = cls._normalize(value)
            if normalized:
                tokens.update(normalized.split())
        return tokens

    @classmethod
    def _text_similarity(cls, left: str, right: str) -> float:
        left_tokens = cls._tokens([left])
        right_tokens = cls._tokens([right])
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = len(left_tokens & right_tokens)
        return overlap / max(len(left_tokens), len(right_tokens))

    @classmethod
    def _skill_match(cls, candidate_skill: str, job_skill: str) -> bool:
        candidate = cls._normalize(candidate_skill)
        job = cls._normalize(job_skill)
        return candidate == job or candidate in job or job in candidate

    @classmethod
    def _skills_score(cls, candidate_skills: list[str], job_skills: list[str]) -> float:
        if not job_skills:
            return 0.5
        if not candidate_skills:
            return 0.0
        matched = 0
        for job_skill in job_skills:
            if any(cls._skill_match(candidate_skill, job_skill) for candidate_skill in candidate_skills):
                matched += 1
        return matched / len(job_skills)

    @classmethod
    def _location_score(cls, candidate: JobRankingCandidateProfile, job: JobRankingJob) -> float:
        preferred_locations = candidate.preferred_locations or ([candidate.current_location] if candidate.current_location else [])
        if not preferred_locations:
            return 0.5
        if job.location is None:
            return 0.5
        best_match = max(cls._text_similarity(job.location, location) for location in preferred_locations)
        if best_match > 0:
            return best_match
        if job.work_mode == "remote":
            return 0.8
        if job.work_mode == "hybrid":
            return 0.6
        return 0.0

    @staticmethod
    def _salary_score(candidate: JobRankingCandidateProfile, job: JobRankingJob) -> float:
        if candidate.desired_salary is None or candidate.desired_salary <= 0:
            return 0.5
        if (
            candidate.salary_currency
            and job.salary_currency
            and candidate.salary_currency.upper() != job.salary_currency.upper()
        ):
            return 0.5
        if job.salary_max is not None:
            return min(1.0, max(0.0, job.salary_max / candidate.desired_salary))
        if job.salary_min is not None:
            return min(1.0, max(0.0, job.salary_min / candidate.desired_salary))
        return 0.5

    @classmethod
    def _experience_score(
        cls, candidate: JobRankingCandidateProfile, job: JobRankingJob
    ) -> float:
        if candidate.experience_years is None:
            return 0.5

        required_min = job.experience_min_years
        required_max = job.experience_max_years
        if required_min is None and required_max is None and job.experience_level:
            required_min = cls.EXPERIENCE_LEVEL_MAP.get(cls._normalize(job.experience_level))

        if required_min is None and required_max is None:
            return 0.5

        experience_years = candidate.experience_years
        if required_min is not None and experience_years < required_min:
            return min(1.0, experience_years / required_min) if required_min else 0.0
        if required_max is not None and experience_years > required_max:
            if required_max <= 0:
                return 1.0
            excess_ratio = (experience_years - required_max) / required_max
            return max(0.7, 1.0 - excess_ratio * 0.2)
        return 1.0

    @staticmethod
    def _remote_score(candidate: JobRankingCandidateProfile, job: JobRankingJob) -> float:
        if job.work_mode is None:
            return 0.5
        return JobRankingService.REMOTE_SCORE_MAP[candidate.remote_preference][job.work_mode]

    @staticmethod
    def _visa_score(candidate: JobRankingCandidateProfile, job: JobRankingJob) -> float:
        if not candidate.requires_visa_sponsorship:
            return 1.0
        return 1.0 if job.visa_sponsorship else 0.0


def get_job_ranking_service() -> JobRankingService:
    return JobRankingService()
