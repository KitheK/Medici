"""Identifier canonicalization before suppression hashing."""

from __future__ import annotations

from medici.optout.service import OutputPerson, canonicalize_identifier, exclude_suppressed, opt_out

IDENTIFIER = "pat.opt@example.test"


def _person(identifier: str) -> OutputPerson:
    return OutputPerson(
        name="Pat Opt",
        role_label="team",
        source_url="https://example.test/team",
        excerpt="Pat Opt pat.opt@example.test",
        identifier=identifier,
    )


def test_canonicalize_identifier_strips_mailto_and_case():
    raw = "  MAILTO:Pat.Opt@Example.TEST/  "
    assert canonicalize_identifier(raw) == IDENTIFIER


def test_opt_out_with_mixed_case_form_suppresses_canonical_output_identifier(
    db_conn, suppression_key
):
    opt_out(db_conn, "MAILTO:Pat.Opt@Example.TEST", key=suppression_key)
    people = [_person(IDENTIFIER)]
    assert exclude_suppressed(db_conn, people, key=suppression_key) == []