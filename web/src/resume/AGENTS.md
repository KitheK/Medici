# Resume approval screen

Issues: E5-5. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Show changed bullets side by side; the user accepts or rejects each.

## Produce

- `ApprovalScreen` component and tests.

## Rules for this area

- Nothing is exported until every changed bullet is decided.

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
