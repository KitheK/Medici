"""Expiry list/delete agree on the boundary instant."""

from __future__ import annotations

from datetime import timedelta

from medici.store import contacts, expiry


def test_contact_at_exact_expires_at_is_deleted_and_not_listed(db_conn, frozen_now):
    row_id = contacts.save_contact(
        db_conn,
        name="Kai Boundary",
        role_text="team",
        source_url="https://careers.example.test/boundary",
        excerpt="Kai Boundary on the careers page.",
        saved=False,
        now=frozen_now - timedelta(days=30),
        identifier="kai.boundary@example.test",
    )
    got = contacts.get_contact(db_conn, row_id)
    assert got is not None
    assert got.expires_at == frozen_now
    assert contacts.list_contacts(db_conn, now=frozen_now) == []
    assert expiry.delete_expired(db_conn, now=frozen_now) == 1
    assert contacts.get_contact(db_conn, row_id) is None