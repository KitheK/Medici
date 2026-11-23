# Tests

Mirror `src/medici/<area>/` as `tests/<area>/`. Write the failing test first.

- `tests/privacy/` holds tests marked `@pytest.mark.privacy`. They must always pass; never weaken one to get a build green.
- Use `fixtures/` (local site, invented names) and the fake model client. No live web, no real model, no real people.
- Run one area with `python3 -m pytest tests/<area> -q`; run everything CI runs with `make ci`.
