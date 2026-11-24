# 2026-11-23: E5-1 Resume schema and validator

- Added `src/medici/resume/schema/` (`facts.py`, `validate.py`): typed user facts,
  `ResumeDocument` JSON schema, and strict validator for employers, schools, dates, tools,
  and project names.
- Added `tests/resume/` with fabrication tests and a privacy-marked posting-injection test.
- Owner skipped the E0-1 gate; E2-1 was not needed for this issue (no model client).
- Next: E5-2 resume prompt/model call once E2-1 lands; E5-3 LaTeX render.
