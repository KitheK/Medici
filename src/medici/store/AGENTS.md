# Storage, expiry and suppression

Issues: E2-5, E8-1. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Persist contacts with retention built in. SQLite first, Postgres at E8-1.

## Produce

- `db.py`: connection and schema creation.
- `contacts.py`: save and read contacts, each with `expires_at` (30 days when unsaved).
- `expiry.py`: job that deletes expired rows.
- `suppression.py`: opt-out table storing an HMAC of the identifier, plus `is_suppressed()`.
- E8-1: Postgres migration in `migrations/`, secrets from a vault, encryption on.

## Rules for this area

- Suppression stores only an HMAC (key from the environment, at least 32 bytes; no default).
  Never the raw name or email. Canonicalise emails and URLs before hashing; the store only
  strips and lower-cases the string it receives.
- Expiry is code, tested with a fake clock.
- No contact row without an `expires_at`.
- Every `save_contact` call must pass an `identifier` so the suppression table is always checked.

## Neighbours

- Used by: scoring, optout, network, api

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
