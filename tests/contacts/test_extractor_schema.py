"""Rows from the model payload are schema-checked before building contacts."""

from __future__ import annotations

from medici.contacts.extractor import _contact_from_row


def test_skips_rows_that_fail_per_contact_schema():
    assert _contact_from_row({"name": "Rowan Blockwell", "role_text": "Engineer"}, "url") is None
    good = _contact_from_row(
        {
            "name": "Rowan Blockwell",
            "role_text": "Platform Engineer",
            "excerpt": "Rowan Blockwell — Platform Engineer",
        },
        "http://brightloom.example.test/about/",
    )
    assert good is not None
    assert good.name == "Rowan Blockwell"
    assert good.source_url == "http://brightloom.example.test/about/"