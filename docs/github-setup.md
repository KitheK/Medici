# GitHub setup: CI, builders, reviewers and the queue

## The loop

```
issue_map.json ── queue (tools/queue.py) ─┬─ claude-code lane ─► build-claude.yml ─► PR claude/issue-ID ──┐
 (deps, owner, WIP limit per lane)        └─ cursor lane      ─► build-cursor.yml ─► PR cursor/issue-ID ──┤
                                                                                                           ▼
 CI (ci.yml): lint+unit · integration · e2e · scope  ──► required check `ci`
 agent-review.yml: Claude reviews cursor/* and human PRs · Cursor reviews claude/* and human PRs
                    ──► required check `review-gate`            then you merge
```

The two builder workflows have separate concurrency groups and the queue gives each builder only its
own issues, so Claude Code and Cursor build at the same time on different issues. Nobody reviews their
own PR. Both reviewers run on human-written PRs.

## Test layers

| Layer | Command | What it covers | Runs |
|---|---|---|---|
| Unit | `make test-unit` | pure logic, fake model | every PR |
| Integration | `make test-integration` | fixture site, sqlite, CLI subprocess, API contracts | every PR |
| End-to-end | `make test-e2e` | whole workflows from the outside (Playwright joins when `web/` exists) | every PR |
| Privacy | `make privacy` | rules that may never be weakened | every PR |
| Scope | `tools/check_files_allowed.py` | a branch touches only its issue's `files_allowed` | every PR |
| Manual | `docs/manual-testing.md` | live web, real model, visual and human checks | before release |

`make ci` runs all automated layers locally. `ci` (the aggregate job) is the one required check.

## Secrets and variables (Settings → Secrets and variables → Actions)

| Name | Kind | Used by |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | secret | Claude builder and reviewer (`claude setup-token`; uses your Claude plan) |
| `CURSOR_API_KEY` | secret | Cursor builder and reviewer (Cursor dashboard) |
| `GH_PAT` | secret | builders; fine-grained, this repo only, Contents + Pull requests + Issues read/write, **no** Workflows permission |
| `ENABLE_AGENTS` | variable | `true` switches builders and reviewers on |
| `ENABLE_NIGHTLY` | variable | `true` lets the scheduled runs pick issues |
| `CURSOR_MODEL` | variable, optional | model name passed to `agent --model` |

Also install the Claude GitHub App on the repo. Why `GH_PAT`: pushes and PRs made with the built-in
token do not trigger other workflows, so CI and the reviewers would never run on agent PRs.
Leave `ENABLE_AGENTS` unset until the smoke test below passes; with it unset, `review-gate` passes.

## Repository settings

- Actions → General → Workflow permissions: read and write.
- Ruleset for `setup/phase-0` (current default branch): require a pull request; require status checks
  `ci` and `review-gate` (they appear in the picker after their first run); require review from Code
  Owners once a second reviewer exists. With one person, leave approvals off: agent PRs are opened
  with your PAT and you cannot approve your own PR. The two checks plus your merge click are the gate.
- Labels and issues: `python3 -m tools.sync_github` (also runs on merge to `setup/phase-0`).

## Queue behaviour and labels

Three labels control the agents. Nothing is built until a person labels it.

| Label | Meaning | When agents work on it |
|---|---|---|
| `agent` | owned by an agent, not a person (set automatically from `issue_map.json`) | n/a |
| `agent-queue` | in the agent queue | right away: adding the label starts the owning builder on that issue, or run `build-claude` / `build-cursor` by hand |
| `agent-night` | queued for the night run | only the scheduled run (about 2:17 AM and 2:47 AM Pacific, set by `cron` in `build-claude.yml` and `build-cursor.yml`; also needs `ENABLE_NIGHTLY=true`) |

`python -m tools.queue pick --owner claude-code|cursor --only <labelled IDs>` returns the first labelled
issue that is `todo`, owned by that lane, with every dependency done **and passing**, and not already in
an open PR. Each lane holds at most one issue at a time, and the two lanes run in parallel. Human issues
(E0, E1, E8-3) never enter an agent lane; until E0-1, E1-1 and E1-2 are done, labelling a product issue
does nothing. Sync keeps hand-added `agent-queue`, `agent-night`, `needs-human` and `blocked` labels, and
removes the two queue labels once an issue passes. To change the night time, edit the two `cron` lines
(they are UTC).

## Mentor feedback (for learning)

`agent-feedback.yml` gives every PR one advisory review whose job is to teach good software
engineering and keep the code good. It is not a gate and never fails a PR.

- **When:** a PR is opened or marked ready, or you add the `agent-feedback` label to re-run it after
  more commits (the workflow removes the label when done). Dependabot PRs are skipped.
- **What you get:** a purpose check (does the code do what the issue and area guide say it is for?),
  named patterns and anti-patterns, inline comments with one-click **suggested changes** where a fix
  is clear, one or two alternative ways of thinking about a design choice with honest trade-offs,
  what is working well, and a short list of concepts to read up on.
- **Severity:** `fix` (likely defect or clear anti-pattern), `consider` (a better option),
  `learn` (teaching point, no change needed).
- **How it stays safe:** the reviewer is read-only and writes only `feedback.json`. A script
  (`tools/post_feedback.py`) posts it: comments are anchored only to lines in the diff, `@mentions`
  are neutralised, volume is capped at 15 inline comments, and a bad anchor falls back to the review
  body instead of losing the feedback. The rubric is `.github/feedback-prompt.md`; edit it to change
  what the mentor focuses on.
- It is separate from the requirements gate (`agent-review.yml`), which checks acceptance criteria
  and rules and does block.

## Smoke test (first time)

1. Set the secrets. Do not set `ENABLE_AGENTS` yet.
2. Open a PR from a `ci/` or `docs/` branch: `ci` runs, `review-gate` passes with a notice.
3. Set `ENABLE_AGENTS=true`. Open a small human PR: both reviewers run and post reviews.
4. After E0-1, E1-1 and E1-2 are closed, run `build-claude` and `build-cursor` with `workflow_dispatch`.
5. On the first real run, confirm `agent -p --force --trust`, `CURSOR_API_KEY`, and
   `claude-code-action@v1` inputs against current Cursor and Claude docs (see
   [Cursor CLI in GitHub Actions](https://cursor.com/docs/cli/github-actions)).

## Safety notes

- Reviewers get the PR as plain files and may only write `review.md` and `verdict.txt`. PR text is
  treated as data. Only same-repo branches get reviewed (forks never see secrets).
- Cursor builds with edit-only permissions (`.cursor/cli.json`); git, pushing and PR creation are
  workflow steps. Neither builder may edit `.github/` or `tools/`; `GH_PAT` has no Workflows permission.
- Every agent run costs plan usage and Actions minutes. Start with the nightly runs off.
