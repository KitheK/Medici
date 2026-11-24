"""Fill Jake's resume template from validated resume JSON."""

from medici.resume.render.escape import escape_latex
from medici.resume.render.render import render_resume

__all__ = ["escape_latex", "render_resume"]