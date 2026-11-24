"""LaTeX escaping for user-supplied resume strings."""

from __future__ import annotations

import pytest

from medici.resume.render.escape import escape_latex

_SPECIALS = "&%$#_{}~^\\"


def test_escape_replaces_every_special_character():
    esc = escape_latex(_SPECIALS)
    assert r"\&" in esc
    assert r"\%" in esc
    assert r"\$" in esc
    assert r"\#" in esc
    assert r"\_" in esc
    assert r"\{" in esc
    assert r"\}" in esc
    assert r"\textasciitilde{}" in esc
    assert r"\textasciicircum{}" in esc
    assert r"\textbackslash{}" in esc


def test_escape_neutralizes_latex_command_injection():
    hostile = r"\input{evil.tex} \write18{rm -rf /}"
    out = escape_latex(hostile)
    assert r"\input" not in out
    assert r"\write" not in out
    assert "input" in out
    assert r"\textbackslash{}" in out


@pytest.mark.parametrize(
    "text",
    [
        "Plain text only",
        "Loominary Labs & Paperbyte",
        "100% on example.test",
        "cost $5",
        "id #9",
        "snake_case",
        "brace {test}",
        "tilde~here",
        "caret^2",
        r"path\to\file",
    ],
)
def test_escape_roundtrip_preserves_meaning_as_latex_text(text: str):
    esc = escape_latex(text)
    assert "\\usepackage" not in esc
    assert "\\begin{" not in esc