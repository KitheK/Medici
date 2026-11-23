"""Resume schema validator: only user facts may appear in generated resumes."""

from __future__ import annotations

from dataclasses import replace

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
from medici.resume.schema.validate import ValidationError, validate_resume

# Invented names only — no real people or companies.
_SAMPLE_FACTS = UserFacts(
    employers=(
        EmployerFact(
            name="Loominary Labs",
            title="Platform Engineer",
            location="Ficton, EX",
            start="Jun 2019",
            end="Present",
            bullets=("Shipped batch jobs on example.test.",),
        ),
        EmployerFact(
            name="Paperbyte Systems",
            title="Intern",
            location="Sampleville, EX",
            start="May 2017",
            end="Aug 2017",
        ),
    ),
    schools=(
        SchoolFact(
            name="North Example Institute",
            degree="B.S. Computer Science",
            location="Sampleville, EX",
            start="Sep 2015",
            end="May 2019",
        ),
    ),
    tools=("Python", "PostgreSQL", "Docker"),
    projects=(
        ProjectFact(
            name="fixture-cache",
            start="Jan 2018",
            end="Apr 2018",
            tools=("Python",),
            bullets=("Cached fixture payloads for tests.",),
        ),
    ),
)


def _matching_resume() -> ResumeDocument:
    return ResumeDocument(
        education=(
            EducationEntry(
                school="North Example Institute",
                degree="B.S. Computer Science",
                location="Sampleville, EX",
                dates="Sep 2015 -- May 2019",
            ),
        ),
        experience=(
            ExperienceEntry(
                employer="Loominary Labs",
                title="Platform Engineer",
                location="Ficton, EX",
                dates="Jun 2019 -- Present",
                bullets=("Shipped batch jobs on example.test.",),
            ),
            ExperienceEntry(
                employer="Paperbyte Systems",
                title="Intern",
                location="Sampleville, EX",
                dates="May 2017 -- Aug 2017",
            ),
        ),
        projects=(
            ProjectEntry(
                name="fixture-cache",
                dates="Jan 2018 -- Apr 2018",
                tools=("Python",),
                bullets=("Cached fixture payloads for tests.",),
            ),
        ),
        skills=("Python", "PostgreSQL", "Docker"),
    )


def test_valid_resume_passes_validation():
    validate_resume(_matching_resume(), _SAMPLE_FACTS)


def test_rejects_fabricated_employer():
    resume = _matching_resume()
    bad = replace(
        resume,
        experience=(
            replace(
                resume.experience[0],
                employer="PhantomWorks LLC",
            ),
            *resume.experience[1:],
        ),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(bad, _SAMPLE_FACTS)
    assert "employer" in str(exc.value).lower()
    assert "PhantomWorks" in str(exc.value)


def test_rejects_fabricated_school():
    resume = _matching_resume()
    bad = replace(
        resume,
        education=(
            replace(
                resume.education[0],
                school="South Fictional University",
            ),
        ),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(bad, _SAMPLE_FACTS)
    assert "school" in str(exc.value).lower()


def test_rejects_fabricated_date():
    resume = _matching_resume()
    bad = replace(
        resume,
        experience=(
            replace(
                resume.experience[0],
                dates="Jun 2019 -- Dec 2099",
            ),
            *resume.experience[1:],
        ),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(bad, _SAMPLE_FACTS)
    assert "date" in str(exc.value).lower()


def test_rejects_fabricated_tool_in_skills():
    resume = _matching_resume()
    bad = replace(resume, skills=(*resume.skills, "Kubernetes"))
    with pytest.raises(ValidationError) as exc:
        validate_resume(bad, _SAMPLE_FACTS)
    assert "tool" in str(exc.value).lower()


def test_rejects_fabricated_tool_in_project():
    resume = _matching_resume()
    bad = replace(
        resume,
        projects=(
            replace(
                resume.projects[0],
                tools=("Python", "Terraform"),
            ),
        ),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(bad, _SAMPLE_FACTS)
    assert "tool" in str(exc.value).lower()


def test_rejects_fabricated_project_name():
    resume = _matching_resume()
    bad = replace(
        resume,
        projects=(
            replace(
                resume.projects[0],
                name="phantom-sidequest",
            ),
        ),
    )
    with pytest.raises(ValidationError) as exc:
        validate_resume(bad, _SAMPLE_FACTS)
    assert "project" in str(exc.value).lower()


def test_validate_dict_round_trip():
    resume = _matching_resume()
    validate_resume(resume.to_dict(), _SAMPLE_FACTS.to_dict())