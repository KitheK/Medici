"""Delete contact rows whose expires_at is in the past."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def delete_expired(conn: sqlite3.Connection, *, now: datetime) -> int:
    """Remove contacts with expires_at strictly before ``now``. Returns rows deleted."""
    cur = conn.execute(
        "DELETE FROM contacts WHERE expires_at < ?",
        (_iso(now),),
    )
    conn.commit()
    return int(cur.rowcount)