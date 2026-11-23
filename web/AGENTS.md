# Web app

Issues: E5-5, E7-2, E7-3, E8-2. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Next.js review screen. Owned by Cursor. Reads only from the API payload defined in `src/medici/api/schemas.py`.

## Produce

- `package.json` and config (first web issue creates it).
- Feature folders under `src/`: `resume`, `review`, `map`, `legal`.

## Rules for this area

- No send, connect or message button anywhere. Copy buttons only.
- Every contact shows its source link and confidence.
- Email guesses are labelled "unverified" wherever shown.
- The browser never fetches third-party pages.

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
