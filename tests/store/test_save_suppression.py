"""save_contact rejects identifiers on the suppression list."""

from __future__ import annotations

import pytest

from medici.store import contacts, suppression

IDENTIFIER = "jordan.sandbox@example.test"


def test_save_contact_rejects_suppressed_identifier(db_conn, frozen_now, suppression_key):
    suppression.add_suppression(db_conn, IDENTIFIER, key=suppression_key)
    with pytest.raises(contacts.SuppressedContactError):
        contacts.save_contact(
            db_conn,
            name="Jordan Sandbox",
            role_text="team",
            source_url="https://about.example.test/team",
            excerpt="Jordan Sandbox builds tools.",
            saved=False,
            now=frozen_now,
            identifier=IDENTIFIER,
            suppression_key=suppression_key,
        )
    assert contacts.list_contacts(db_conn, now=frozen_now) == []


def test_save_contact_without_identifier_skips_suppression_check(
    db_conn, frozen_now, suppression_key
):
    suppression.add_suppression(db_conn, IDENTIFIER, key=suppression_key)
    row_id = contacts.save_contact(
        db_conn,
        name="Jordan Sandbox",
        role_text="team",
        source_url="https://about.example.test/team",
        excerpt="Jordan Sandbox builds tools.",
        saved=False,
        now=frozen_now,
    )
    assert contacts.get_contact(db_conn, row_id) is not None