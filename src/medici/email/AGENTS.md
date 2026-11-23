# Email format guess

Issues: E4-1, E4-2. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Suggest a likely address pattern, honestly labelled, or say "no guess".

## Produce

- `evidence.py`: collect addresses the company published on its own pages.
- `infer.py`: infer a format only from at least 2 agreeing examples, otherwise `NoGuess`.
- `mx.py`: DNS MX lookup for the domain (no SMTP).
- `label.py`: attach the label `unverified` to every guess.

## Rules for this area

- No SMTP probing, no verification services, no purchased lists.
- Every guess is labelled "unverified".
- Fewer than two agreeing published examples returns "no guess".

## Neighbours

- Uses: crawl, fetch
- Used by: api

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
