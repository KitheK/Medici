"""Database bootstrap."""

from __future__ import annotations

from medici.store.db import connect, init_schema


def test_init_schema_creates_contacts_and_suppressions_tables():
    conn = connect(":memory:")
    init_schema(conn)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    }
    assert "contacts" in tables
    assert "suppressions" in tables
    conn.close()