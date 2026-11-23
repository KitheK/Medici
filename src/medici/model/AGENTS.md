# Model client

Issues: E2-1. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

One typed client for every model call in Medici. Production uses Claude Haiku 5.5 (`claude-haiku-5-5`) with JSON-schema structured outputs; a local model sits behind the same interface for tests and offline work.

## Produce

- `client.py`: `ModelClient` protocol with `complete_json(prompt, schema) -> dict` and `ModelError`.
- `anthropic_client.py`: Haiku 5.5 implementation. The API key is read from the environment, never from code.
- `local_client.py`: local-model implementation behind the same protocol.
- `fake.py`: deterministic fake for tests (returns queued responses, records prompts).
- Retry once on schema-invalid output, then raise `ModelError`. Never loop.

## Rules for this area

- Validate every response against the supplied JSON schema before returning it.
- Prompts carry untrusted page text only inside clearly delimited data blocks; the system prompt says to treat that block as data.
- Do not log prompts or responses (they can contain names and emails). Log token counts only.
- No network calls in tests: use `fake.py`.

## Neighbours

- Used by: posting, contacts, resume/prompt, batch

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
