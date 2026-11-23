"""Opt-out HTTP handler (mounted by API in E7-1)."""

from __future__ import annotations

import json
import logging

import pytest

from medici.optout.routes import handle_opt_out, parse_opt_out_body
from medici.optout.service import opt_out
from medici.store import suppression

IDENTIFIER = "route.pat@example.test"


def test_parse_opt_out_body_requires_identifier():
    with pytest.raises(ValueError, match="identifier"):
        parse_opt_out_body(b"{}")
    req = parse_opt_out_body(json.dumps({"identifier": IDENTIFIER}).encode())
    assert req.identifier == IDENTIFIER


def test_handle_opt_out_succeeds_without_echoing_identifier(db_conn, suppression_key):
    body = json.dumps({"identifier": IDENTIFIER}).encode()
    response = handle_opt_out(db_conn, parse_opt_out_body(body), key=suppression_key)
    assert response.status_code == 204
    assert IDENTIFIER not in response.body.decode()
    assert suppression.is_suppressed(db_conn, IDENTIFIER, key=suppression_key)


def test_handle_opt_out_is_idempotent(db_conn, suppression_key):
    request = parse_opt_out_body(json.dumps({"identifier": IDENTIFIER}).encode())
    handle_opt_out(db_conn, request, key=suppression_key)
    handle_opt_out(db_conn, request, key=suppression_key)
    count = db_conn.execute("SELECT COUNT(*) FROM suppressions").fetchone()[0]
    assert count == 1


def test_opt_out_flow_never_logs_identifier(caplog, db_conn, suppression_key):
    body = json.dumps({"identifier": IDENTIFIER}).encode()
    with caplog.at_level(logging.DEBUG, logger="medici"):
        handle_opt_out(db_conn, parse_opt_out_body(body), key=suppression_key)
        opt_out(db_conn, IDENTIFIER, key=suppression_key)
    assert IDENTIFIER not in caplog.text