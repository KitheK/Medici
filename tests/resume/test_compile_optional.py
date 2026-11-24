"""Optional local pdflatex smoke test (skipped when TeX is not installed)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from medici.resume.render.render import render_resume
from tests.resume.test_render import _SAMPLE, _TEMPLATE


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not installed")
def test_rendered_resume_tex_builds_pdf():
    tex = render_resume(_SAMPLE, template_path=_TEMPLATE)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        tex_path = work / "resume.tex"
        tex_path.write_text(tex, encoding="utf-8")
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout[-500:] + result.stderr[-500:]
        assert (work / "resume.pdf").is_file()