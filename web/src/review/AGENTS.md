# Review screen and source panel

Issues: E7-2. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

One screen showing recruiter, team members, email guess and resume status.

## Produce

- `ReviewScreen`, `ContactCard`, `SourcePanel` and tests.

## Rules for this area

- Each contact shows source and confidence.
- No send button exists.

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
