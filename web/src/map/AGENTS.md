# Mind map and message helper

Issues: E7-3. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Graph of you, company, recruiter and team (React Flow) plus copy buttons and a message helper.

## Produce

- `MindMap`, `CopyButton`, `MessageHelper` and tests.

## Rules for this area

- The message helper drafts text to copy. It never sends.

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
