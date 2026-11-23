"""Call the model client and validate resume output against user facts."""

from __future__ import annotations

from collections.abc import Mapping

from medici.model.client import ModelClient, ModelError
from medici.resume.prompt.prompt import RESUME_JSON_SCHEMA, build_resume_prompt
from medici.resume.schema.facts import (
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeDocument,
    UserFacts,
)
from medici.resume.schema.validate import ValidationError, validate_resume


def facts_to_resume_document(facts: UserFacts) -> ResumeDocument:
    """Deterministic baseline resume JSON built only from user facts (no model)."""
    education = tuple(
        EducationEntry(
            school=school.name,
            degree=school.degree or "",
            dates=_format_dates(school.start, school.end),
            location=school.location,
        )
        for school in facts.schools
    )
    experience = tuple(
        ExperienceEntry(
            employer=employer.name,
            title=employer.title or "",
            dates=_format_dates(employer.start, employer.end),
            location=employer.location,
            bullets=employer.bullets,
        )
        for employer in facts.employers
    )
    projects = tuple(
        ProjectEntry(
            name=project.name,
            dates=_format_dates(project.start, project.end),
            tools=project.tools,
            bullets=project.bullets,
        )
        for project in facts.projects
    )
    return ResumeDocument(
        education=education,
        experience=experience,
        skills=facts.tools,
        projects=projects,
    )


def _format_dates(start: str | None, end: str | None) -> str:
    if start and end:
        return f"{start} -- {end}"
    if start:
        return start
    if end:
        return end
    return ""


def generate_resume(
    facts: UserFacts | Mapping[str, object],
    client: ModelClient,
    posting: str | None = None,
) -> ResumeDocument:
    """Return schema- and fact-valid resume JSON from the model."""
    user = facts if isinstance(facts, UserFacts) else UserFacts.from_dict(facts)
    prompt = build_resume_prompt(user, posting)
    last_validation: ValidationError | None = None
    for _ in range(2):
        raw = client.complete_json(prompt, RESUME_JSON_SCHEMA)
        doc = ResumeDocument.from_dict(raw)
        try:
            validate_resume(doc, user)
        except ValidationError as exc:
            last_validation = exc
            continue
        return doc
    if last_validation is not None:
        raise last_validation
    raise ModelError("model returned unusable resume JSON")