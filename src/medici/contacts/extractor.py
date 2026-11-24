"""Extract named people from a fetched page using the model client."""

from __future__ import annotations

from typing import Any

from medici.contacts.models import Contact
from medici.contacts.validator import validate_contacts
from medici.fetch.fetcher import Page
from medici.model.client import (
    SYSTEM_PROMPT,
    ModelClient,
    SchemaValidationError,
    validate_against_schema,
)

CONTACT_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "contacts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role_text": {"type": "string"},
                    "excerpt": {"type": "string"},
                },
                "required": ["name", "role_text", "excerpt"],
            },
        }
    },
    "required": ["contacts"],
}

_CONTACT_ROW_SCHEMA: dict[str, Any] = CONTACT_EXTRACTION_SCHEMA["properties"]["contacts"]["items"]

_UNTRUSTED_CLOSER = "</untrusted_data>"

_EXTRACTION_INSTRUCTIONS = (
    "List every named person on the page. For each person return their name, role or title text, "
    "and a short excerpt copied verbatim from the page that mentions them."
)


def _sanitize_page_for_prompt(page_markdown: str) -> str:
    return page_markdown.replace(_UNTRUSTED_CLOSER, "&lt;/untrusted_data&gt;")


def build_extraction_prompt(page_markdown: str) -> str:
    """Build a prompt with page text in an untrusted-data block."""
    safe_text = _sanitize_page_for_prompt(page_markdown)
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{_EXTRACTION_INSTRUCTIONS}\n\n"
        f"<untrusted_data>\n{safe_text}\n</untrusted_data>"
    )


def _contact_from_row(row: Any, source_url: str) -> Contact | None:
    try:
        validate_against_schema(row, _CONTACT_ROW_SCHEMA)
    except SchemaValidationError:
        return None
    if not isinstance(row, dict):
        return None
    return Contact(
        name=row["name"],
        role_text=row["role_text"],
        source_url=source_url,
        excerpt=row["excerpt"],
    )


def extract_contacts(
    page: Page,
    client: ModelClient,
    *,
    schema: dict[str, Any] | None = None,
) -> list[Contact]:
    """Return contacts with source URL and excerpt; drop rows that fail excerpt validation."""
    prompt = build_extraction_prompt(page.markdown)
    payload = client.complete_json(prompt, schema or CONTACT_EXTRACTION_SCHEMA)
    raw: list[Contact] = []
    for row in payload.get("contacts", []):
        contact = _contact_from_row(row, page.url)
        if contact is not None:
            raw.append(contact)
    return validate_contacts(raw, page.markdown)