"""Claude Haiku 5.5 client with JSON-schema structured outputs."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from medici.model.client import (
    SYSTEM_PROMPT,
    ModelError,
    request_json_with_retry,
)

logger = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-5-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

PostJson = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


def _default_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(body).encode()
    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise ModelError(f"anthropic HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ModelError(f"anthropic request failed: {exc.reason}") from exc


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
        self._post_json = post_json or _default_post_json
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
                "output_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "medici_output",
                        "strict": True,
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
            blocks = response.get("content") or []
            if not blocks or "text" not in blocks[0]:
                raise ModelError("anthropic response missing text block")
            return blocks[0]["text"]

        return request_json_with_retry(fetch_text, schema)