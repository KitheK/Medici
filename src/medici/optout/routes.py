"""Opt-out endpoint handler; wire into FastAPI in E7-1."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from medici.optout.service import canonicalize_identifier, opt_out


@dataclass(frozen=True, slots=True)
class OptOutRequest:
    identifier: str


@dataclass(frozen=True, slots=True)
class OptOutResponse:
    status_code: int
    body: bytes


def parse_opt_out_body(raw: bytes) -> OptOutRequest:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        msg = "body must be JSON"
        raise ValueError(msg) from exc
    if not isinstance(data, dict):
        msg = "body must be a JSON object"
        raise ValueError(msg)
    identifier = data.get("identifier")
    if not isinstance(identifier, str) or not identifier.strip():
        msg = "identifier is required"
        raise ValueError(msg)
    return OptOutRequest(identifier=canonicalize_identifier(identifier))


def handle_opt_out(
    conn: sqlite3.Connection,
    request: OptOutRequest,
    *,
    key: bytes | None = None,
) -> OptOutResponse:
    """Accept an opt-out; response must not echo the identifier (no logging here)."""
    opt_out(conn, request.identifier, key=key)
    return OptOutResponse(status_code=204, body=b"")