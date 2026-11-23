"""Local model gateway client (same interface as Anthropic)."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from medici.model.client import SYSTEM_PROMPT, ModelError, request_json_with_retry

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_URL = "http://127.0.0.1:8766/v1/complete"

PostJson = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


def _default_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(body).encode()
    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise ModelError(f"local model HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ModelError(f"local model request failed: {exc.reason}") from exc


class LocalModelClient:
    """Talks to a Medici local completion gateway for offline runs and tests."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        post_json: PostJson | None = None,
    ) -> None:
        self._url = (base_url or DEFAULT_LOCAL_URL).rstrip("/")
        self._post_json = post_json or _default_post_json

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