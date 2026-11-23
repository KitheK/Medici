# Batch runner and report

Issues: E9-1, E9-3. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Process many postings with per-host limits and a budget cap.

## Produce

- `runner.py`: run N postings, 1 request per second per host, stop at the budget cap.
- `report/`: per-batch tokens, cost and failures.

## Rules for this area

- Budget cap is enforced in code.
- Same privacy rules as single runs; logs stay clean.

## Neighbours

- Uses: crawl, model
- Used by: agent

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
