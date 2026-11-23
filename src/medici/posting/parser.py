"""Parse job posting text into structured fields using the model client."""

from __future__ import annotations

import re
from typing import Any

from medici.model.client import ModelClient
from medici.posting.models import Posting

UNTRUSTED_START = "<untrusted_data>"
UNTRUSTED_END = "</untrusted_data>"
MAX_POSTING_CHARS = 100_000

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
_HOSTNAME_LABEL = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")


def _absent_to_none(value: str) -> str | None:
    stripped = value.strip()
    return None if not stripped else stripped


def _is_valid_hostname(hostname: str) -> bool:
    host = hostname.rstrip(".")
    if not host or len(host) > 253 or " " in host:
        return False
    labels = host.split(".")
    if len(labels) < 2:
        return False
    return all(_HOSTNAME_LABEL.match(label) for label in labels)


def _cap_posting_text(text: str) -> str:
    if len(text) <= MAX_POSTING_CHARS:
        return text
    return text[:MAX_POSTING_CHARS]


def _escape_untrusted_markers(text: str) -> str:
    return text.replace(UNTRUSTED_END, "&lt;/untrusted_data&gt;")


def _build_prompt(text: str) -> str:
    return (
        "Extract structured job posting fields from the posting below.\n"
        "Use an empty string for any field that is not clearly present in the text.\n"
        "Never invent or guess a company web domain; only copy a domain if it appears "
        "verbatim in the posting.\n\n"
        f"{UNTRUSTED_START}\n{text}\n{UNTRUSTED_END}"
    )


def _ground_field(name: str, value: str | None, source_text: str) -> str | None:
    if value is None:
        return None
    if name == "domain":
        if value not in source_text or not _is_valid_hostname(value):
            return None
    elif name == "named_contact" and value not in source_text:
        return None
    return value


def parse_posting(text: str, client: ModelClient) -> Posting:
    """Return structured posting fields; absent values become ``None``."""
    source_text = _cap_posting_text(text)
    prompt_text = _escape_untrusted_markers(source_text)
    raw = client.complete_json(_build_prompt(prompt_text), POSTING_PARSE_SCHEMA)
    fields: dict[str, str | None] = {}
    for name in _FIELD_NAMES:
        value = _absent_to_none(str(raw.get(name, "")))
        if name in ("domain", "named_contact"):
            value = _ground_field(name, value, source_text)
        fields[name] = value
    return Posting(**fields)