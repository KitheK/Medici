# Agent wrapper

Issues: E9-2. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Optional agent wrapper exposing pipeline stages as tools.

## Produce

- `tools.py`: stage tools (parse, fetch, extract, score).
- `pause.py`: human approval pause before any save.

## Rules for this area

- No send tool exists. No save without approval.
- The wrapper adds orchestration only; business rules stay in the stage modules.

## Neighbours

- Uses: batch

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
