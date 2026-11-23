# API endpoints

Issues: E7-1. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

The contract between the Python core and the web review screen.

## Produce

- `app.py`: FastAPI app.
- `schemas.py`: review payload models (contacts with source and confidence, email guess with label, resume diff).
- Contract tests that pin the payload shape.

## Rules for this area

- No endpoint sends anything anywhere.
- Every contact in the payload has a source URL and confidence.
- Payload changes need a contract-test update and a note for the web agents.

## Neighbours

- Uses: scoring, email, resume, network, optout
- Used by: web

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
