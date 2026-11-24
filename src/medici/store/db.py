"""SQLite connection and schema."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import overload


@overload
def connect(path: str) -> sqlite3.Connection: ...


@overload
def connect(path: Path) -> sqlite3.Connection: ...


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


CONTACTS_DDL = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role_text TEXT NOT NULL,
    source_url TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    saved INTEGER NOT NULL DEFAULT 0 CHECK (saved IN (0, 1)),
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

SUPPRESSIONS_DDL = """
CREATE TABLE IF NOT EXISTS suppressions (
    identifier_hmac TEXT PRIMARY KEY NOT NULL,
    created_at TEXT NOT NULL
);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(CONTACTS_DDL + SUPPRESSIONS_DDL)
    conn.commit()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise