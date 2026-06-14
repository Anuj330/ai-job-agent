from app.modules.ai.batch_match import score_job


def test_score_is_share_of_job_skills_in_resume() -> None:
    resume = "Senior engineer with Python, Django and PostgreSQL experience."
    # 2 of 3 distinct job skills present (Python, Django) -> 67.
    assert score_job(resume.lower(), ["Python", "Django", "Kubernetes"]) == 67


def test_full_overlap_scores_100() -> None:
    assert score_job("python django", ["Python", "Django"]) == 100


def test_no_skills_returns_none() -> None:
    # No usable skills -> None so the UI hides the badge instead of faking a score.
    assert score_job("anything", []) is None
