# Scoring, cap and role labels

Issues: E3-2. Read the issue's `acceptance` list in `issue_map.json`; this file says what to produce and the rules to respect. Shared rules are in the root `AGENTS.md`.

## Purpose

Choose who to show: at most 1 suspected recruiter and 2 team members.

## Produce

- `score.py`: rank contacts by role match to the posting; assign labels `recruiter` or `team`.
- `cap.py`: enforce the 3-person cap.

## Rules for this area

- The cap is enforced in code, tested on a page with 10 contacts.
- Label wording says "suspected"; never claim certainty.
- Drop suppressed people before ranking.

## Neighbours

- Uses: contacts, store
- Used by: network, api

## Tests

Mirror this folder under `tests/`. Write the failing test first. Use `fixtures/` and the fake model client; never the live web or a real model in tests.
