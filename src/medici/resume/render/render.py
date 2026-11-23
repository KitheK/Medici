"""Render validated resume JSON into Jake's LaTeX template."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from medici.resume.render.escape import escape_latex
from medici.resume.schema.facts import ResumeDocument

TEMPLATE_MACROS: tuple[str, ...] = (
    "@@MEDICI_EDUCATION@@",
    "@@MEDICI_EXPERIENCE@@",
    "@@MEDICI_PROJECTS@@",
    "@@MEDICI_SKILLS@@",
)

_DEFAULT_TEMPLATE = Path(__file__).resolve().parents[4] / "templates" / "jakes.tex"


def _repo_template_path() -> Path:
    return _DEFAULT_TEMPLATE


def load_template(path: Path | None = None) -> str:
    template_path = path or _repo_template_path()
    return template_path.read_text(encoding="utf-8")


def _education_block(doc: ResumeDocument) -> str:
    if not doc.education:
        return (
            r" \resumeSubHeadingListStart"
            "\n \\resumeSubHeadingListEnd\n"
        )
    lines = [r" \resumeSubHeadingListStart"]
    for entry in doc.education:
        school = escape_latex(entry.school)
        degree = escape_latex(entry.degree)
        dates = escape_latex(entry.dates)
        location = escape_latex(entry.location or "")
        lines.append(" \\resumeSubheading")
        lines.append(f" {{{school}}}{{{location}}}")
        lines.append(f" {{{degree}}}{{{dates}}}")
    lines.append(r" \resumeSubHeadingListEnd")
    return "\n".join(lines) + "\n"


def _experience_block(doc: ResumeDocument) -> str:
    if not doc.experience:
        return (
            r" \resumeSubHeadingListStart"
            "\n \\resumeSubHeadingListEnd\n"
        )
    lines = [r" \resumeSubHeadingListStart"]
    for entry in doc.experience:
        title = escape_latex(entry.title)
        employer = escape_latex(entry.employer)
        dates = escape_latex(entry.dates)
        location = escape_latex(entry.location or "")
        lines.append(" \\resumeSubheading")
        lines.append(f" {{{employer}}}{{{dates}}}")
        lines.append(f" {{{title}}}{{{location}}}")
        if entry.bullets:
            lines.append(r" \resumeItemListStart")
            for bullet in entry.bullets:
                lines.append(f" \\resumeItem{{{escape_latex(bullet)}}}")
            lines.append(r" \resumeItemListEnd")
    lines.append(r" \resumeSubHeadingListEnd")
    return "\n".join(lines) + "\n"


def _projects_block(doc: ResumeDocument) -> str:
    if not doc.projects:
        return ""
    lines = [
        "%-----------PROJECTS-----------",
        r"\section{Projects}",
        r" \resumeSubHeadingListStart",
    ]
    for entry in doc.projects:
        name = escape_latex(entry.name)
        dates = escape_latex(entry.dates)
        tools = ", ".join(escape_latex(t) for t in entry.tools)
        heading = f"\\textbf{{{name}}}"
        if tools:
            heading += f" $|$ \\emph{{{tools}}}"
        lines.append(" \\resumeProjectHeading")
        lines.append(f" {{{heading}}}{{{dates}}}")
        if entry.bullets:
            lines.append(r" \resumeItemListStart")
            for bullet in entry.bullets:
                lines.append(f" \\resumeItem{{{escape_latex(bullet)}}}")
            lines.append(r" \resumeItemListEnd")
    lines.append(r" \resumeSubHeadingListEnd")
    return "\n".join(lines) + "\n"


def _skills_block(doc: ResumeDocument) -> str:
    if not doc.skills:
        skill_text = ""
    else:
        skill_text = ", ".join(escape_latex(s) for s in doc.skills)
    return (
        "%-----------PROGRAMMING SKILLS-----------\n"
        r"\section{Technical Skills}" "\n"
        r" \begin{itemize}[leftmargin=0.15in, label={}]" "\n"
        r" \small{\item{" "\n"
        f" \\textbf{{Skills}}{{: {skill_text}}}" "\n"
        " }}\n"
        r" \end{itemize}" "\n"
    )


def _fill_template_macros(template: str, replacements: dict[str, str]) -> str:
    """Substitute each macro once on the template text only (not on replacement bodies)."""
    for macro in TEMPLATE_MACROS:
        if macro not in template:
            msg = f"missing template macro {macro!r}"
            raise ValueError(msg)
    pattern = re.compile("|".join(re.escape(m) for m in TEMPLATE_MACROS))

    def _replace(match: re.Match[str]) -> str:
        key = match.group(0)
        return replacements[key]

    return pattern.sub(_replace, template)


def render_resume(
    resume: ResumeDocument | Mapping[str, object],
    *,
    template_path: Path | None = None,
) -> str:
    """Return a complete `.tex` document from resume JSON and Jake's template."""
    document = (
        resume if isinstance(resume, ResumeDocument) else ResumeDocument.from_dict(resume)
    )
    template = load_template(template_path)
    replacements = {
        TEMPLATE_MACROS[0]: _education_block(document),
        TEMPLATE_MACROS[1]: _experience_block(document),
        TEMPLATE_MACROS[2]: _projects_block(document),
        TEMPLATE_MACROS[3]: _skills_block(document),
    }
    return _fill_template_macros(template, replacements)