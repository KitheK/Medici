# Architecture map

Where each part of the system lives, which issues build it, and the guide an agent should read first.
Every folder below has an `AGENTS.md` saying what to produce there.

```
posting text ──► src/medici/posting ─┐
                                     ├─► src/medici/crawl ─► contacts ─► scoring ─► api ─► web/
company domain ─► src/medici/fetch ──┘        (E3-1)         (E2-4)      (E3-2)    (E7-1)
                                                   └─► email (E4-1, E4-2) ─────────────┘
user facts ─► resume/schema ─► resume/prompt ─► resume/render ─► resume/compile ─► web/src/resume
                (E5-1)           (E5-2)           (E5-3)           (E5-4)            (E5-5)
store (E2-5) · optout (E3-4) · network (E6-x) · logging (E3-3) · batch (E9-x) · agent (E9-2)
```

| Area | Folder | Issues | Owner |
|---|---|---|---|
| Model client | `src/medici/model` | E2-1 | Claude Code |
| Posting parser | `src/medici/posting` | E2-2 | Claude Code |
| Fetch wrapper | `src/medici/fetch` | E2-3 | Claude Code |
| Contact extractor | `src/medici/contacts` | E2-4 | Claude Code |
| Storage, expiry, suppression | `src/medici/store`, `migrations` | E2-5, E8-1 | Claude Code |
| CLI review card | `src/medici/cli` | E2-6 | Claude Code |
| Crawl | `src/medici/crawl` | E3-1 | Claude Code |
| Scoring and cap | `src/medici/scoring` | E3-2 | Claude Code |
| Log hygiene, injection tests | `src/medici/logging`, `tests/privacy` | E3-3 | Claude Code |
| Opt-out | `src/medici/optout` | E3-4 | Claude Code |
| Email step | `src/medici/email` | E4-1, E4-2 | Claude Code |
| Resume engine | `src/medici/resume/*`, `templates` | E5-1 to E5-4 | Claude Code |
| Saved network | `src/medici/network` | E6-1 to E6-3 | Claude Code |
| API | `src/medici/api` | E7-1 | Claude Code |
| Web | `web/src/*` | E5-5, E7-2, E7-3, E8-2 | Cursor |
| Batch and agent | `src/medici/batch`, `src/medici/agent` | E9-1 to E9-3 | Claude Code |
| Decisions, data map, legal | `docs/` | E0-1, E0-2, E1-1, E1-2, E8-3 | You |
