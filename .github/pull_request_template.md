## Issue

Closes #

Issue ID (as in `issue_map.json`):

## What changed

## Agent cross-review

When `ENABLE_AGENTS=true` (see `docs/github-setup.md`), opening a ready (non-draft) PR adds
`review:claude` or `review:cursor`, and that agent (the one that did not make the PR) reviews it.
To run again:

- Add label `review:request` or `review:rerequest` (re-review reads the full diff and prior comments)
- Comment `/review` or `/rereview` on the PR (needs write access)
- Actions → **agent-review** → **Run workflow** with the PR number

## Checklist

- [ ] Branch is named `issue/<ID>` and only touches the issue's `files_allowed`
- [ ] `make ci` passes
- [ ] `python3 tools/issue_map.py complete <ID>` run (it, not me, sets `passes`)
- [ ] A new file in `progress/` says what changed (see `progress/README.md`)
- [ ] No names, emails or secrets in logs, fixtures or tests
- [ ] No send, connect or message capability added
