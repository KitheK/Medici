"""Escape user text for safe inclusion in LaTeX."""

from __future__ import annotations

_REPLACEMENTS: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text: str) -> str:
    """Return *text* with LaTeX special characters escaped."""
    return "".join(_REPLACEMENTS.get(ch, ch) for ch in text)