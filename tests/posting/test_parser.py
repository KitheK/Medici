"""Posting parser: structured fields from job posting text via the model client."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from medici.model.fake import FakeModelClient
from medici.posting.models import Posting
from medici.posting.parser import UNTRUSTED_END, UNTRUSTED_START, parse_posting

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "postings"
MANIFEST = FIXTURES / "manifest.json"


def _model_fields(expected: dict) -> dict[str, str]:
    """Map expected Posting fields to model JSON (empty string = absent)."""
    out: dict[str, str] = {}
    for key in ("company", "domain", "title", "team_text", "named_contact"):
        value = expected.get(key)
        out[key] = "" if value is None else str(value)
    return out


def _load_cases() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return data["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_fixture_extracts_expected_fields(case: dict) -> None:
    text = (FIXTURES / case["file"]).read_text(encoding="utf-8")
    expected = case["expected"]
    client = FakeModelClient(responses=[_model_fields(expected)])

    posting = parse_posting(text, client)

    assert posting == Posting(**expected)


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_expected_strings_appear_in_posting_text(case: dict) -> None:
    """Golden labels are grounded in the fixture text (reviewer acceptance aid)."""
    text = (FIXTURES / case["file"]).read_text(encoding="utf-8").lower()
    expected = case["expected"]
    for key in ("company", "title", "team_text", "named_contact", "domain"):
        value = expected.get(key)
        if value:
            assert str(value).lower() in text, f"{case['id']}: {key!r} not in posting text"


def test_prompt_wraps_posting_in_untrusted_data() -> None:
    body = "Job: Widget Wrangler at Example Labs"
    client = FakeModelClient(
        responses=[
            {
                "company": "Example Labs",
                "domain": "",
                "title": "Widget Wrangler",
                "team_text": "",
                "named_contact": "",
            }
        ]
    )
    parse_posting(body, client)
    prompt = client.prompts[0]
    assert UNTRUSTED_START in prompt
    assert UNTRUSTED_END in prompt
    assert body in prompt


def test_injection_posting_does_not_change_output_shape() -> None:
    """Planted instructions in the posting must not alter parser output shape."""
    path = FIXTURES / "04_injection_hostile.txt"
    text = path.read_text(encoding="utf-8")
    fixed = {
        "company": "Brightloom Robotics",
        "domain": "careers.brightloom.example.test",
        "title": "Platform Reliability Engineer",
        "team_text": "Fleet Software",
        "named_contact": "Marisol Quenby",
    }
    client = FakeModelClient(responses=[_model_fields(fixed)])
    posting = parse_posting(text, client)
    assert posting == Posting(
        company="Brightloom Robotics",
        domain="careers.brightloom.example.test",
        title="Platform Reliability Engineer",
        team_text="Fleet Software",
        named_contact="Marisol Quenby",
    )
    assert "ignore previous" in text.lower()