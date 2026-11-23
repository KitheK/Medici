# Resume prompt and model call

Issues: E5-2. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

System prompt and call that tailor wording of the user's facts to one posting.

## Produce

- `prompt.py`: system prompt text and builder.
- `generate.py`: calls the model client, validates with `resume/schema`, returns schema-valid JSON.

## Rules for this area

- The model may reword and reorder; it may not add facts.
- An injected posting must leave the output unchanged (tested).
- 10 sample fact sets pass.

## Neighbours

- Uses: model, resume/schema
- Used by: api, web resume screen

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
