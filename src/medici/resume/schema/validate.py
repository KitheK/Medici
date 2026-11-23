"""Validate generated resume JSON against the user's own facts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from medici.resume.schema.facts import (
    ResumeDocument,
    UserFacts,
    allowed_dates,
    allowed_employers,
    allowed_projects,
    allowed_schools,
    allowed_tools,
)

_DATE_SPLIT = re.compile(r"\s*(?:--|—|–|-|to)\s*", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ValidationError(ValueError):
    """Resume JSON includes a fact not supplied by the user."""

    problems: tuple[str, ...]

    def __str__(self) -> str:
        return "; ".join(self.problems)


def _parse_resume(resume: ResumeDocument | Mapping[str, object]) -> ResumeDocument:
    if isinstance(resume, ResumeDocument):
        return resume
    return ResumeDocument.from_dict(resume)


def _parse_facts(facts: UserFacts | Mapping[str, object]) -> UserFacts:
    if isinstance(facts, UserFacts):
        return facts
    return UserFacts.from_dict(facts)


def _date_tokens(dates: str) -> tuple[str, ...]:
    text = dates.strip()
    if not text:
        return ()
    parts = [p.strip() for p in _DATE_SPLIT.split(text) if p.strip()]
    return tuple(parts) if parts else (text,)


def validate_resume(
    resume: ResumeDocument | Mapping[str, object],
    facts: UserFacts | Mapping[str, object],
) -> None:
    """Raise ValidationError when the resume cites facts the user did not provide."""
    doc = _parse_resume(resume)
    user = _parse_facts(facts)

    employers = allowed_employers(user)
    schools = allowed_schools(user)
    projects = allowed_projects(user)
    tools = allowed_tools(user)
    dates = allowed_dates(user)

    problems: list[str] = []

    for entry in doc.experience:
        if entry.employer not in employers:
            problems.append(f"unknown employer: {entry.employer!r}")
        for token in _date_tokens(entry.dates):
            if token not in dates:
                problems.append(f"unknown date: {token!r} in experience")

    for entry in doc.education:
        if entry.school not in schools:
            problems.append(f"unknown school: {entry.school!r}")
        for token in _date_tokens(entry.dates):
            if token not in dates:
                problems.append(f"unknown date: {token!r} in education")

    for entry in doc.projects:
        if entry.name not in projects:
            problems.append(f"unknown project: {entry.name!r}")
        for token in _date_tokens(entry.dates):
            if token not in dates:
                problems.append(f"unknown date: {token!r} in project")
        for tool in entry.tools:
            if tool.casefold() not in tools:
                problems.append(f"unknown tool: {tool!r} in project")

    for skill in doc.skills:
        if skill.casefold() not in tools:
            problems.append(f"unknown tool: {skill!r} in skills")

    if problems:
        raise ValidationError(tuple(problems))