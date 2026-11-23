"""Typed schema for the user's own resume facts and generated resume JSON."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


def _tuple_str(values: Sequence[Any] | None) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(str(v) for v in values)


def _required_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing or empty {key!r}")
    return str(value).strip()


@dataclass(frozen=True, slots=True)
class EmployerFact:
    name: str
    title: str | None = None
    location: str | None = None
    start: str | None = None
    end: str | None = None
    bullets: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EmployerFact:
        return cls(
            name=_required_str(data, "name"),
            title=(str(data["title"]).strip() if data.get("title") else None),
            location=(str(data["location"]).strip() if data.get("location") else None),
            start=(str(data["start"]).strip() if data.get("start") else None),
            end=(str(data["end"]).strip() if data.get("end") else None),
            bullets=_tuple_str(data.get("bullets")),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name}
        if self.title:
            out["title"] = self.title
        if self.location:
            out["location"] = self.location
        if self.start:
            out["start"] = self.start
        if self.end:
            out["end"] = self.end
        if self.bullets:
            out["bullets"] = list(self.bullets)
        return out


@dataclass(frozen=True, slots=True)
class SchoolFact:
    name: str
    degree: str | None = None
    location: str | None = None
    start: str | None = None
    end: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SchoolFact:
        return cls(
            name=_required_str(data, "name"),
            degree=(str(data["degree"]).strip() if data.get("degree") else None),
            location=(str(data["location"]).strip() if data.get("location") else None),
            start=(str(data["start"]).strip() if data.get("start") else None),
            end=(str(data["end"]).strip() if data.get("end") else None),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name}
        if self.degree:
            out["degree"] = self.degree
        if self.location:
            out["location"] = self.location
        if self.start:
            out["start"] = self.start
        if self.end:
            out["end"] = self.end
        return out


@dataclass(frozen=True, slots=True)
class ProjectFact:
    name: str
    start: str | None = None
    end: str | None = None
    tools: tuple[str, ...] = ()
    bullets: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProjectFact:
        return cls(
            name=_required_str(data, "name"),
            start=(str(data["start"]).strip() if data.get("start") else None),
            end=(str(data["end"]).strip() if data.get("end") else None),
            tools=_tuple_str(data.get("tools")),
            bullets=_tuple_str(data.get("bullets")),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name}
        if self.start:
            out["start"] = self.start
        if self.end:
            out["end"] = self.end
        if self.tools:
            out["tools"] = list(self.tools)
        if self.bullets:
            out["bullets"] = list(self.bullets)
        return out


@dataclass(frozen=True, slots=True)
class UserFacts:
    employers: tuple[EmployerFact, ...]
    schools: tuple[SchoolFact, ...]
    tools: tuple[str, ...]
    projects: tuple[ProjectFact, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> UserFacts:
        employers_raw = data.get("employers")
        schools_raw = data.get("schools")
        tools_raw = data.get("tools")
        if not isinstance(employers_raw, list):
            raise ValueError("employers must be a list")
        if not isinstance(schools_raw, list):
            raise ValueError("schools must be a list")
        if not isinstance(tools_raw, list):
            raise ValueError("tools must be a list")
        projects_raw = data.get("projects") or []
        if not isinstance(projects_raw, list):
            raise ValueError("projects must be a list")
        return cls(
            employers=tuple(EmployerFact.from_dict(e) for e in employers_raw),
            schools=tuple(SchoolFact.from_dict(s) for s in schools_raw),
            tools=_tuple_str(tools_raw),
            projects=tuple(ProjectFact.from_dict(p) for p in projects_raw),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "employers": [e.to_dict() for e in self.employers],
            "schools": [s.to_dict() for s in self.schools],
            "tools": list(self.tools),
            "projects": [p.to_dict() for p in self.projects],
        }


@dataclass(frozen=True, slots=True)
class EducationEntry:
    school: str
    degree: str
    dates: str
    location: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EducationEntry:
        return cls(
            school=_required_str(data, "school"),
            degree=_required_str(data, "degree"),
            dates=_required_str(data, "dates"),
            location=(str(data["location"]).strip() if data.get("location") else None),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "school": self.school,
            "degree": self.degree,
            "dates": self.dates,
        }
        if self.location:
            out["location"] = self.location
        return out


@dataclass(frozen=True, slots=True)
class ExperienceEntry:
    employer: str
    title: str
    dates: str
    location: str | None = None
    bullets: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExperienceEntry:
        return cls(
            employer=_required_str(data, "employer"),
            title=_required_str(data, "title"),
            dates=_required_str(data, "dates"),
            location=(str(data["location"]).strip() if data.get("location") else None),
            bullets=_tuple_str(data.get("bullets")),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "employer": self.employer,
            "title": self.title,
            "dates": self.dates,
        }
        if self.location:
            out["location"] = self.location
        if self.bullets:
            out["bullets"] = list(self.bullets)
        return out


@dataclass(frozen=True, slots=True)
class ProjectEntry:
    name: str
    dates: str
    tools: tuple[str, ...] = ()
    bullets: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProjectEntry:
        return cls(
            name=_required_str(data, "name"),
            dates=_required_str(data, "dates"),
            tools=_tuple_str(data.get("tools")),
            bullets=_tuple_str(data.get("bullets")),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"name": self.name, "dates": self.dates}
        if self.tools:
            out["tools"] = list(self.tools)
        if self.bullets:
            out["bullets"] = list(self.bullets)
        return out


@dataclass(frozen=True, slots=True)
class ResumeDocument:
    """Schema-valid resume JSON produced by the model (before LaTeX render)."""

    education: tuple[EducationEntry, ...]
    experience: tuple[ExperienceEntry, ...]
    skills: tuple[str, ...]
    projects: tuple[ProjectEntry, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ResumeDocument:
        education_raw = data.get("education")
        experience_raw = data.get("experience")
        skills_raw = data.get("skills")
        if not isinstance(education_raw, list):
            raise ValueError("education must be a list")
        if not isinstance(experience_raw, list):
            raise ValueError("experience must be a list")
        if not isinstance(skills_raw, list):
            raise ValueError("skills must be a list")
        projects_raw = data.get("projects") or []
        if not isinstance(projects_raw, list):
            raise ValueError("projects must be a list")
        return cls(
            education=tuple(EducationEntry.from_dict(e) for e in education_raw),
            experience=tuple(ExperienceEntry.from_dict(e) for e in experience_raw),
            skills=_tuple_str(skills_raw),
            projects=tuple(ProjectEntry.from_dict(p) for p in projects_raw),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "education": [e.to_dict() for e in self.education],
            "experience": [e.to_dict() for e in self.experience],
            "skills": list(self.skills),
            "projects": [p.to_dict() for p in self.projects],
        }


def allowed_employers(facts: UserFacts) -> frozenset[str]:
    return frozenset(e.name for e in facts.employers)


def allowed_schools(facts: UserFacts) -> frozenset[str]:
    return frozenset(s.name for s in facts.schools)


def allowed_projects(facts: UserFacts) -> frozenset[str]:
    return frozenset(p.name for p in facts.projects)


def allowed_tools(facts: UserFacts) -> frozenset[str]:
    tools = {t.casefold() for t in facts.tools}
    for project in facts.projects:
        tools.update(t.casefold() for t in project.tools)
    return frozenset(tools)


def allowed_dates(facts: UserFacts) -> frozenset[str]:
    parts: set[str] = set()

    def add(value: str | None) -> None:
        if value and value.strip():
            parts.add(value.strip())

    for employer in facts.employers:
        add(employer.start)
        add(employer.end)
    for school in facts.schools:
        add(school.start)
        add(school.end)
    for project in facts.projects:
        add(project.start)
        add(project.end)
    return frozenset(parts)