"""Shared HTTP helper for model clients."""

from __future__ import annotations

import io
import urllib.error
from unittest import mock

import pytest

from medici.model.client import TransportError
from medici.model.http import default_post_json


def test_default_post_json_raises_transport_error_without_response_body():
    with mock.patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            "https://x",
            429,
            "Too Many",
            {},
            io.BytesIO(b"secret prompt echoed back"),
        ),
    ):
        with pytest.raises(TransportError) as exc_info:
            default_post_json("https://x", {}, {"prompt": "secret"}, provider="anthropic")
    assert "429" in str(exc_info.value)
    assert "secret" not in str(exc_info.value)