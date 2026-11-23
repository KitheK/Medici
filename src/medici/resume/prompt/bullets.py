"""Bullet-level checks until E5-1 (#54) grows the shared validator."""

from __future__ import annotations

import re

from medici.resume.schema.facts import ResumeDocument, UserFacts, allowed_tools
from medici.resume.schema.validate import ValidationError

_LOWERCASE_TOOL_NAMES = frozenset(
    {
        "aws",
        "azure",
        "cuda",
        "docker",
        "go",
        "java",
        "javascript",
        "kubernetes",
        "linux",
        "node",
        "postgresql",
        "python",
        "react",
        "redis",
        "rust",
        "spark",
        "sql",
        "terraform",
    }
)
_COMMON_BULLET_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "at",
        "built",
        "for",
        "in",
        "on",
        "or",
        "shipped",
        "the",
        "to",
        "using",
        "via",
        "with",
    }
)
_WORD = re.compile(r"\b[A-Za-z][A-Za-z0-9+#.]*\b")
_METRIC = re.compile(r"\d+(?:\.\d+)?%")


def _user_bullet_texts(facts: UserFacts) -> tuple[str, ...]:
    texts: list[str] = []
    for employer in facts.employers:
        texts.extend(employer.bullets)
    for project in facts.projects:
        texts.extend(project.bullets)
    return tuple(texts)


def _all_resume_bullets(doc: ResumeDocument) -> tuple[str, ...]:
    bullets: list[str] = []
    for entry in doc.experience:
        bullets.extend(entry.bullets)
    for entry in doc.projects:
        bullets.extend(entry.bullets)
    return tuple(bullets)


def validate_bullet_content(doc: ResumeDocument, facts: UserFacts) -> None:
    """Reject bullets that cite tools or metrics the user did not provide."""
    allowed = allowed_tools(facts)
    user_bullets = _user_bullet_texts(facts)
    problems: list[str] = []

    for bullet in _all_resume_bullets(doc):
        for match in _WORD.finditer(bullet):
            token = match.group()
            folded = token.casefold()
            if folded in _COMMON_BULLET_WORDS:
                continue
            camel_case = any(char.isupper() for char in token[1:])
            looks_like_tool = camel_case or folded in _LOWERCASE_TOOL_NAMES
            if looks_like_tool and folded not in allowed:
                problems.append(f"unknown tool in bullet: {token!r}")

        for match in _METRIC.finditer(bullet):
            metric = match.group()
            if not any(metric in source for source in user_bullets):
                problems.append(f"unknown metric in bullet: {metric!r}")

    if problems:
        raise ValidationError(tuple(problems))