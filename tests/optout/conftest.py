"""Shared fixtures for opt-out tests."""

from __future__ import annotations

import pytest

from medici.store.db import connect, init_schema

TEST_SUPPRESSION_KEY = "test-only-suppression-key-32-bytes-min!!"


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