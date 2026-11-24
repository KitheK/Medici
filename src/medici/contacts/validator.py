"""Reject contacts whose name or excerpt is not literally on the page."""

from __future__ import annotations

import re

from medici.contacts.models import Contact


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _name_at_word_boundary(name: str, text: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(name) + r"(?!\w)"
    return re.search(pattern, text) is not None


def is_valid_contact(name: str, excerpt: str, page_text: str) -> bool:
    """Return True when the name appears in the excerpt and the excerpt is on the page."""
    if not name or not excerpt:
        return False
    norm_excerpt = _normalize_whitespace(excerpt)
    if not _name_at_word_boundary(name, norm_excerpt):
        return False
    norm_page = _normalize_whitespace(page_text)
    return norm_excerpt in norm_page


def validate_contacts(contacts: list[Contact], page_text: str) -> list[Contact]:
    """Keep only contacts whose name and excerpt are present in ``page_text``."""
    return [c for c in contacts if is_valid_contact(c.name, c.excerpt, page_text)]