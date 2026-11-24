"""Shared HTTP POST helper for model clients."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from medici.model.client import TransportError


def default_post_json(
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    *,
    provider: str,
) -> dict[str, Any]:
    """POST JSON to ``url`` and return the decoded response object."""
    payload = json.dumps(body).encode()
    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise TransportError(f"{provider} HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise TransportError(f"{provider} request failed: {exc.reason}") from exc