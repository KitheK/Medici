# GitHub setup: CI, builders, reviewers and the queue

## The loop

```
issue_map.json ── queue (tools/queue.py) ─┬─ claude-code lane ─► build-claude.yml ─► PR claude/issue-ID ──┐
 (deps, owner, WIP limit per lane)        └─ cursor lane      ─► build-cursor.yml ─► PR cursor/issue-ID ──┤
                                                                                                           ▼
 CI (ci.yml): lint+unit · integration · e2e · scope  ──► required check `ci`
 agent-review.yml: one reviewer per PR: Cursor for Claude's PRs · Claude for Cursor's and human PRs
                    ──► required check `review-gate`            then you merge
```

The two builder workflows have separate concurrency groups and the queue gives each builder only its
own issues, so Claude Code and Cursor build at the same time on different issues. Nobody reviews their
own PR. Each PR gets one reviewer (`tools/pick_reviewer.py`); Claude reviews human PRs.

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
| `ENABLE_CONFLICT_SWEEP` | variable, optional | `true` fixes every conflicting PR after each push to a base branch |
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

## Queue behaviour

`python -m tools.queue pick --owner claude-code|cursor` returns the first issue that is `todo`, owned by
that lane, with every dependency done **and passing**, and not already in an open PR. Each lane holds at
most one issue at a time. Human issues (E0, E1, E8-3) never enter an agent lane; until E0-1, E1-1 and
E1-2 are done the agent queue is empty by design. Run on demand with the `claude-now` or `cursor-now`
label on an issue, or `workflow_dispatch`.

## Requesting cross-review

Automatic: when a PR is opened, reopened or marked ready for review (and not a draft),
`agent-review` runs one reviewer if `ENABLE_AGENTS=true`, and labels the PR `review:claude` or
`review:cursor` to show which. The PR's author is decided by the first of these that gives one answer:

1. Builder branch prefix: `claude/` or `cursor/`.
2. The marker the agent's tool leaves in the PR body (Cursor's hidden comment, Claude Code's footer).
3. The agent that wrote or co-wrote the most commits.

The other agent reviews. A human PR or an even mix goes to Claude (`DEFAULT_REVIEWER`).

Manual re-run (same requirements as automatic):

| Control | What it does |
|---|---|
| Label `review:request` | Queue a fresh cross-review (label is removed when the run starts) |
| Label `review:rerequest` | Re-review the **full current diff**; rubric emphasises prior review comments |
| PR comment `/review` or `/rereview` as the first line | Same as the labels; author must have **write**, be the repo owner, or be a trusted bot |
| `workflow_dispatch` on **agent-review** | `pr_number` required; set `rereview` for a re-review pass |

Outcome labels: `review:pass` or `review:changes` (set by `review-gate`).

One of `claude-review` and `cursor-review` is always skipped. If **both** are skipped while
`review-gate` is green on a ready PR, the repo variable `ENABLE_AGENTS` is not `true`. Set it only after `CLAUDE_CODE_OAUTH_TOKEN`, `CURSOR_API_KEY`
and (for builders) `GH_PAT` are configured (table above).

## Which bots may start agents

`TRUSTED_BOTS` at the top of `agent-review.yml`, `build-claude.yml` and `fix-conflicts.yml` names them
one by one. Do not use `*`: the repo is public, and `claude-code-action` does not check that an allowed
bot has write access, so `*` would let anyone's GitHub App start Claude on your plan.

## Fixing merge conflicts

Comment `/fix-conflicts` on the PR (write access or a trusted bot), or run **fix-conflicts** from Actions
with the PR number. Set `ENABLE_CONFLICT_SWEEP=true` to also run it after each push to a base branch.

- New `progress.md` entries from both sides are kept without an agent. Anything else is resolved by the
  agent that made the PR, so the other one still reviews it.
- The agent has a read-only token, no shell, and may edit only the conflicted files. `make ci` must pass
  before anything is pushed, and the push is never forced.
- Conflicts in protected files (`.github/`, `tools/`, `tests/privacy/`, any `AGENTS.md`, build config),
  deleted or binary files, or more than 20 files go to a human with the label `needs-human`. The sweep
  skips that label, so remove it to try again.
- Every run comments on the PR: what was fixed and how, or why nothing was pushed.
- Without `GH_PAT`, checks and review do not start by themselves on the pushed commit.

## Smoke test (first time)

1. Set the secrets. Do not set `ENABLE_AGENTS` yet.
2. Open a PR from a `ci/` or `docs/` branch: `ci` runs, `review-gate` passes with a notice.
3. Set `ENABLE_AGENTS=true`. Open a small human PR: Claude runs and posts a review.
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
