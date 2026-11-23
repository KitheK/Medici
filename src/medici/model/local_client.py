"""Local model gateway client (same interface as Anthropic)."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from medici.model.client import SYSTEM_PROMPT, ModelError, request_json_with_retry
from medici.model.http import default_post_json

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_URL = "http://127.0.0.1:8766/v1/complete"

PostJson = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


def _local_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    return default_post_json(url, headers, body, provider="local model")


class LocalModelClient:
    """Talks to a Medici local completion gateway for offline runs and tests."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        post_json: PostJson | None = None,
    ) -> None:
        self._url = (base_url or DEFAULT_LOCAL_URL).rstrip("/")
        self._post_json = post_json or _local_post_json

    @classmethod
    def from_env(cls) -> LocalModelClient:
        return cls(base_url=os.environ.get("MEDICI_LOCAL_MODEL_URL"))

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        def fetch_text() -> str:
            body = {
                "system": SYSTEM_PROMPT,
                "prompt": prompt,
                "schema": schema,
            }
            headers = {"content-type": "application/json"}
            response = self._post_json(self._url, headers, body)
            usage = response.get("usage") or {}
            logger.info(
                "local model tokens input=%s output=%s",
                usage.get("input_tokens"),
                usage.get("output_tokens"),
            )
            message = response.get("message") or {}
            content = message.get("content")
            if not isinstance(content, str):
                raise ModelError("local model response missing message.content")
            return content

        return request_json_with_retry(fetch_text, schema)