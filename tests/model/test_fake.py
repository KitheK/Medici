"""Fake model client for deterministic tests."""

from __future__ import annotations

import pytest

from medici.model.client import SchemaValidationError
from medici.model.fake import FakeModelClient


def test_fake_returns_queued_responses_and_records_prompts():
    schema = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}
    client = FakeModelClient(responses=[{"x": "first"}, {"x": "second"}])

    assert client.complete_json("prompt one", schema) == {"x": "first"}
    assert client.complete_json("prompt two", schema) == {"x": "second"}
    assert client.prompts == ["prompt one", "prompt two"]


def test_fake_validates_schema_before_returning():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}
    client = FakeModelClient(responses=[{"n": "not-int"}])

    with pytest.raises(SchemaValidationError):
        client.complete_json("bad", schema)