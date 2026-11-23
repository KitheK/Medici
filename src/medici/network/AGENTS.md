# Saved contacts

Issues: E6-1, E6-2, E6-3. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Private, per-user saved recruiter network.

## Produce

- `save.py`: save, delete and export a user's saved contacts (only on an explicit click).
- `verify.py`: re-fetch the source, mark entries stale if the page is gone, delete 180 days after last verification.
- `isolation` tests: user B never sees user A's contacts; a suppression hit clears both lists.

## Rules for this area

- Nothing saves without an explicit user action.
- Every query is scoped by user id.
- Suppression cascades into saved lists.

## Neighbours

- Uses: scoring, optout, fetch, store
- Used by: api

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
