"""Opt-out service and output filtering."""

from __future__ import annotations

from medici.optout.service import OutputPerson, exclude_suppressed, opt_out
from medici.store import suppression

IDENTIFIER = "pat.opt@example.test"
OTHER = "sam.keep@example.test"


def _person(name: str, identifier: str) -> OutputPerson:
    return OutputPerson(
        name=name,
        role_label="team",
        source_url="https://example.test/team",
        excerpt=f"{name} builds things.",
        identifier=identifier,
    )


def test_opt_out_records_hmac_not_plain_identifier(db_conn, suppression_key):
    opt_out(db_conn, IDENTIFIER, key=suppression_key)
    rows = db_conn.execute("SELECT identifier_hmac FROM suppressions").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == suppression.identifier_hmac(IDENTIFIER, suppression_key)
    assert IDENTIFIER not in rows[0][0]


def test_suppressed_person_never_appears_in_output(db_conn, suppression_key):
    people = [
        _person("Pat Opt", IDENTIFIER),
        _person("Sam Keep", OTHER),
    ]
    assert [p.identifier for p in exclude_suppressed(db_conn, people, key=suppression_key)] == [
        IDENTIFIER,
        OTHER,
    ]

    opt_out(db_conn, IDENTIFIER, key=suppression_key)
    visible_after = exclude_suppressed(db_conn, people, key=suppression_key)
    assert [p.identifier for p in visible_after] == [OTHER]
    assert all(p.identifier != IDENTIFIER for p in visible_after)


def test_exclude_suppressed_treats_identifier_case_insensitively(db_conn, suppression_key):
    opt_out(db_conn, IDENTIFIER.upper(), key=suppression_key)
    people = [_person("Pat Opt", IDENTIFIER)]
    assert exclude_suppressed(db_conn, people, key=suppression_key) == []