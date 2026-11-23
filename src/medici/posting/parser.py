"""Parse job posting text into structured fields using the model client."""

from __future__ import annotations

from typing import Any

from medici.model.client import ModelClient
from medici.posting.models import Posting

UNTRUSTED_START = "<untrusted_data>"
UNTRUSTED_END = "</untrusted_data>"

POSTING_PARSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "domain": {"type": "string"},
        "title": {"type": "string"},
        "team_text": {"type": "string"},
        "named_contact": {"type": "string"},
    },
    "required": ["company", "domain", "title", "team_text", "named_contact"],
}

_FIELD_NAMES = ("company", "domain", "title", "team_text", "named_contact")


def _absent_to_none(value: str) -> str | None:
    stripped = value.strip()
    return None if not stripped else stripped


def _build_prompt(text: str) -> str:
    return (
        "Extract structured job posting fields from the posting below.\n"
        "Use an empty string for any field that is not clearly present in the text.\n"
        "Never invent or guess a company web domain; only copy a domain if it appears "
        "verbatim in the posting.\n\n"
        f"{UNTRUSTED_START}\n{text}\n{UNTRUSTED_END}"
    )


def parse_posting(text: str, client: ModelClient) -> Posting:
    """Return structured posting fields; absent values become ``None``."""
    raw = client.complete_json(_build_prompt(text), POSTING_PARSE_SCHEMA)
    fields = {name: _absent_to_none(raw[name]) for name in _FIELD_NAMES}
    return Posting(**fields)