#!/usr/bin/env python3
"""The deterministic half of fix-conflicts.yml: what may be fixed, what may be pushed, what to say.

An agent only edits the conflicted files. Everything else is decided here, from the default
branch's copy of this file, so nothing an agent or a PR writes can widen what is pushed:
  plan     merge base into head; list the files an agent may resolve, or hand over to a human
  collect  take only those files from the agent's working tree, and check them
  apply    redo the merge from scratch and put the collected files in
  comment  write the PR comment

Append-only logs (AUTO) keep both sides without an agent.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

MAX_FILES = 20
MAX_NOTES = 4000
AUTO = ("progress.md",)
PROTECTED = (
    ".github/*", ".claude/*", ".cursor/*", "tools/*", "tests/privacy/*",
    "AGENTS.md", "*/AGENTS.md", "CLAUDE.md", "*/CLAUDE.md",
    "Makefile", "init.sh", "pyproject.toml", ".gitignore", ".gitattributes",
)
MARKER = re.compile(r"^(<{7}|>{7}|\|{7}) ", re.M)
SECRET = re.compile(r"(?:sk-ant-|gh[pousr]_|github_pat_)[A-Za-z0-9_-]{16,}")
AGENTS = {"claude": "Claude", "cursor": "Cursor"}


class Rejected(Exception):
    """The resolution must not be pushed."""


def _git(repo, *args: str, ok: tuple[int, ...] = (0,)) -> bytes:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if done.returncode not in ok:
        raise Rejected(f"git {args[0]} failed: {done.stderr.decode(errors='replace').strip()}")
    return done.stdout


def _merge(repo, head: str, base: str) -> dict[str, dict[int, str]]:
    """Start merging base into head; return {conflicted path: {stage: file mode}}."""
    _git(repo, "reset", "-q", "--hard")
    _git(repo, "checkout", "-q", "--detach", head)
    _git(
        repo, "-c", "merge.conflictStyle=zdiff3", "-c", "user.name=merge",
        "-c", "user.email=merge@example.invalid", "merge", "--no-commit", "--no-ff", base,
        ok=(0, 1),
    )
    stages: dict[str, dict[int, str]] = {}
    for entry in _git(repo, "ls-files", "-u", "-z").decode().split("\0"):
        if entry:
            meta, path = entry.split("\t", 1)
            mode, _, stage = meta.split()
            stages.setdefault(path, {})[int(stage)] = mode
    return stages


def plan(repo, head: str, base: str) -> dict:
    """Merge, and say what may be fixed. Leaves the merge in progress for the agent."""
    stages = _merge(repo, head, base)
    result = {"status": "conflicts", "files": [], "auto": [], "reason": ""}
    if not stages:
        return result | {"status": "clean"}
    problems = []
    for path, modes in sorted(stages.items()):
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in PROTECTED):
            problems.append(f"`{path}` is protected")
        elif not {2, 3} <= set(modes):
            problems.append(f"`{path}` was deleted on one side")
        elif not set(modes.values()) <= {"100644", "100755"}:
            problems.append(f"`{path}` is not a regular file")
        elif b"\0" in _git(repo, "show", f":2:{path}") + _git(repo, "show", f":3:{path}"):
            problems.append(f"`{path}` is binary")
        elif path in AUTO and 1 in modes and _keep_both(repo, path) is not None:
            result["auto"].append(path)
        else:
            result["files"].append(path)
    if len(result["files"]) > MAX_FILES:
        problems.append(f"{len(result['files'])} files conflict, more than {MAX_FILES}")
    if problems:
        return result | {"status": "human", "reason": "; ".join(problems)}
    return result


def check_text(path: str, text: str) -> None:
    if MARKER.search(text):
        raise Rejected(f"{path} still has a conflict marker")
    if SECRET.search(text):
        raise Rejected(f"{path} has text that looks like a secret")
    if path.endswith(".json"):
        try:
            json.loads(text)
        except ValueError as err:
            raise Rejected(f"{path} is not valid JSON") from err


def _read(root: Path, path: str) -> bytes:
    target = root / path
    if target.is_symlink() or not target.is_file():
        raise Rejected(f"{path} is missing or not a regular file")
    data = target.read_bytes()
    try:
        check_text(path, data.decode("utf-8"))
    except UnicodeDecodeError as err:
        raise Rejected(f"{path} is not UTF-8 text") from err
    return data


def collect(repo, files: list[str], out) -> None:
    """Copy only the planned files out of the agent's working tree, after checking them."""
    contents = {path: _read(Path(repo), path) for path in files}
    for path, data in contents.items():
        target = Path(out) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _check_issue_map(repo, head: str, base: str, text: str) -> None:
    """An agent may combine issue_map.json, never decide what passes or what may be touched."""

    def index(raw) -> dict:
        return {issue["id"]: issue for issue in json.loads(raw)["issues"]}

    try:
        merged = index(text)
        sides = [index(_git(repo, "show", f"{rev}:issue_map.json")) for rev in (head, base)]
    except (ValueError, KeyError, TypeError) as err:
        raise Rejected("issue_map.json does not have the expected shape") from err
    if set(merged) != set(sides[0]) | set(sides[1]):
        raise Rejected("issue_map.json gained or lost an issue")
    for iid, issue in merged.items():
        for key in ("passes", "files_allowed", "owner", "acceptance", "depends_on"):
            if issue.get(key) not in [side[iid].get(key) for side in sides if iid in side]:
                raise Rejected(f"issue_map.json: {iid} has a {key} value from neither side")


