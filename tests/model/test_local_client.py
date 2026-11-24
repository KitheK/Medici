"""Local model client (no real network)."""

from __future__ import annotations

import json

import pytest

from medici.model.client import ModelError
from medici.model.local_client import LocalModelClient

SCHEMA = {
    "type": "object",
    "properties": {"count": {"type": "integer"}},
    "required": ["count"],
}


def test_local_returns_schema_valid_json():
    posts: list[dict] = []

    def post_json(url: str, headers: dict, body: dict) -> dict:
        posts.append(body)
        return {"message": {"content": json.dumps({"count": 3})}}

    client = LocalModelClient(base_url="http://127.0.0.1:9999", post_json=post_json)
    assert client.complete_json("count things", SCHEMA) == {"count": 3}
    assert posts[0]["schema"] == SCHEMA


def test_local_retries_once_then_raises():
    n = 0

    def post_json(url: str, headers: dict, body: dict) -> dict:
        nonlocal n
        n += 1
        return {"message": {"content": '{"count": "nope"}'}}

    client = LocalModelClient(base_url="http://127.0.0.1:9999", post_json=post_json)
    with pytest.raises(ModelError):
        client.complete_json("x", SCHEMA)
    assert n == 2