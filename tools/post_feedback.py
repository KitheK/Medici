#!/usr/bin/env python3
"""Turn a mentor reviewer's feedback.json into one GitHub review with inline comments.

The reviewer agent is read-only: it writes feedback.json and this script does the posting. It
- anchors every inline comment to a line that is really in the PR diff (GitHub rejects the whole
  review otherwise) and moves any other comment into the review body,
- renders "suggestion" fixes as GitHub suggested changes the author can apply with one click,
- neutralises @mentions and HTML comments in agent text, and caps the volume,
- never fails the build: feedback is advice, not a merge gate.

Usage: python -m tools.post_feedback --repo OWNER/NAME --pr N
       [--feedback feedback.json] [--diff pr.diff]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MARKER = "<!-- medici-mentor-feedback -->"
MAX_INLINE = 15
MAX_TEXT = 2000
MAX_FILE_BYTES = 200_000
CATEGORIES = {
    "anti-pattern", "pattern", "design", "naming", "testing", "error-handling",
    "security", "performance", "readability", "purpose",
}
SEVERITIES = ("fix", "consider", "learn")  # most to least important
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def commentable_lines(diff: str) -> dict[str, set[int]]:
    """Map each changed file to the new-side line numbers a review comment may attach to."""
    out: dict[str, set[int]] = {}
    path: str | None = None
    new_line = 0
    in_hunk = False
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            path, in_hunk = None, False
        elif raw.startswith("+++ "):
            target = raw[4:].strip()
            path = None if target == "/dev/null" else target.removeprefix("b/")
            if path:
                out.setdefault(path, set())
        elif (m := HUNK.match(raw)) and path:
            new_line, in_hunk = int(m.group(1)), True
        elif in_hunk and path:
            if raw.startswith("+") or raw.startswith(" "):
                out[path].add(new_line)
                new_line += 1
            elif raw.startswith("-") or raw.startswith("\\"):
                continue
            else:
                in_hunk = False
    return out


def clean(text: object, limit: int = MAX_TEXT) -> str:
    """Agent text is untrusted: no pings, no hidden HTML comments, bounded length."""
    s = str(text or "").strip()
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"@(?=\w)", "@​", s)
    return s[:limit]


def fence(code: str) -> str:
    longest = max((len(r) for r in re.findall(r"`+", code)), default=0)
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}suggestion\n{code.rstrip(chr(10))}\n{ticks}"


def inline_body(c: dict, suggest: bool) -> str:
    head = f"**{c['severity']} · {c['category']}** — {clean(c.get('body'))}"
    if suggest and c.get("suggestion") is not None:
        head += "\n\n" + fence(str(c["suggestion"])[:MAX_TEXT])
    return head


def normalise(raw: dict) -> dict:
    comments = []
    for c in raw.get("comments") or []:
        if not isinstance(c, dict) or not c.get("path") or not isinstance(c.get("line"), int):
            continue
        sev = c.get("severity") if c.get("severity") in SEVERITIES else "consider"
        cat = c.get("category") if c.get("category") in CATEGORIES else "design"
        start = c.get("start_line") if isinstance(c.get("start_line"), int) else None
        comments.append({**c, "severity": sev, "category": cat, "start_line": start})
    comments.sort(key=lambda c: SEVERITIES.index(c["severity"]))  # stable within a severity
    return {**raw, "comments": comments}


def build_review(raw: dict, diff: str) -> dict:
    fb = normalise(raw)
    ok = commentable_lines(diff)
    inline, overflow = [], []
    for c in fb["comments"]:
        lines = ok.get(c["path"], set())
        start = c["start_line"] if c["start_line"] and c["start_line"] < c["line"] else None
        span = range(start or c["line"], c["line"] + 1)
        anchored = bool(lines) and all(n in lines for n in span) and len(inline) < MAX_INLINE
        if anchored:
            payload = {"path": c["path"], "line": c["line"], "side": "RIGHT",
                       "body": inline_body(c, suggest=True)}
            if start:
                payload.update(start_line=start, start_side="RIGHT")
            inline.append(payload)
        else:
            overflow.append(c)

    parts = [MARKER, "### Mentor feedback", "", clean(fb.get("summary"))]
    pc = fb.get("purpose_check") or {}
    if pc:
        parts += ["", f"**Does it do what it is for?** {clean(pc.get('verdict'), 40)}. "
                      f"{clean(pc.get('notes'))}"]
    if fb.get("strengths"):
        wins = [f"- {clean(s, 400)}" for s in fb["strengths"][:5]]
        parts += ["", "**What is working well**", *wins]
    if fb.get("alternatives"):
        parts += ["", "**Another way to think about it**"]
        for a in fb["alternatives"][:3]:
            where = f" (`{clean(a.get('where'), 120)}`)" if a.get("where") else ""
            line = f"- **{clean(a.get('title'), 120)}**{where}: {clean(a.get('idea'), 700)}"
            if a.get("tradeoffs"):
                line += f" _Trade-offs:_ {clean(a.get('tradeoffs'), 500)}"
            parts.append(line)
    if fb.get("concepts"):
        parts += ["", "**Concepts worth learning from this PR**"]
        parts += [f"- **{clean(k.get('name'), 80)}**: {clean(k.get('explanation'), 500)}"
                  for k in fb["concepts"][:5]]
    if overflow:
        parts += ["", "**More notes (not on a changed line)**"]
        parts += [f"- `{c['path']}:{c['line']}` {c['severity']} · {c['category']}: "
                  f"{clean(c.get('body'), 600)}" for c in overflow]
    parts += ["", "_Advisory feedback to learn from. It never blocks a merge._"]
    return {"event": "COMMENT", "body": "\n".join(parts), "comments": inline}


def post(repo: str, pr: int, review: dict) -> bool:
    def call(payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["gh", "api", f"repos/{repo}/pulls/{pr}/reviews", "--input", "-"],
            input=json.dumps(payload), capture_output=True, text=True,
        )

    res = call(review)
    if res.returncode and review["comments"]:  # a bad anchor must not lose the feedback
        folded = "\n".join(f"- `{c['path']}:{c['line']}` {c['body']}" for c in review["comments"])
        res = call({"event": "COMMENT", "comments": [],
                    "body": review["body"] + "\n\n**Inline notes**\n" + folded})
    if res.returncode:
        print(res.stderr or res.stdout, file=sys.stderr)
    return res.returncode == 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True)
    p.add_argument("--pr", type=int, required=True)
    p.add_argument("--feedback", type=Path, default=Path("feedback.json"))
    p.add_argument("--diff", type=Path, default=Path("pr.diff"))
    a = p.parse_args(argv)
    try:
        if a.feedback.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("feedback.json too large")
        raw = json.loads(a.feedback.read_text())
        if not isinstance(raw, dict):
            raise ValueError("feedback.json must be an object")
    except (OSError, ValueError) as err:  # advisory: never fail the PR over this
        print(f"::warning::no usable feedback ({err}); nothing posted")
        return 0
    review = build_review(raw, a.diff.read_text() if a.diff.exists() else "")
    ok = post(a.repo, a.pr, review)
    print(f"posted review with {len(review['comments'])} inline comments" if ok else "post failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
