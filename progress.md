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

## 2026-11-22: CI, queue and cross-review (H1-1 to H1-5)

- Split CI into unit, integration, e2e, privacy and scope jobs behind one required `ci` check.
- Added `tools/queue.py`: one lane per builder, so Claude Code and Cursor build at the same time.
- Added `build-claude.yml`, `build-cursor.yml` and `agent-review.yml` (cross-review, `review-gate`).
- Unverified until the first real run: Cursor CLI flags and `.cursor/cli.json` syntax, and
  `claude-code-action@v1` inputs. See the smoke test in `docs/github-setup.md`.

## 2026-11-23: Land CI and Cursor lanes on setup/phase-0

- Cherry-picked PR #45 agent/CI stack onto `setup/phase-0` (was only on `setup/github-workflow-2`).
- Fixed builder workflows to target the repo default branch (`setup/phase-0`), not `main`.
- CI and issue-sync push triggers include `setup/phase-0`; Cursor `agent` uses `--trust` in Actions.
- `pr-hygiene` allows `Agent/` branches (Cursor Cloud Agent integration PRs).

## 2026-11-23: E5-1 Resume schema and validator

- Added `src/medici/resume/schema/` (`facts.py`, `validate.py`): typed user facts,
  `ResumeDocument` JSON schema, and strict validator for employers, schools, dates, tools,
  and project names.
- Added `tests/resume/` with fabrication tests and a privacy-marked posting-injection test.
- Owner skipped the E0-1 gate; E2-1 was not needed for this issue (no model client).
- Next: E5-2 resume prompt/model call once E2-1 lands; E5-3 LaTeX render.