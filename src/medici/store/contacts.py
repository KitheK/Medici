"""Save and read contacts; every row carries expires_at."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

UNSAVED_RETENTION_DAYS = 30
SAVED_RETENTION_DAYS = 180


@dataclass(frozen=True, slots=True)
class StoredContact:
    id: int
    name: str
    role_text: str
    source_url: str
    excerpt: str
    saved: bool
    expires_at: datetime
    created_at: datetime


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


def expires_at_for(*, saved: bool, now: datetime) -> datetime:
    days = SAVED_RETENTION_DAYS if saved else UNSAVED_RETENTION_DAYS
    return now + timedelta(days=days)


def save_contact(
    conn: sqlite3.Connection,
    *,
    name: str,
    role_text: str,
    source_url: str,
    excerpt: str,
    saved: bool,
    now: datetime,
) -> int:
    expires = expires_at_for(saved=saved, now=now)
    created = _iso(now)
    cur = conn.execute(
        """
        INSERT INTO contacts (name, role_text, source_url, excerpt, saved, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, role_text, source_url, excerpt, int(saved), _iso(expires), created),
    )
    conn.commit()
    return int(cur.lastrowid)


def _row_to_contact(row: sqlite3.Row) -> StoredContact:
    return StoredContact(
        id=int(row["id"]),
        name=row["name"],
        role_text=row["role_text"],
        source_url=row["source_url"],
        excerpt=row["excerpt"],
        saved=bool(row["saved"]),
        expires_at=_parse(row["expires_at"]),
        created_at=_parse(row["created_at"]),
    )


def get_contact(conn: sqlite3.Connection, contact_id: int) -> StoredContact | None:
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if row is None:
        return None
    return _row_to_contact(row)


def list_contacts(conn: sqlite3.Connection, *, now: datetime | None = None) -> list[StoredContact]:
    if now is None:
        rows = conn.execute("SELECT * FROM contacts ORDER BY id").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE expires_at > ? ORDER BY id",
            (_iso(now),),
        ).fetchall()
    return [_row_to_contact(r) for r in rows]