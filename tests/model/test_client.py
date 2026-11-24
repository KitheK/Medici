"""Core model client: schema validation and retry."""

from __future__ import annotations

import json

import pytest

from medici.model.client import (
    InvalidModelOutputError,
    ModelError,
    SchemaDefinitionError,
    SchemaValidationError,
    TransportError,
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


def test_validate_against_schema_enforces_enum_with_type():
    schema = {"type": "string", "enum": ["a", "b"]}
    with pytest.raises(SchemaValidationError):
        validate_against_schema("c", schema)


def test_validate_against_schema_rejects_extra_properties_when_disallowed():
    schema = {
        "type": "object",
        "properties": {"x": {"type": "string"}},
        "additionalProperties": False,
    }
    with pytest.raises(SchemaValidationError):
        validate_against_schema({"x": "ok", "y": 1}, schema)


def test_validate_against_schema_enforces_min_items():
    schema = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    with pytest.raises(SchemaValidationError):
        validate_against_schema([], schema)


def test_validate_against_schema_accepts_any_of_branch():
    schema = {
        "anyOf": [
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"b": {"type": "integer"}}},
        ]
    }
    validate_against_schema({"b": 2}, schema)


def test_validate_against_schema_rejects_unsupported_keyword():
    with pytest.raises(SchemaDefinitionError):
        validate_against_schema({"x": 1}, {"type": "object", "not": {}})


def test_parse_and_validate_parses_json():
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    out = parse_and_validate('{"ok": true}', schema)
    assert out == {"ok": True}


def test_parse_and_validate_rejects_non_json():
    with pytest.raises(InvalidModelOutputError):
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


def test_request_json_with_retry_does_not_retry_transport_errors():
    calls = 0

    def fetch() -> str:
        nonlocal calls
        calls += 1
        raise TransportError("anthropic HTTP 429")

    schema = {"type": "object"}
    with pytest.raises(TransportError):
        request_json_with_retry(fetch, schema)
    assert calls == 1


def test_request_json_with_retry_does_not_retry_response_shape_errors():
    calls = 0

    def fetch() -> str:
        nonlocal calls
        calls += 1
        raise ModelError("anthropic response missing text block")

    schema = {"type": "object"}
    with pytest.raises(ModelError) as exc_info:
        request_json_with_retry(fetch, schema)
    assert not isinstance(exc_info.value, (InvalidModelOutputError, SchemaValidationError))
    assert calls == 1