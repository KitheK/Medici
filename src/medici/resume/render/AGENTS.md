# LaTeX renderer

Issues: E5-3. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Fill Jake's resume template from validated JSON.

## Produce

- `render.py`: JSON to `.tex` using the macros in `templates/jakes.tex`.
- `escape.py`: escape & % $ # _ { } ~ ^ \ in every field.
- `templates/jakes.tex`: the template.

## Rules for this area

- Escape every user-supplied string. Tested with hostile input.
- No raw `\input`, `\write18` or other commands can come from data.

## Neighbours

- Uses: resume/schema
- Used by: resume/compile

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
