# Sandboxed compile

Issues: E5-4. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Turn `.tex` into a one-page PDF safely.

## Produce

- `compile.py`: run Tectonic or latexmk with no network, shell escape off and a time limit.
- `sandbox.py`: process isolation helpers.

## Rules for this area

- No network, no shell escape, hard timeout.
- 20 test inputs each produce a one-page PDF; overflow raises, it does not silently shrink.

## Neighbours

- Uses: resume/render
- Used by: api

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
