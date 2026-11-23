"""Opt-out table: HMAC of identifier only, never the raw value."""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from datetime import UTC, datetime

SUPPRESSION_KEY_ENV = "MEDICI_SUPPRESSION_KEY"


def suppression_key_from_env() -> bytes:
    raw = os.environ.get(SUPPRESSION_KEY_ENV)
    if not raw:
        msg = f"{SUPPRESSION_KEY_ENV} must be set for suppression operations"
        raise RuntimeError(msg)
    return raw.encode("utf-8")


def identifier_hmac(identifier: str, key: bytes) -> str:
    normalized = identifier.strip().lower()
    return hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def add_suppression(
    conn: sqlite3.Connection,
    identifier: str,
    *,
    key: bytes | None = None,
    now: datetime | None = None,
) -> None:
    hkey = key if key is not None else suppression_key_from_env()
    if now is None:
        now = datetime.now(UTC)
    digest = identifier_hmac(identifier, hkey)
    conn.execute(
        """
        INSERT OR IGNORE INTO suppressions (identifier_hmac, created_at)
        VALUES (?, ?)
        """,
        (digest, now.astimezone(UTC).isoformat()),
    )
    conn.commit()


def is_suppressed(
    conn: sqlite3.Connection,
    identifier: str,
    *,
    key: bytes | None = None,
) -> bool:
    hkey = key if key is not None else suppression_key_from_env()
    digest = identifier_hmac(identifier, hkey)
    row = conn.execute(
        "SELECT 1 FROM suppressions WHERE identifier_hmac = ?",
        (digest,),
    ).fetchone()
    return row is not None