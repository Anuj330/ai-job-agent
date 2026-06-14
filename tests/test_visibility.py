from app.modules.visibility.schemas import VisibilityRequest
from app.modules.visibility.service import build_visibility_result


def _request(resume_text: str) -> VisibilityRequest:
    return VisibilityRequest(
        resume_text=resume_text,
        target_role="python developer",
        top_keywords=10,
    )


def test_ranks_missing_keywords_by_market_demand() -> None:
    postings_skills = [
        ["Python", "Django", "AWS"],
        ["Python", "Django", "PostgreSQL"],
        ["Python", "FastAPI"],
        ["Python", "Django", "AWS"],
    ]
    # Resume has Python but lacks the most-demanded supporting skill (Django, 3/4 postings).
    result = build_visibility_result(
        _request("Experienced engineer skilled in Python."),
        "Experienced engineer skilled in Python.",
        postings_skills,
    )

    assert result.analyzed_postings == 4
    present = {item.keyword for item in result.present_keywords}
    missing = [item.keyword for item in result.missing_keywords]
    assert "Python" in present
    # Django is the highest-demand missing keyword, so it must rank first.
    assert missing[0] == "Django"
    assert result.missing_keywords[0].postings == 3
    assert result.missing_keywords[0].demand_pct == 75.0
    # Score is weighted by demand: only Python (4) covered out of 4+3+2+1+1 = 11.
    assert result.visibility_score == round(4 / 11 * 100)


def test_full_coverage_scores_high() -> None:
    resume = "Python and Django expert with years of delivery."
    postings_skills = [["Python", "Django"], ["Python", "Django"]]
    result = build_visibility_result(_request(resume), resume, postings_skills)
    assert result.visibility_score == 100
    assert not result.missing_keywords


def test_no_postings_returns_guidance() -> None:
    resume = "Python developer resume text here."
    result = build_visibility_result(_request(resume), resume, [])
    assert result.analyzed_postings == 0
    assert result.visibility_score == 0
    assert result.recommendations
