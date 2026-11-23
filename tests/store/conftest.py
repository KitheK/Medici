"""Shared fixtures for store tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from medici.store.db import connect, init_schema

TEST_SUPPRESSION_KEY = "test-only-suppression-key"


@pytest.fixture
def suppression_key(monkeypatch: pytest.MonkeyPatch) -> bytes:
    monkeypatch.setenv("MEDICI_SUPPRESSION_KEY", TEST_SUPPRESSION_KEY)
    return TEST_SUPPRESSION_KEY.encode()


@pytest.fixture
def db_conn(suppression_key):  # noqa: ARG001 — fixture wires env for store code
    conn = connect(":memory:")
    init_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def frozen_now() -> datetime:
    return datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)