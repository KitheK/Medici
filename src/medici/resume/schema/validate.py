"""Validate generated resume JSON against the user's own facts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from medici.resume.schema.facts import (
    EmployerFact,
    ProjectFact,
    ResumeDocument,
    SchoolFact,
    UserFacts,
    allowed_tools,
)

# Range separators only — \bto\b so "October" is never split.
_DATE_SPLIT = re.compile(
    r"\s*(?:--|—|–)\s*|\s+-\s+|\s+\bto\b\s+",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_TOOL_AFTER_PREP = re.compile(
    r"\b(?:using|with|via|in|on)\s+([A-Za-z][A-Za-z0-9+#./-]*)",
    re.IGNORECASE,
)


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


def date_tokens(dates: str) -> tuple[str, ...]:
    text = dates.strip()
    if not text:
        return ()
    parts = [p.strip() for p in _DATE_SPLIT.split(text) if p.strip()]
    return tuple(parts) if parts else (text,)


def _dates_for_employer(employer: EmployerFact) -> frozenset[str]:
    out: set[str] = set()
    if employer.start:
        out.add(employer.start.strip())
    if employer.end:
        out.add(employer.end.strip())
    return frozenset(out)


def _dates_for_school(school: SchoolFact) -> frozenset[str]:
    out: set[str] = set()
    if school.start:
        out.add(school.start.strip())
    if school.end:
        out.add(school.end.strip())
    return frozenset(out)


def _dates_for_project(project: ProjectFact) -> frozenset[str]:
    out: set[str] = set()
    if project.start:
        out.add(project.start.strip())
    if project.end:
        out.add(project.end.strip())
    return frozenset(out)


def _tools_for_project(project: ProjectFact, global_tools: frozenset[str]) -> frozenset[str]:
    if project.tools:
        return frozenset(t.casefold() for t in project.tools)
    return global_tools


def _allowed_numbers(facts: UserFacts) -> frozenset[str]:
    found: set[str] = set()
    for employer in facts.employers:
        for bullet in employer.bullets:
            found.update(_NUMBER.findall(bullet))
    for project in facts.projects:
        for bullet in project.bullets:
            found.update(_NUMBER.findall(bullet))
    return frozenset(found)


def _allowed_bullet_texts(facts: UserFacts) -> frozenset[str]:
    texts: set[str] = set()
    for employer in facts.employers:
        texts.update(employer.bullets)
    for project in facts.projects:
        texts.update(project.bullets)
    return frozenset(texts)


def _validate_date_tokens(
    dates: str,
    allowed: frozenset[str],
    problems: list[str],
    *,
    context: str,
) -> None:
    for token in date_tokens(dates):
        if token not in allowed:
            problems.append(f"unknown date: {token!r} in {context}")


def _tool_spans_in_text(text: str, tools: frozenset[str]) -> list[tuple[int, int]]:
    """Return non-overlapping spans for allowed tool names as they appear in text."""
    names = sorted({t for t in tools if t}, key=len, reverse=True)
    spans: list[tuple[int, int]] = []
    lowered = text.casefold()
    for name in names:
        needle = name.casefold()
        start = 0
        while True:
            idx = lowered.find(needle, start)
            if idx < 0:
                break
            end = idx + len(needle)
            if (idx == 0 or not lowered[idx - 1].isalnum()) and (
                end == len(lowered) or not lowered[end].isalnum()
            ):
                overlaps = any(not (end <= a or idx >= b) for a, b in spans)
                if not overlaps:
                    spans.append((idx, end))
            start = idx + 1
    return spans


def _unknown_tools_in_bullet(text: str, allowed_tools_fold: frozenset[str]) -> list[str]:
    unknown: list[str] = []
    for match in _TOOL_AFTER_PREP.finditer(text):
        token = match.group(1)
        if token.casefold() not in allowed_tools_fold:
            unknown.append(token)
    spans = _tool_spans_in_text(text, allowed_tools_fold)
    masked = list(text)
    for start, end in sorted(spans, reverse=True):
        for i in range(start, end):
            masked[i] = " "
    stripped = "".join(masked)
    for match in re.finditer(r"\b([A-Za-z][A-Za-z0-9+#./-]{1,})\b", stripped):
        token = match.group(1)
        if match.start() == 0 or (match.start() > 0 and stripped[match.start() - 1] in ".!?"):
            continue
        if token.casefold() in allowed_tools_fold:
            continue
        if token.lower() in {"and", "the", "for", "with", "using", "via", "on", "in", "to"}:
            continue
        if token[0].isupper() and token.casefold() not in allowed_tools_fold:
            unknown.append(token)
    return unknown


def _unknown_numbers_in_bullet(text: str, allowed_numbers: frozenset[str]) -> list[str]:
    if not allowed_numbers:
        found = _NUMBER.findall(text)
        return found
    return [n for n in _NUMBER.findall(text) if n not in allowed_numbers]


def _validate_bullets(
    bullets: tuple[str, ...],
    allowed_tools_fold: frozenset[str],
    allowed_numbers: frozenset[str],
    allowed_exact: frozenset[str],
    problems: list[str],
    *,
    context: str,
) -> None:
    for bullet in bullets:
        if bullet in allowed_exact:
            continue
        for token in _unknown_tools_in_bullet(bullet, allowed_tools_fold):
            problems.append(f"unknown tool: {token!r} in {context} bullet")
        for num in _unknown_numbers_in_bullet(bullet, allowed_numbers):
            problems.append(f"unknown number: {num!r} in {context} bullet")


def validate_resume(
    resume: ResumeDocument | Mapping[str, object],
    facts: UserFacts | Mapping[str, object],
) -> None:
    """Raise ValidationError when the resume cites facts the user did not provide."""
    doc = _parse_resume(resume)
    user = _parse_facts(facts)

    employers_by_name = {e.name: e for e in user.employers}
    schools_by_name = {s.name: s for s in user.schools}
    projects_by_name = {p.name: p for p in user.projects}
    global_tools = allowed_tools(user)
    allowed_numbers = _allowed_numbers(user)
    allowed_bullets = _allowed_bullet_texts(user)

    problems: list[str] = []

    for entry in doc.experience:
        employer = employers_by_name.get(entry.employer)
        if employer is None:
            problems.append(f"unknown employer: {entry.employer!r}")
            continue
        if employer.title is not None and entry.title != employer.title:
            problems.append(
                f"unknown title: {entry.title!r} for employer {entry.employer!r} "
                f"(expected {employer.title!r})"
            )
        _validate_date_tokens(
            entry.dates,
            _dates_for_employer(employer),
            problems,
            context=f"experience at {entry.employer!r}",
        )
        _validate_bullets(
            entry.bullets,
            global_tools,
            allowed_numbers,
            allowed_bullets,
            problems,
            context=f"experience at {entry.employer!r}",
        )

    for entry in doc.education:
        school = schools_by_name.get(entry.school)
        if school is None:
            problems.append(f"unknown school: {entry.school!r}")
            continue
        if school.degree is not None and entry.degree != school.degree:
            problems.append(
                f"unknown degree: {entry.degree!r} for school {entry.school!r} "
                f"(expected {school.degree!r})"
            )
        _validate_date_tokens(
            entry.dates,
            _dates_for_school(school),
            problems,
            context=f"education at {entry.school!r}",
        )

    for entry in doc.projects:
        project = projects_by_name.get(entry.name)
        if project is None:
            problems.append(f"unknown project: {entry.name!r}")
            continue
        _validate_date_tokens(
            entry.dates,
            _dates_for_project(project),
            problems,
            context=f"project {entry.name!r}",
        )
        project_tools = _tools_for_project(project, global_tools)
        for tool in entry.tools:
            if tool.casefold() not in project_tools:
                problems.append(f"unknown tool: {tool!r} in project {entry.name!r}")
        _validate_bullets(
            entry.bullets,
            global_tools,
            allowed_numbers,
            {b for b in allowed_bullets if b in project.bullets},
            problems,
            context=f"project {entry.name!r}",
        )

    for skill in doc.skills:
        if skill.casefold() not in global_tools:
            problems.append(f"unknown tool: {skill!r} in skills")

    if problems:
        raise ValidationError(tuple(problems))