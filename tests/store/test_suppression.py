"""Suppression table stores only HMACs of identifiers."""

from __future__ import annotations

import pytest

from medici.store import suppression

IDENTIFIER = "morgan.rivera@example.test"


def test_suppression_row_is_hmac_not_raw_identifier(db_conn, suppression_key):
    suppression.add_suppression(db_conn, IDENTIFIER, key=suppression_key)
    rows = db_conn.execute("SELECT identifier_hmac FROM suppressions").fetchall()
    assert len(rows) == 1
    stored = rows[0][0]
    assert stored != IDENTIFIER
    assert "@" not in stored
    assert stored == suppression.identifier_hmac(IDENTIFIER, suppression_key)


def test_is_suppressed_matches_after_add(db_conn, suppression_key):
    assert not suppression.is_suppressed(db_conn, IDENTIFIER, key=suppression_key)
    suppression.add_suppression(db_conn, IDENTIFIER, key=suppression_key)
    assert suppression.is_suppressed(db_conn, IDENTIFIER, key=suppression_key)


def test_different_identifiers_get_different_hmacs(suppression_key):
    a = suppression.identifier_hmac("pat.one@example.test", suppression_key)
    b = suppression.identifier_hmac("pat.two@example.test", suppression_key)
    assert a != b


@pytest.mark.privacy
def test_suppression_table_never_contains_plain_identifier(db_conn, suppression_key):
    """Privacy: opt-out rows must not store the raw identifier."""
    identifier = "quinn.north@example.invalid"
    suppression.add_suppression(db_conn, identifier, key=suppression_key)
    blob = db_conn.execute("SELECT identifier_hmac FROM suppressions").fetchone()[0]
    assert identifier not in blob
    assert blob == suppression.identifier_hmac(identifier, suppression_key)
    assert len(blob) == 64