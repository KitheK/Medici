"""Deterministic fake model client for tests."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from medici.model.client import SchemaValidationError, validate_against_schema


class FakeModelClient:
    """Returns queued dict responses and records prompts (no network)."""

    def __init__(self, responses: Iterable[dict[str, Any]] | None = None) -> None:
        self._responses = list(responses or [])
        self.prompts: list[str] = []

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.prompts.append(prompt)
        if not self._responses:
            raise SchemaValidationError("fake model has no queued responses")
        data = self._responses.pop(0)
        validate_against_schema(data, schema)
        return data