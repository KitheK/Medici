"""Record opt-outs and drop suppressed people from pipeline output."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

from medici.store import suppression


def canonicalize_identifier(raw: str) -> str:
    """Normalize opt-out keys so mixed-case or mailto forms hash identically."""
    value = raw.strip()
    if not value:
        return value
    if value.lower().startswith("mailto:"):
        value = value[7:].strip()
    if value.endswith("/") and "@" in value:
        value = value.rstrip("/")
    if value.lower().startswith(("http://", "https://")):
        return value.rstrip("/").lower()
    return value.strip().lower()


def _delete_saved_contacts_for_identifier(conn: sqlite3.Connection, canonical: str) -> None:
    """Drop saved rows that match the opt-out identifier (email in excerpt or name)."""
    if "@" in canonical:
        conn.execute(
            "DELETE FROM contacts WHERE saved = 1 AND instr(lower(excerpt), ?) > 0",
            (canonical,),
        )
    else:
        conn.execute(
            "DELETE FROM contacts WHERE saved = 1 AND lower(trim(name)) = ?",
            (canonical,),
        )
    conn.commit()


@dataclass(frozen=True, slots=True)
class OutputPerson:
    """A person eligible to appear in user-facing output (pre- or post-cap)."""

    name: str
    role_label: str
    source_url: str
    excerpt: str
    identifier: str


def opt_out(
    conn: sqlite3.Connection,
    identifier: str,
    *,
    key: bytes | None = None,
) -> None:
    """Store an opt-out as an HMAC in the suppression table; never the raw identifier."""
    canonical = canonicalize_identifier(identifier)
    suppression.add_suppression(conn, canonical, key=key)
    _delete_saved_contacts_for_identifier(conn, canonical)


def exclude_suppressed(
    conn: sqlite3.Connection,
    people: Sequence[OutputPerson],
    *,
    key: bytes | None = None,
) -> list[OutputPerson]:
    """Return only people who are not on the suppression list."""
    return [
        person
        for person in people
        if not suppression.is_suppressed(
            conn, canonicalize_identifier(person.identifier), key=key
        )
    ]