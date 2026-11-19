import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jobmatch import keyword_baseline, load_jobs, load_resumes, parse_resume, score, summary  # noqa: E402
from jobmatch.match import total_years  # noqa: E402


@pytest.fixture(scope="module")
def jobs():
    return load_jobs(ROOT / "data" / "jobs.md")


@pytest.fixture(scope="module")
def resumes():
    return load_resumes(ROOT / "data" / "resumes.md")


@pytest.fixture(autouse=True)
def no_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)


def test_loads_jobs_and_resumes(jobs, resumes):
    assert set(jobs) == {"J1", "J2", "J3"}
    assert jobs["J1"].must[1] == ["Django", "FastAPI"]
    assert jobs["J3"].min_years == 4
    assert len(resumes) == 36


def test_years_do_not_double_count_overlap():
    r = parse_resume("- A, X, 2019 to 2021\n- B, Y, 2020 to 2023\n")
    assert total_years(r) == 4


def test_skills_list_alone_is_not_enough(jobs, resumes):
    # R04 lists every skill but only did manual testing.
    m = score(resumes["R04"], jobs["J1"])
    assert m.label == "maybe"
    assert all(c.status == "listed" for c in m.checks)
    assert keyword_baseline(resumes["R04"].text, jobs["J1"]) == "strong"


def test_no_hands_on_counts_as_missing(jobs, resumes):
    m = score(resumes["R07"], jobs["J1"])
    pg = next(c for c in m.checks if c.skill == "PostgreSQL")
    assert pg.status == "missing"


def test_reporting_to_a_team_lead_is_not_leading(jobs, resumes):
    m = score(resumes["R26"], jobs["J3"])
    lead = next(c for c in m.checks if c.skill == "Team lead")
    assert lead.status == "missing"


def test_strong_fit_with_reasons(jobs, resumes):
    m = score(resumes["R01"], jobs["J1"])
    assert m.label == "strong"
    text = summary(m, jobs["J1"].title)
    assert text.startswith("Strong fit")
    assert "4 years of work" in text


def test_name_does_not_change_the_result(jobs, resumes):
    r = resumes["R13"]
    renamed = parse_resume(r.text.replace(r.name, "Someone Else"))
    assert score(renamed, jobs["J2"]).label == score(r, jobs["J2"]).label
    assert r.name not in summary(score(r, jobs["J2"]), jobs["J2"].title)
