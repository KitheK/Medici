"""Anthropic Haiku client (no real network)."""

from __future__ import annotations

import json

import pytest

from medici.model.anthropic_client import HAIKU_MODEL, AnthropicModelClient
from medici.model.client import ModelError

SCHEMA = {
    "type": "object",
    "properties": {"title": {"type": "string"}},
    "required": ["title"],
}


def _ok_response(text: str) -> dict:
    return {
        "content": [{"type": "text", "text": text}],
        "usage": {"input_tokens": 11, "output_tokens": 7},
    }


def test_haiku_model_id():
    assert HAIKU_MODEL == "claude-haiku-5-5"


def test_anthropic_returns_schema_valid_json():
    calls: list[dict] = []

    def post_json(url: str, headers: dict, body: dict) -> dict:
        calls.append(body)
        return _ok_response(json.dumps({"title": "Engineer"}))

    client = AnthropicModelClient(api_key="test-key", post_json=post_json)
    out = client.complete_json("parse this posting", SCHEMA)
    assert out == {"title": "Engineer"}
    assert calls[0]["model"] == HAIKU_MODEL
    assert calls[0]["output_format"]["type"] == "json_schema"


def test_anthropic_retries_once_on_bad_output_then_raises():
    bodies: list[dict] = []

    def post_json(url: str, headers: dict, body: dict) -> dict:
        bodies.append(body)
        if len(bodies) == 1:
            return _ok_response("{not valid json")
        return _ok_response("{still bad")

    client = AnthropicModelClient(api_key="test-key", post_json=post_json)
    with pytest.raises(ModelError):
        client.complete_json("x", SCHEMA)
    assert len(bodies) == 2


def test_anthropic_requires_api_key_from_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ModelError):
        AnthropicModelClient.from_env()