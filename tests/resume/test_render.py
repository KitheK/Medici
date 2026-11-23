"""LaTeX renderer: Jake's template macros and resume JSON → .tex."""

from __future__ import annotations

from pathlib import Path

from medici.resume.render.escape import escape_latex
from medici.resume.render.render import (
    TEMPLATE_MACROS,
    load_template,
    render_resume,
)
from medici.resume.schema.facts import (
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeDocument,
)

_REPO = Path(__file__).resolve().parents[2]
_TEMPLATE = _REPO / "templates" / "jakes.tex"

_SAMPLE = ResumeDocument(
    education=(
        EducationEntry(
            school="North Example Institute",
            degree="B.S. Computer Science",
            location="Sampleville, EX",
            dates="Sep 2015 -- May 2019",
        ),
    ),
    experience=(
        ExperienceEntry(
            employer="Loominary Labs",
            title="Platform Engineer",
            location="Ficton, EX",
            dates="Jun 2019 -- Present",
            bullets=("Shipped batch jobs on example.test.",),
        ),
    ),
    projects=(
        ProjectEntry(
            name="fixture-cache",
            dates="Jan 2018 -- Apr 2018",
            tools=("Python",),
            bullets=("Cached fixture payloads for tests.",),
        ),
    ),
    skills=("Python", "PostgreSQL", "Docker"),
)


def test_template_exists_with_named_macros():
    text = load_template(_TEMPLATE)
    for macro in TEMPLATE_MACROS:
        assert macro in text


def test_render_fills_all_macros():
    tex = render_resume(_SAMPLE, template_path=_TEMPLATE)
    for macro in TEMPLATE_MACROS:
        assert macro not in tex
    assert r"\section{Education}" in tex
    assert r"\section{Experience}" in tex
    assert escape_latex("North Example Institute") in tex
    assert escape_latex("Loominary Labs") in tex
    assert escape_latex("fixture-cache") in tex
    assert escape_latex("Python") in tex


def test_render_escapes_hostile_bullets():
    hostile = ResumeDocument(
        education=(),
        experience=(
            ExperienceEntry(
                employer="Loominary Labs",
                title=r"Lead & Co.$100%",
                location="Ficton~^",
                dates="2020 -- Present",
                bullets=(r"\input{evil} #1 _x",),
            ),
        ),
        skills=(r"C\++",),
    )
    tex = render_resume(hostile, template_path=_TEMPLATE)
    assert r"\input{evil}" not in tex
    assert "evil" in tex
    assert r"\&" in tex
    assert r"\%" in tex
    assert r"\#" in tex
    assert r"\_" in tex
    assert r"\textbackslash{}" in tex


def test_render_omits_empty_projects_section():
    doc = ResumeDocument(
        education=_SAMPLE.education,
        experience=_SAMPLE.experience,
        skills=_SAMPLE.skills,
        projects=(),
    )
    tex = render_resume(doc, template_path=_TEMPLATE)
    assert r"\section{Projects}" not in tex