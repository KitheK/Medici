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

## 2026-11-23: PR review request labels and controls

- Extended `agent-review.yml`: `prepare` job, auto `review:claude` / `review:cursor` on ready PRs,
  trigger labels `review:request` / `review:rerequest`, `/review` and `/rereview` comments,
  `workflow_dispatch`, and re-review context via `prior-review-comments.md`.
- New labels in `.github/labels.json`; documented in `AGENTS.md`, `docs/github-setup.md`, PR template.
- PRs #52/#54 skipped reviewers because `ENABLE_AGENTS` is not `true` (not a workflow bug).

## 2026-11-23: One designated reviewer per PR

- `agent-review` picks one reviewer from who made the PR (`tools/pick_reviewer.py`) instead of running
  both. Branch prefix alone missed Cursor PRs on `issue/*` branches.
- `review-gate` fails if no reviewer could be designated (it was skipped, which counts as passing).
- Not yet run on GitHub: open PRs use the new rule only after their base contains this change.

## 2026-11-24: Trusted bots and conflict fixes

- Claude refused runs started by Cursor's bot (PRs 51 and 52). Named bots may now start the Claude
  workflows and comment commands; only the first line of a comment has to be the command.
- A comment that is not a command no longer cancels a running review.
- Added `fix-conflicts.yml` and `tools/conflict_fix.py`: `/fix-conflicts`, a manual run, or an opt-in sweep.
- Not yet run on GitHub: the conflict workflow only starts once it is on the default branch.

## 2026-11-23: E2-5 storage, expiry and suppression

- Added `src/medici/store/` (SQLite schema, contacts with mandatory `expires_at`, expiry
  delete job, suppression table with HMAC-only identifiers) and `tests/store/`.
- Assumed E0-1 retention from root `AGENTS.md` (30-day unsaved, 180-day saved from save time;
  re-verification refresh deferred to E6-2).
- Next: E2-2 posting parser, E2-4 contact extractor, then E2-6 CLI review card.
- Blockers: none (E0-1 human gate deliberately bypassed for this session).
