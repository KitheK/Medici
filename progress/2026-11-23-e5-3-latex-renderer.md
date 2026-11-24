# 2026-11-23: E5-3 LaTeX renderer

- Added `src/medici/resume/render/` (`escape.py`, `render.py`), `templates/jakes.tex` (Jake's shell
  with `@@MEDICI_*@@` macros), and tests for escaping and macro fill.
- Branched from `issue/E5-1`; PDF compile remains E5-4. No contact/heading block in output yet
  (`ResumeDocument` has no header fields).
- Review follow-up: single-pass macro fill, Jake employer/title order, optional `pdflatex` test.
- Next: E5-4 sandboxed compile; E5-2 prompt when E2-1 lands.
