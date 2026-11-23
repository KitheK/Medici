# Medici build plan (summary)

Full plan: "Medici: build plan" on claude.ai (the source of truth for the issue backlog).

**Product.** One job posting in, one sourced outreach plan out: a suspected recruiter, two team
members, a labelled unverified email-format guess, and a one-page Jake's-format resume built from
the user's own facts. Nothing is sent automatically. Saved contacts are private per user.

**Two lanes, one review screen.**
- People lane: posting parser, fetch wrapper (robots + allowlist + rate limit), contact extractor
  with excerpt validator, score and cap (1 recruiter + 2 team), email step.
- Resume lane: fact store, Haiku 5.5 JSON, LaTeX renderer, sandboxed compile, approval screen.

**Epics.** H0 setup, E0 decisions, E1 feasibility spike (gate: hit rate of about half on 30
postings), E2 walking skeleton, E3 people lane, E4 email step, E5 resume engine, E6 saved network,
E7 review screen, E8 launch checks, E9 batch runner.

**Backlog.** `issue_map.json` holds all 37 issues with dependencies, owners, `files_allowed` and
acceptance checks. Run `make next` to see what is ready.
