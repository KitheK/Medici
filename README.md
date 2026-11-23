# Medici

Turn one job posting into a sourced outreach plan: a suspected recruiter, two team members, a
labelled unverified email-format guess, and a one-page Jake's-format resume built only from your
own facts. Medici never sends anything for you.

Status: Phase 0 setup. See `docs/build-plan.md`, `progress.md` and `issue_map.json`.

## Quick start

```bash
make install   # editable install with dev tools
make ci        # lint, tests, privacy tests, issue-map validation
make next      # which issue is ready to build
```

## Building with agents

Claude Code and Cursor share `AGENTS.md`. One issue per session, in its own worktree:

```bash
claude --worktree E2-3      # Claude Code
bash init.sh                # health check at the start of every session
python3 tools/issue_map.py complete E2-3   # only this sets `passes`
```

## Ground rules

Public pages only, no LinkedIn scraping, no auto-sending, at most 3 people per job, 30-day expiry
for unsaved results, opt-outs stored as HMACs. Details in `AGENTS.md`.
