"""Contacts persist with mandatory expires_at."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest

from medici.store import contacts


def test_unsaved_contact_gets_thirty_day_expiry(db_conn, frozen_now):
    row_id = contacts.save_contact(
        db_conn,
        name="Avery Lattice",
        role_text="Engineering",
        source_url="https://careers.example.test/open",
        excerpt="Avery Lattice leads platform engineering.",
        saved=False,
        now=frozen_now,
    )
    got = contacts.get_contact(db_conn, row_id)
    assert got is not None
    assert got.expires_at == frozen_now + timedelta(days=30)


def test_saved_contact_gets_longer_expiry(db_conn, frozen_now):
    row_id = contacts.save_contact(
        db_conn,
        name="Blair Widget",
        role_text="Recruiting",
        source_url="https://about.example.test/team",
        excerpt="Blair Widget supports hiring.",
        saved=True,
        now=frozen_now,
    )
    got = contacts.get_contact(db_conn, row_id)
    assert got is not None
    assert got.expires_at == frozen_now + timedelta(days=180)


def test_insert_without_expires_at_is_rejected(db_conn, frozen_now):
    """Schema and API always set expires_at; direct SQL without it must fail."""
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO contacts (name, role_text, source_url, excerpt, saved, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                "Casey Null",
                "team",
                "https://example.test",
                "excerpt",
                frozen_now.isoformat(),
            ),
        )
        db_conn.commit()