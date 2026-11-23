# Fetch wrapper

Issues: E2-3. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

The only code path allowed to touch the network for page content. Everything else calls this.

## Produce

- `fetcher.py`: `Fetcher.get(url) -> Page | Skipped` returning Markdown text, final URL and fetch time.
- `robots.py`: robots.txt check using the standard-library parser, cached per host.
- `allowlist.py`: host allowlist; anything else raises `NotAllowed`.
- `ratelimit.py`: 1 request per second per host.
- `html.py`: HTML to Markdown conversion, dropping scripts, styles and hidden elements.

## Rules for this area

- Obey robots.txt. A disallowed path is skipped, not retried.
- Reject off-allowlist URLs before any request is made.
- At most 1 request per second per host, enforced in code and tested with a fake clock.
- Identify honestly with a descriptive User-Agent. No login pages, no LinkedIn, no CAPTCHA bypass.
- Tests use the local fixture site (`fixtures/serve.py`), never the live web.

## Neighbours

- Uses: fixtures (tests only)
- Used by: contacts, crawl, email, network

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
