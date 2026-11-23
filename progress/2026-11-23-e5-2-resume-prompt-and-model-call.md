# 2026-11-23: E5-2 Resume prompt and model call

- Added `src/medici/resume/prompt/` (`prompt.py`, `generate.py`): system prompt, untrusted
  posting block, `RESUME_JSON_SCHEMA`, `generate_resume` with fact-validator retry, and
  `facts_to_resume_document` for deterministic baselines.
- Added tests: ten sample fact sets, hostile posting unchanged-output check, fabrication reject.
- Fake model only in tests; E5-1 and E2-1 now on `setup/phase-0`.
- Next: E5-3 LaTeX renderer.