def _entries(text: str) -> dict[str, str] | None:
    """Split a log into {heading: whole entry}; the part before the first entry has heading ''."""
    blocks = re.split(r"^(?=## )", text, flags=re.M)
    entries = {"": blocks[0].strip("\n")}
    for block in blocks[1:]:
        heading = block.split("\n", 1)[0].strip()
        if heading in entries:
            return None
        entries[heading] = block.strip("\n")
    return entries


def combine_log(*, base: str, start: str, head: str) -> str | None:
    """Combine whole entries, base's first. None when that would mean guessing."""
    ours, old, theirs = _entries(head), _entries(start), _entries(base)
    if ours is None or old is None or theirs is None:
        return None
    merged = []
    for heading in [*theirs, *(h for h in ours if h not in theirs)]:
        b, s, h = theirs.get(heading), old.get(heading), ours.get(heading)
        if b == h or h == s:
            entry = b
        elif b == s:
            entry = h
        else:
            return None
        if entry is None:
            return None  # one side removed it; a log should only grow
        merged.append(entry)
    return "\n\n".join(e for e in merged if e) + "\n"


def _keep_both(repo, path: str) -> str | None:
    sides = {}
    for name, stage in (("base", 3), ("start", 1), ("head", 2)):
        text = _git(repo, "show", f":{stage}:{path}").decode("utf-8", errors="replace")
        sides[name] = text.replace("\r\n", "\n")
    return combine_log(**sides)


def apply(repo, head: str, base: str, out) -> None:
    """Redo the merge and stage exactly the planned files. The caller commits."""
    planned = plan(repo, head, base)
    if planned["status"] != "conflicts":
        raise Rejected(f"merge is now {planned['status']}: {planned['reason']}")
    out = Path(out)
    given = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if not p.is_dir())
    if given != sorted(planned["files"]):
        raise Rejected("the resolved files are not exactly the conflicted files")
    for path in planned["files"]:
        data = _read(out, path)
        if path == "issue_map.json":
            _check_issue_map(repo, head, base, data.decode("utf-8"))
        (Path(repo) / path).write_bytes(data)
    for path in planned["auto"]:
        (Path(repo) / path).write_bytes((_keep_both(repo, path) or "").encode("utf-8"))
    _git(repo, "add", "--", *planned["files"], *planned["auto"])


def _clean_notes(notes: str) -> str:
    """Agent notes are untrusted: no mentions, no HTML, no secrets, bounded length."""
    notes = SECRET.sub("[removed]", notes.strip())[:MAX_NOTES]
    notes = notes.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return notes.replace("@", "@​")


def comment(
    *, outcome: str, fixer: str, files: list[str], auto: list[str], notes: str, commit: str,
    ci_starts: bool, reason: str,
) -> str:
    if outcome == "clean":
        return "### Merge conflicts\n\nThis PR has no merge conflicts, so nothing was changed.\n"
    if outcome != "fixed":
        why = _clean_notes(reason) or "the run failed; see its log"
        return f"### Merge conflicts: needs a human\n\nNothing was pushed. Reason: {why}.\n"
    lines = ["### Fixed merge conflicts", "", f"Merged the base branch in {commit}."]
    if auto:
        lines += ["", "**Merged automatically (kept both sides):**", ""]
        lines += [f"- `{path}`" for path in auto]
    if files:
        lines += ["", f"**Resolved by {AGENTS[fixer]}:**", ""]
        lines += [f"- `{path}`" for path in files]
        lines += ["", "**What was fixed:**", ""]
        lines.append(_clean_notes(notes) or f"{AGENTS[fixer]} did not leave notes; see the commit.")
    lines += ["", "`make ci` passed on the merged result before it was pushed."]
    if not ci_starts:
        lines += [
            "",
            "Checks and review do not start by themselves on this commit, because the `GH_PAT` "
            "secret is not set. Push any commit to start them.",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "apply"):
        s = sub.add_parser(name)
        s.add_argument("--repo", required=True)
        s.add_argument("--head", required=True)
        s.add_argument("--base", required=True)
        if name == "apply":
            s.add_argument("--out", required=True)
    s = sub.add_parser("collect")
    s.add_argument("--repo", required=True)
    s.add_argument("--plan", required=True)
    s.add_argument("--out", required=True)
    s = sub.add_parser("comment")
    s.add_argument("--outcome", required=True)
    s.add_argument("--fixer", choices=[*AGENTS, ""], default="")
    s.add_argument("--plan")
    s.add_argument("--notes")
    s.add_argument("--commit", default="")
    s.add_argument("--ci-starts", action="store_true")
    s.add_argument("--reason", default="")
    args = p.parse_args(argv)

    def load_plan() -> dict:
        path = Path(args.plan) if args.plan else None
        return json.loads(path.read_text(encoding="utf-8")) if path and path.is_file() else {}

    try:
        if args.cmd == "plan":
            print(json.dumps(plan(args.repo, args.head, args.base)))
        elif args.cmd == "collect":
            collect(args.repo, load_plan()["files"], args.out)
        elif args.cmd == "apply":
            apply(args.repo, args.head, args.base, args.out)
        else:
            planned = load_plan()
            notes = Path(args.notes) if args.notes else None
            print(comment(
                outcome=args.outcome, fixer=args.fixer,
                files=planned.get("files", []), auto=planned.get("auto", []),
                notes=notes.read_text(encoding="utf-8", errors="replace")
                if notes and notes.is_file() else "",
                commit=args.commit, ci_starts=args.ci_starts,
                reason=args.reason or planned.get("reason", ""),
            ))
    except Rejected as err:
        print(f"::error::{err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
