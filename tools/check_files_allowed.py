#!/usr/bin/env python3
"""CI check: a branch named for an issue may only change that issue's `files_allowed`.

Usage: check_files_allowed.py <base-ref>
The issue id comes from the branch name (GITHUB_HEAD_REF or the current branch),
e.g. `issue/E2-3` or `E2-3-fetch-wrapper`. Branches without an id are skipped.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import PurePosixPath

from tools.issue_map import ALWAYS_ALLOWED, DEFAULT_MAP, by_id, load

ID_IN_BRANCH = re.compile(r"[HE]\d+-\d+")


def glob_to_regex(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(f"^{out}$")


def disallowed(changed: list[str], allowed: list[str]) -> list[str]:
    patterns = [glob_to_regex(g) for g in [*allowed, *ALWAYS_ALLOWED]]
    return [f for f in changed if not any(p.match(str(PurePosixPath(f))) for p in patterns)]


def main(argv: list[str]) -> int:
    base = argv[1] if len(argv) > 1 else "origin/main"
    branch = os.environ.get("GITHUB_HEAD_REF") or subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    ).stdout.strip()
    m = ID_IN_BRANCH.search(branch)
    if not m:
        print(f"branch {branch!r} names no issue; skipping files_allowed check")
        return 0
    issue = by_id(load(DEFAULT_MAP)).get(m.group())
    if issue is None:
        print(f"unknown issue {m.group()}")
        return 1
    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True, check=True
    ).stdout.split()
    bad = disallowed(changed, issue["files_allowed"])
    if bad:
        print(f"{issue['id']} changed files outside files_allowed:", *bad, sep="\n  ")
        return 1
    print(f"{issue['id']}: all {len(changed)} changed files are allowed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
