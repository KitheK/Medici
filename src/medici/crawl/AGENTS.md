# Multi-page crawl

Issues: E3-1. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Follow allowlisted paths (team, about, careers, blog) from a company site.

## Produce

- `crawler.py`: `crawl(domain, budget=10) -> list[Page]` that stops after 10 pages per job.
- `paths.py`: allowlisted path patterns.

## Rules for this area

- Go through the fetch wrapper only.
- Hard cap of 10 pages per job, tested.
- Same-domain only.

## Neighbours

- Uses: fetch, contacts
- Used by: scoring, email

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
