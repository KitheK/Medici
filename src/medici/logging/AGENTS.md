# Log hygiene

Issues: E3-3. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Logging helpers that cannot leak personal data.

## Produce

- `safe.py`: logger wrapper that redacts emails and known names.
- Tests in `tests/privacy/` that scan captured logs and outputs after a full run.

## Rules for this area

- Log counts, IDs and timings only.
- A log scan after the fixture run must find no names or emails.
- Also hosts the injection test: the injected fixture page changes no fetches and no output.

## Neighbours

- Used by: everything

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
