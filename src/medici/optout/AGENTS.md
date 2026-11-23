# Opt-out

Issues: E3-4. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Let a person ask not to appear, and make that stick.

## Produce

- `service.py`: `opt_out(identifier)` stores an HMAC in the suppression table.
- `routes.py`: opt-out endpoint handler (wired by the API in E7-1).

## Rules for this area

- A suppressed person never appears in any output, including saved lists (E6-3 tests the cascade).
- Never echo the identifier back in logs.

## Neighbours

- Uses: store
- Used by: network, api

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
