"""Opt-out removes matching saved contacts, not only the suppression row."""

from __future__ import annotations

from datetime import UTC, datetime

from medici.optout.service import opt_out
from medici.store.contacts import list_contacts, save_contact

IDENTIFIER = "saved.pat@example.test"
NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)


def test_opt_out_deletes_saved_contact_matching_identifier(db_conn, suppression_key):
    save_contact(
        db_conn,
        name="Pat Saved",
        role_text="Engineer",
        source_url="https://example.test/team",
        excerpt=f"Contact {IDENTIFIER} on the team page.",
        saved=True,
        now=NOW,
        identifier=IDENTIFIER,
        suppression_key=suppression_key,
    )
    save_contact(
        db_conn,
        name="Alex Keep",
        role_text="Recruiter",
        source_url="https://example.test/hr",
        excerpt="Alex Keep alex.keep@example.test",
        saved=True,
        now=NOW,
        identifier="alex.keep@example.test",
        suppression_key=suppression_key,
    )
    assert len(list_contacts(db_conn, now=NOW)) == 2

    opt_out(db_conn, IDENTIFIER, key=suppression_key)

    remaining = list_contacts(db_conn, now=NOW)
    assert len(remaining) == 1
    assert remaining[0].name == "Alex Keep"


def test_opt_out_leaves_unsaved_rows_until_expiry(db_conn, suppression_key):
    save_contact(
        db_conn,
        name="Pat Draft",
        role_text="Engineer",
        source_url="https://example.test/team",
        excerpt=f"Pat Draft {IDENTIFIER}",
        saved=False,
        now=NOW,
        identifier=IDENTIFIER,
        suppression_key=suppression_key,
    )
    opt_out(db_conn, IDENTIFIER, key=suppression_key)
    assert len(list_contacts(db_conn, now=NOW)) == 1