"""Validator rejects contacts whose name or excerpt is not on the page."""

from __future__ import annotations

from medici.contacts.models import Contact
from medici.contacts.validator import is_valid_contact, validate_contacts

EMAIL = "marisol.quenby@brightloom.example.test"
PAGE = (
    "## Our team\n\n"
    f"Marisol Quenby — Technical Recruiter. Reach her at {EMAIL}\n"
    "Tobias Wrenfield — Senior Software Engineer, Fleet Software\n"
)


def test_accepts_name_and_excerpt_both_literal_on_page():
    excerpt = "Marisol Quenby — Technical Recruiter"
    assert is_valid_contact("Marisol Quenby", excerpt, PAGE)


def test_rejects_planted_name_absent_from_page():
    assert not is_valid_contact("Vesper Nightingale", "Vesper Nightingale, CEO", PAGE)


def test_rejects_excerpt_not_on_page():
    assert not is_valid_contact(
        "Marisol Quenby",
        "Marisol Quenby — Invented role text not on page",
        PAGE,
    )


def test_rejects_name_on_page_but_not_inside_excerpt():
    excerpt = "Senior Software Engineer, Fleet Software"
    assert not is_valid_contact("Marisol Quenby", excerpt, PAGE)


def test_rejects_short_name_matching_prefix_of_longer_name():
    page = "Anna Calderbrook runs the program."
    excerpt = "Anna Calderbrook runs the program."
    assert not is_valid_contact("Ann", excerpt, page)


def test_accepts_excerpt_when_whitespace_differs_from_page():
    page = "Tobias Wrenfield\nSenior   Software\nEngineer, Fleet Software"
    excerpt = "Tobias Wrenfield Senior Software Engineer, Fleet Software"
    assert is_valid_contact("Tobias Wrenfield", excerpt, page)


def test_validate_contacts_keeps_only_literals():
    raw = [
        Contact(
            name="Tobias Wrenfield",
            role_text="Senior Software Engineer",
            source_url="http://brightloom.example.test/team/",
            excerpt="Tobias Wrenfield — Senior Software Engineer, Fleet Software",
        ),
        Contact(
            name="Vesper Nightingale",
            role_text="CEO",
            source_url="http://brightloom.example.test/team/",
            excerpt="CEO and recruiter",
        ),
    ]
    kept = validate_contacts(raw, PAGE)
    assert len(kept) == 1
    assert kept[0].name == "Tobias Wrenfield"