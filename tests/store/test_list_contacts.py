"""list_contacts hides expired rows by default."""

from __future__ import annotations

from datetime import timedelta

from medici.store import contacts


def test_list_contacts_omits_expired_when_now_omitted(db_conn, frozen_now):
    contacts.save_contact(
        db_conn,
        name="Frank Expired",
        role_text="team",
        source_url="https://careers.example.test/old",
        excerpt="Frank Expired appears on the page.",
        saved=False,
        now=frozen_now - timedelta(days=31),
    )
    fresh_id = contacts.save_contact(
        db_conn,
        name="Gina Fresh",
        role_text="team",
        source_url="https://careers.example.test/new",
        excerpt="Gina Fresh appears on the page.",
        saved=False,
        now=frozen_now,
    )
    visible = contacts.list_contacts(db_conn, now=frozen_now)
    ids = {c.id for c in visible}
    assert fresh_id in ids
    assert len(ids) == 1


def test_list_contacts_defaults_now_to_current_time(db_conn, frozen_now, monkeypatch):
    """When ``now`` is omitted, expired rows must not appear (uses current time)."""
    contacts.save_contact(
        db_conn,
        name="Hank Old",
        role_text="team",
        source_url="https://careers.example.test/stale",
        excerpt="Hank Old on the team page.",
        saved=False,
        now=frozen_now - timedelta(days=40),
    )
    live_id = contacts.save_contact(
        db_conn,
        name="Ivy Live",
        role_text="team",
        source_url="https://careers.example.test/live",
        excerpt="Ivy Live on the team page.",
        saved=False,
        now=frozen_now,
    )

    monkeypatch.setattr(contacts, "_current_time", lambda: frozen_now)
    visible = contacts.list_contacts(db_conn)
    assert [c.id for c in visible] == [live_id]