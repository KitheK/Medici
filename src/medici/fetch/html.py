"""HTML to Markdown conversion."""

from __future__ import annotations

import re
from html.parser import HTMLParser

_SCRIPT_STYLE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)


def _is_hidden(attrs: list[tuple[str, str | None]]) -> bool:
    attr = {k.lower(): (v or "") for k, v in attrs}
    if attr.get("hidden") is not None:
        return True
    if attr.get("aria-hidden", "").lower() == "true":
        return True
    style = attr.get("style", "").replace(" ", "").lower()
    return "display:none" in style or "visibility:hidden" in style


class _ToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._hidden_depth = 0
        self._tag_stack: list[bool] = []
        self._skip: set[str] = set()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in {"script", "style", "noscript"}:
            self._skip.add(t)
            return
        hidden = _is_hidden(attrs)
        if self._skip:
            return
        if self._hidden_depth:
            self._tag_stack.append(hidden)
            if hidden:
                self._hidden_depth += 1
            return
        if hidden:
            self._hidden_depth += 1
            self._tag_stack.append(True)
            return
        self._tag_stack.append(False)
        if t in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(t[1])
            self._parts.append("\n" + "#" * level + " ")
        elif t == "p":
            self._parts.append("\n\n")
        elif t == "br":
            self._parts.append("\n")
        elif t == "li":
            self._parts.append("\n- ")
        elif t == "strong" or t == "b":
            self._parts.append("**")
        elif t == "em" or t == "i":
            self._parts.append("*")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self._skip:
            self._skip.discard(t)
            return
        if self._hidden_depth:
            was_hidden = self._tag_stack.pop() if self._tag_stack else False
            if was_hidden:
                self._hidden_depth -= 1
            return
        if self._tag_stack:
            self._tag_stack.pop()
        if t in {"h1", "h2", "h3", "h4", "h5", "h6", "p"}:
            self._parts.append("\n")
        elif t == "strong" or t == "b":
            self._parts.append("**")
        elif t == "em" or t == "i":
            self._parts.append("*")

    def handle_data(self, data: str) -> None:
        if self._skip or self._hidden_depth:
            return
        self._parts.append(data)

    def get_markdown(self) -> str:
        text = "".join(self._parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_markdown(html: str) -> str:
    """Convert HTML to plain Markdown, dropping scripts, styles and hidden blocks."""
    cleaned = _SCRIPT_STYLE.sub("", html)
    parser = _ToMarkdown()
    parser.feed(cleaned)
    return parser.get_markdown()