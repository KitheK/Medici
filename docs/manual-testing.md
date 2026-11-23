# Manual testing

Automated layers (run in CI, see `docs/github-setup.md`): unit, integration, end-to-end, privacy.
Manual testing covers what must not run in CI: the live web, real model calls, and human judgement.
Open a "Manual test pass" issue (template) before a release and after any change to fetching,
storage, opt-out, the resume pipeline or the review screen.

## 1. Live robots.txt spot check (people only)
Pick 3 real company sites you have no relationship with. In the CLI, request only their allowlisted
pages. Confirm a disallowed path is skipped and no more than 1 request per second reaches each host.
Never run this from CI or an agent. Record no names or emails in the notes.

## 2. Real model call (opt-in, budget-capped)
Run the model client against Haiku 5.5 (`claude-haiku-5-5`) on 3 fixture postings. Confirm
schema-valid JSON, and that the injected fixture page changes nothing. Stop if spend passes the cap
set in your environment.

## 3. Resume PDF
Generate from your own facts. One page, Jake's layout, no fabricated employer, school, date or tool.
Open the PDF and read every bullet against your facts.

## 4. Privacy checklist
- No send, connect or message control anywhere in the UI.
- Opt-out removes the person from output and saved lists.
- Unsaved results expire at 30 days; saved entries go stale at 180 days (use the fake-clock tool).
- Logs from the run contain counts and IDs, not names or emails.
- Privacy notice and opt-out links work from the review screen.

## 5. Sign-off
Tick the checklist in the issue and link the commit or tag. E8-3 is not done without a pass.
