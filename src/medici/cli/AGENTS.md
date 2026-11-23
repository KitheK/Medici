# Command-line review card

Issues: E2-6. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

First end-to-end slice: one command takes a fixture posting and prints a review card.

## Produce

- `__main__.py`: `python -m medici.cli review <posting-file>` prints recruiter, team members and source links.
- `card.py`: pure formatting function, easy to test.

## Rules for this area

- Every contact line shows its source URL.
- No send, connect or message command exists.

## Neighbours

- Uses: posting, contacts, store

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
