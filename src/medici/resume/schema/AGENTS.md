# Resume facts schema and validator

Issues: E5-1. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

The user's own facts, and the validator that keeps generated resumes honest.

## Produce

- `facts.py`: typed schema for the user's facts (employers, schools, dates, tools, projects).
- `validate.py`: reject any generated resume that contains an employer, school, date or tool not in the facts.

## Rules for this area

- Facts come only from the user. Nothing from the posting becomes a fact.
- The validator is strict and tested with planted fabrications.

## Neighbours

- Uses: model
- Used by: resume/prompt, resume/render

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
