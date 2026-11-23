# Privacy notice and opt-out page

Issues: E8-2. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Privacy notice and opt-out page, linked from the review screen.

## Produce

- `PrivacyNotice`, `OptOutPage` and tests.

## Rules for this area

- Link both from the review screen footer.
- Wording comes from the reviewed draft (E0-2).

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
