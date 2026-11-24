"""Contact records extracted from fetched pages."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    name: str
    role_text: str
    source_url: str
    excerpt: str