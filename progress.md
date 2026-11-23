# Progress log

Newest entry last. Each session appends one entry: date, issue, what changed, what is next, blockers.

## 2026-11-22: Phase 0 setup (H0-1 to H0-4)

- Added the Python skeleton, `make ci`, GitHub Actions workflow and a placeholder privacy test (H0-1).
- Added `AGENTS.md`, `CLAUDE.md`, Cursor rules, `init.sh` and this log (H0-2).
- Added `issue_map.json` (37 issues) with picker, validator, completion script and the
  `files_allowed` diff check (H0-3).
- Added synthetic fixture sites with invented names (H0-4).
- Next: human issues E0-1 (data map) and E1-1 (30 hand-labelled postings) gate the first agent
  work. E1-2 is the go-or-narrow decision on hit rate.
- Acceptance lines that start with `$ ` are the commands `complete` runs; the rest are prose for
  reviewers. (A first version matched command words and mistook prose for a command.)
- H0-1 to H0-4 closed with `complete`; they await review in the setup PR.

## 2026-11-23: Cursor issue claims (bookkeeping)

- Claimed for Cursor (week of 2026-11-22), `in_progress`: E2-2, E2-4, E3-4, E5-2, E5-3.
- Claimed for Cursor (week of 2026-11-22), `todo`: E2-6, E3-1, E3-2, E3-3, E4-1, E4-2, E5-4.
