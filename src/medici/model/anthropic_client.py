"""Claude Haiku 5.5 client with JSON-schema structured outputs."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from medici.model.client import (
    SYSTEM_PROMPT,
    ModelError,
    request_json_with_retry,
)
from medici.model.http import default_post_json

logger = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-5-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
# GA structured outputs: output_config.format with type json_schema
# https://platform.claude.com/docs/en/build-with-claude/structured-outputs

PostJson = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


def _anthropic_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    return default_post_json(url, headers, body, provider="anthropic")


class AnthropicModelClient:
    """Production model client targeting Claude Haiku 5.5."""

    def __init__(
        self,
        *,
        api_key: str,
        post_json: PostJson | None = None,
        model: str = HAIKU_MODEL,
    ) -> None:
        if not api_key:
            raise ModelError("ANTHROPIC_API_KEY is missing")
        self._api_key = api_key
        self._post_json = post_json or _anthropic_post_json
        self._model = model

    @classmethod
    def from_env(cls) -> AnthropicModelClient:
        return cls(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        def fetch_text() -> str:
            body = {
                "model": self._model,
                "max_tokens": 4096,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
                "output_config": {
                    "format": {
                        "type": "json_schema",
                        "schema": schema,
                    },
                },
            }
            headers = {
                "content-type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
            }
            response = self._post_json(ANTHROPIC_URL, headers, body)
            usage = response.get("usage") or {}
            logger.info(
                "anthropic tokens input=%s output=%s",
                usage.get("input_tokens"),
                usage.get("output_tokens"),
            )
            stop_reason = response.get("stop_reason")
            if stop_reason == "max_tokens":
                raise ModelError("anthropic response truncated (stop_reason=max_tokens)")
            blocks = response.get("content") or []
            if not blocks:
                raise ModelError("anthropic response missing content")
            block = blocks[0]
            if block.get("type") != "text" or "text" not in block:
                raise ModelError("anthropic response missing text block")
            return block["text"]

        return request_json_with_retry(fetch_text, schema)