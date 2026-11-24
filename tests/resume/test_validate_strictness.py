"""Stricter resume validation (per-entry facts, bullets, date parsing)."""

from __future__ import annotations

import pytest

from medici.resume.schema.facts import (
    EducationEntry,
    EmployerFact,
    ExperienceEntry,
    ProjectEntry,
    ProjectFact,
    ResumeDocument,
    SchoolFact,
    UserFacts,
)
from medici.resume.schema.validate import ValidationError, date_tokens, validate_resume


def test_date_tokens_does_not_split_october_on_to():
    assert date_tokens("October 2023 -- Present") == ("October 2023", "Present")


def test_rejects_employer_dates_from_another_job():
    facts = UserFacts(
        employers=(
            EmployerFact(name="A", title="Engineer", start="Jun 2019", end="Present"),
            EmployerFact(name="B", title="Intern", start="May 2017", end="Aug 2017"),
        ),
        schools=(SchoolFact(name="C", degree="B.S.", start="2015", end="2019"),),  # noqa: E501
        tools=("Python",),
    )
    resume = ResumeDocument(
        education=(EducationEntry(school="C", degree="B.S.", dates="2015 -- 2019"),),
        experience=(
            ExperienceEntry(
                employer="A",
                title="Engineer",
                dates="May 2017 -- Aug 2017",
            ),
            ExperienceEntry(employer="B", title="Intern", dates="May 2017 -- Aug 2017"),
        ),
        skills=("Python",),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(resume, facts)
    assert "date" in str(exc.value).lower()


def test_accepts_october_date_range_from_facts():
    facts = UserFacts(
        employers=(
            EmployerFact(
                name="Loominary Labs",
                title="Engineer",
                start="October 2023",
                end="Present",
            ),
        ),
        schools=(
            SchoolFact(
                name="North Example Institute",
                degree="B.S.",
                start="2015",
                end="2019",
            ),
        ),
        tools=(),
    )
    resume = ResumeDocument(
        education=(
            EducationEntry(
                school="North Example Institute",
                degree="B.S.",
                dates="2015 -- 2019",
            ),
        ),
        experience=(
            ExperienceEntry(
                employer="Loominary Labs",
                title="Engineer",
                dates="October 2023 -- Present",
            ),
        ),
        skills=(),
    )
    validate_resume(resume, facts)


def test_rejects_inflated_job_title():
    facts = UserFacts(
        employers=(
            EmployerFact(
                name="Paperbyte Systems",
                title="Intern",
                start="2017",
                end="2018",
            ),
        ),
        schools=(SchoolFact(name="C", degree="B.S.", start="2015", end="2019"),),
        tools=(),
    )
    resume = ResumeDocument(
        education=(EducationEntry(school="C", degree="B.S.", dates="2015 -- 2019"),),
        experience=(
            ExperienceEntry(
                employer="Paperbyte Systems",
                title="Senior Engineer",
                dates="2017 -- 2018",
            ),
        ),
        skills=(),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(resume, facts)
    assert "title" in str(exc.value).lower()


def test_rejects_inflated_degree():
    facts = UserFacts(
        employers=(),
        schools=(
            SchoolFact(
                name="North Example Institute",
                degree="B.S. Computer Science",
                start="2015",
                end="2019",
            ),
        ),
        tools=(),
    )
    resume = ResumeDocument(
        education=(
            EducationEntry(
                school="North Example Institute",
                degree="M.S. Computer Science",
                dates="2015 -- 2019",
            ),
        ),
        experience=(),
        skills=(),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(resume, facts)
    assert "degree" in str(exc.value).lower()


def test_rejects_fabricated_tool_in_experience_bullet():
    facts = UserFacts(
        employers=(
            EmployerFact(
                name="Loominary Labs",
                title="Engineer",
                start="2019",
                end="Present",
                bullets=("Shipped batch jobs on example.test.",),
            ),
        ),
        schools=(SchoolFact(name="C", degree="B.S.", start="2015", end="2019"),),
        tools=("Python",),
    )
    resume = ResumeDocument(
        education=(EducationEntry(school="C", degree="B.S.", dates="2015 -- 2019"),),
        experience=(
            ExperienceEntry(
                employer="Loominary Labs",
                title="Engineer",
                dates="2019 -- Present",
                bullets=("Cut latency 70% using Kafka.",),
            ),
        ),
        skills=("Python",),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(resume, facts)
    msg = str(exc.value).lower()
    assert "tool" in msg or "kafka" in msg


def test_rejects_fabricated_metric_in_bullet():
    facts = UserFacts(
        employers=(
            EmployerFact(
                name="Loominary Labs",
                title="Engineer",
                start="2019",
                end="Present",
                bullets=("Shipped batch jobs on example.test.",),
            ),
        ),
        schools=(SchoolFact(name="C", degree="B.S.", start="2015", end="2019"),),
        tools=("Python",),
    )
    resume = ResumeDocument(
        education=(EducationEntry(school="C", degree="B.S.", dates="2015 -- 2019"),),
        experience=(
            ExperienceEntry(
                employer="Loominary Labs",
                title="Engineer",
                dates="2019 -- Present",
                bullets=("Cut latency 70% using Python.",),
            ),
        ),
        skills=("Python",),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(resume, facts)
    assert "number" in str(exc.value).lower() or "70" in str(exc.value)


def test_project_tools_must_match_that_projects_facts():
    facts = UserFacts(
        employers=(),
        schools=(SchoolFact(name="C", degree="B.S."),),
        tools=("Python", "Docker"),
        projects=(
            ProjectFact(name="fixture-cache", start="2018", end="2018", tools=("Python",)),
        ),
    )
    resume = ResumeDocument(
        education=(EducationEntry(school="C", degree="B.S.", dates="2015 -- 2019"),),
        experience=(),
        projects=(
            ProjectEntry(
                name="fixture-cache",
                dates="2018 -- 2018",
                tools=("Docker",),
            ),
        ),
        skills=("Python", "Docker"),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(resume, facts)
    assert "tool" in str(exc.value).lower()