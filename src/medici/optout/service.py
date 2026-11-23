"""Record opt-outs and drop suppressed people from pipeline output."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

from medici.store import suppression


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
    suppression.add_suppression(conn, identifier, key=key)


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
        if not suppression.is_suppressed(conn, person.identifier, key=key)
    ]