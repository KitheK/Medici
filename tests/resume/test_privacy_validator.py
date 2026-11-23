"""Privacy: resume validator must not invent credentials from job postings."""

from __future__ import annotations

import pytest

from medici.resume.schema.facts import (
    EducationEntry,
    EmployerFact,
    ExperienceEntry,
    ResumeDocument,
    SchoolFact,
    UserFacts,
)
from medici.resume.schema.validate import ValidationError, validate_resume

pytestmark = pytest.mark.privacy


def test_posting_injected_employer_is_rejected():
    """A posting cannot become a new employer on the resume."""
    facts = UserFacts(
        employers=(EmployerFact(name="Loominary Labs", start="2020", end="Present"),),
        schools=(SchoolFact(name="North Example Institute", start="2016", end="2020"),),
        tools=("Python",),
    )
    resume = ResumeDocument(
        education=(
            EducationEntry(
                school="North Example Institute",
                degree="B.S.",
                dates="2016 -- 2020",
            ),
        ),
        experience=(
            ExperienceEntry(
                employer="TargetCo From Posting",
                title="Engineer",
                dates="2020 -- Present",
            ),
        ),
        skills=("Python",),
    )
    with pytest.raises(ValidationError):
        validate_resume(resume, facts)