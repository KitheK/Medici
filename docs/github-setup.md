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
- Ruleset for `main`: require a pull request; require status checks `ci` and `review-gate`
  (they appear in the picker after their first run); require review from Code Owners once a second
  reviewer exists. With one person, leave approvals off: agent PRs are opened with your token and you
  cannot approve your own PR. The two checks plus your merge click are the gate.
- Labels and issues: `python3 -m tools.sync_github` (also runs on merge to `main`).

## Queue behaviour

`python -m tools.queue pick --owner claude-code|cursor` returns the first issue that is `todo`, owned by
that lane, with every dependency done **and passing**, and not already in an open PR. Each lane holds at
most one issue at a time. Human issues (E0, E1, E8-3) never enter an agent lane; until E0-1, E1-1 and
E1-2 are done the agent queue is empty by design. Run on demand with the `claude-now` or `cursor-now`
label on an issue, or `workflow_dispatch`.

## Smoke test (first time)

1. Set the secrets. Do not set `ENABLE_AGENTS` yet.
2. Open a PR from a `ci/` or `docs/` branch: `ci` runs, `review-gate` passes with a notice.
3. Set `ENABLE_AGENTS=true`. Open a small human PR: both reviewers run and post reviews.
4. After E0-1, E1-1 and E1-2 are closed, run `build-claude` and `build-cursor` with `workflow_dispatch`.
5. Check these against current docs on the first run, because I could not run them from here:
   `agent -p --force` and `.cursor/cli.json` permission syntax (Cursor CLI docs), and the
   `claude-code-action@v1` inputs.

## Safety notes

- Reviewers get the PR as plain files and may only write `review.md` and `verdict.txt`. PR text is
  treated as data. Only same-repo branches get reviewed (forks never see secrets).
- Cursor builds with edit-only permissions (`.cursor/cli.json`); git, pushing and PR creation are
  workflow steps. Neither builder may edit `.github/` or `tools/`; `GH_PAT` has no Workflows permission.
- Every agent run costs plan usage and Actions minutes. Start with the nightly runs off.
