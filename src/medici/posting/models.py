"""Structured fields extracted from a job posting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Posting:
    company: str | None
    domain: str | None
    title: str | None
    team_text: str | None
    named_contact: str | None