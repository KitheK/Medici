"""Core model client: schema validation and retry."""

from __future__ import annotations

import json

import pytest

from medici.model.client import (
    ModelError,
    SchemaValidationError,
    parse_and_validate,
    request_json_with_retry,
    validate_against_schema,
)


def test_validate_against_schema_accepts_matching_object():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    validate_against_schema({"name": "Ada"}, schema)


def test_validate_against_schema_rejects_wrong_type():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    with pytest.raises(SchemaValidationError):
        validate_against_schema({"name": 1}, schema)


def test_validate_against_schema_requires_fields():
    schema = {
        "type": "object",
        "properties": {"a": {"type": "string"}},
        "required": ["a"],
    }
    with pytest.raises(SchemaValidationError):
        validate_against_schema({}, schema)


def test_parse_and_validate_parses_json():
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    out = parse_and_validate('{"ok": true}', schema)
    assert out == {"ok": True}


def test_parse_and_validate_rejects_non_json():
    with pytest.raises(ModelError):
        parse_and_validate("not json", {"type": "object"})


def test_request_json_with_retry_succeeds_first_try():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
    calls: list[int] = []

    def fetch() -> str:
        calls.append(1)
        return '{"n": 2}'

    assert request_json_with_retry(fetch, schema) == {"n": 2}
    assert len(calls) == 1


def test_request_json_with_retry_retries_once_then_succeeds():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
    responses = ['{"n": "two"}', '{"n": 2}']
    calls: list[int] = []

    def fetch() -> str:
        calls.append(1)
        return responses[len(calls) - 1]

    assert request_json_with_retry(fetch, schema) == {"n": 2}
    assert len(calls) == 2


def test_request_json_with_retry_raises_after_two_bad_outputs():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}

    def fetch() -> str:
        return "still not json"

    with pytest.raises(ModelError):
        request_json_with_retry(fetch, schema)


def test_request_json_with_retry_never_loops_more_than_twice():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
    calls = 0

    def fetch() -> str:
        nonlocal calls
        calls += 1
        return json.dumps({"n": "bad"})

    with pytest.raises(ModelError):
        request_json_with_retry(fetch, schema)
    assert calls == 2