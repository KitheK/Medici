#!/usr/bin/env python3
"""Designate the one agent that reviews a pull request: never the agent that made it.

Reads `gh pr view <n> --json headRefName,body,commits` on stdin and prints `claude` or `cursor`.

The author is decided by the first of these that gives one answer:
  1. the builder branch prefix (`claude/`, `cursor/`)
  2. the marker the agent's own tool leaves in the PR body
  3. the agent that wrote or co-wrote the most commits
A human PR, or an even mix, has no agent author and goes to DEFAULT_REVIEWER.
"""

from __future__ import annotations

import json
import re
import sys

OTHER = {"claude": "cursor", "cursor": "claude"}
DEFAULT_REVIEWER = "claude"

BODY_MARKERS = {
    "claude": re.compile(r"Generated (?:with|by) \[Claude Code\]\(https://claude\.(?:ai|com)/"),
    "cursor": re.compile(r"<!-- CURSOR_AGENT_PR_BODY_BEGIN -->"),
}
LOGINS = {"claude": "claude", "cursoragent": "cursor"}


def _from_branch(head: str) -> str | None:
    prefix = head.split("/", 1)[0]
    return prefix if prefix in OTHER else None


def _from_body(body: str) -> str | None:
    found = [agent for agent, marker in BODY_MARKERS.items() if marker.search(body)]
    return found[0] if len(found) == 1 else None


def _from_commits(commits: list[dict]) -> str | None:
    votes = dict.fromkeys(OTHER, 0)
    for commit in commits:
        # gh lists co-authors here too, with the GitHub login their trailer resolves to
        people = commit.get("authors") or []
        agents = {LOGINS.get((p.get("login") or "").lower()) for p in people}
        for agent in agents - {None}:
            votes[agent] += 1
    if votes["claude"] == votes["cursor"]:
        return None
    return max(votes, key=votes.__getitem__)


def author(pr: dict) -> str | None:
    """Return the agent that made the PR, or None for a human or an even mix."""
    return (
        _from_branch(pr.get("headRefName") or "")
        or _from_body(pr.get("body") or "")
        or _from_commits(pr.get("commits") or [])
    )


def reviewer(pr: dict) -> str:
    made_by = author(pr)
    return OTHER[made_by] if made_by else DEFAULT_REVIEWER


def main() -> int:
    pr = json.load(sys.stdin)
    chosen = reviewer(pr)
    print(f"author: {author(pr) or 'human or mixed'}; reviewer: {chosen}", file=sys.stderr)
    print(chosen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
