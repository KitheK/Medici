"""Expiry job deletes rows past expires_at."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from medici.store import contacts, expiry


def test_delete_expired_removes_only_past_rows(db_conn):
    anchor = datetime(2026, 6, 1, tzinfo=UTC)
    old_id = contacts.save_contact(
        db_conn,
        name="Dana Fictional",
        role_text="team",
        source_url="https://careers.example.test/old",
        excerpt="Dana Fictional on the team page.",
        saved=False,
        now=anchor - timedelta(days=31),
    )
    fresh_id = contacts.save_contact(
        db_conn,
        name="Ellis Sample",
        role_text="team",
        source_url="https://careers.example.test/new",
        excerpt="Ellis Sample joined recently.",
        saved=False,
        now=anchor - timedelta(days=5),
    )
    deleted = expiry.delete_expired(db_conn, now=anchor)
    assert deleted == 1
    assert contacts.get_contact(db_conn, old_id) is None
    assert contacts.get_contact(db_conn, fresh_id) is not None


def test_delete_expired_on_empty_db(db_conn, frozen_now):
    assert expiry.delete_expired(db_conn, now=frozen_now) == 0