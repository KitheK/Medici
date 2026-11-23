#!/usr/bin/env python3
"""Issue-map tooling: pick the next issue, validate the map, mark an issue complete.

Rules this file enforces (see AGENTS.md):
  * Agents may set `status`. Only `complete` (this script) may set `passes` to true.
  * `complete` runs the issue's acceptance checks that start with "$ " and refuses if any fail.
  * An issue is ready only when every dependency is done AND passed.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAP = ROOT / "issue_map.json"

STATUSES = {"todo", "in_progress", "blocked", "review", "done"}
OWNERS = {"claude-code", "cursor", "human"}
REQUIRED = [
    "id", "title", "epic", "depends_on", "owner", "labels",
    "files_allowed", "acceptance", "status", "passes", "notes",
]
ID_RE = re.compile(r"^[HE]\d+-\d+$")
COMMAND_PREFIX = "$ "  # acceptance lines starting with this are run; everything else is prose
# Files every agent session may touch in addition to its own `files_allowed`.
ALWAYS_ALLOWED = ["issue_map.json", "progress.md"]


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def save(path: Path, data: dict) -> None:
    Path(path).write_text(json.dumps(data, indent=2) + "\n")


def by_id(data: dict) -> dict[str, dict]:
    return {i["id"]: i for i in data["issues"]}


def validate(data: dict) -> list[str]:
    """Return a list of problems; empty means the map is valid."""
    problems: list[str] = []
    issues = data.get("issues", [])
    seen: set[str] = set()
    for i in issues:
        iid = i.get("id", "<missing id>")
        for key in REQUIRED:
            if key not in i:
                problems.append(f"{iid}: missing field '{key}'")
        if iid in seen:
            problems.append(f"{iid}: duplicate id")
        seen.add(iid)
        if not ID_RE.match(str(iid)):
            problems.append(f"{iid}: id must look like E2-3 or H0-1")
        if i.get("status") not in STATUSES:
            problems.append(f"{iid}: bad status {i.get('status')!r}")
        if i.get("owner") not in OWNERS:
            problems.append(f"{iid}: bad owner {i.get('owner')!r}")
        if i.get("passes") is True and i.get("status") != "done":
            problems.append(f"{iid}: passes is true but status is not done")
        if i.get("owner") in {"claude-code", "cursor"} and not i.get("files_allowed"):
            problems.append(f"{iid}: agent issue needs files_allowed")
    for i in issues:
        for dep in i.get("depends_on", []):
            if dep not in seen:
                problems.append(f"{i['id']}: depends on unknown issue {dep}")
            if dep == i["id"]:
                problems.append(f"{i['id']}: depends on itself")
    cycle = find_cycle(issues)
    if cycle:
        problems.append("dependency cycle: " + " -> ".join(cycle))
    return problems


def find_cycle(issues: list[dict]) -> list[str] | None:
    graph = {i["id"]: [d for d in i.get("depends_on", []) if d != i["id"]] for i in issues}
    WHITE, GREY, BLACK = 0, 1, 2
    color = dict.fromkeys(graph, WHITE)
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = GREY
        stack.append(node)
        for dep in graph[node]:
            if dep not in graph:
                continue
            if color[dep] == GREY:
                return [*stack[stack.index(dep):], dep]
            if color[dep] == WHITE and (found := visit(dep)):
                return found
        stack.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE and (found := visit(node)):
            return found
    return None


def ready(data: dict, owner: str | None = None) -> list[dict]:
    """Issues that are todo with every dependency done and passing, in file order."""
    index = by_id(data)
    out = []
    for i in data["issues"]:
        if i["status"] != "todo":
            continue
        if owner and i["owner"] != owner:
            continue
        if all(index[d]["status"] == "done" and index[d]["passes"] for d in i["depends_on"]):
            out.append(i)
    return out


def command_checks(issue: dict) -> list[list[str]]:
    cmds = []
    for line in issue["acceptance"]:
        if line.startswith(COMMAND_PREFIX):
            argv = shlex.split(line[len(COMMAND_PREFIX):])
            if argv[0] == "pytest":
                argv = [sys.executable, "-m", "pytest", *argv[1:]]
            elif argv[0] in {"python", "python3"}:
                argv[0] = sys.executable
            cmds.append(argv)
    return cmds


def complete(path: Path, issue_id: str, cwd: Path | None = None) -> int:
    data = load(path)
    problems = validate(data)
    if problems:
        print("refused: issue map is invalid", *problems, sep="\n  ")
        return 2
    issue = by_id(data).get(issue_id)
    if issue is None:
        print(f"refused: unknown issue {issue_id}")
        return 2
    if issue["owner"] == "human":
        print("refused: human issues are closed by hand, with a note saying who reviewed it")
        return 2
    cmds = command_checks(issue)
    if not cmds:
        print(f"refused: {issue_id} has no command-style acceptance check to run")
        return 2
    for argv in cmds:
        print("running:", " ".join(argv))
        if subprocess.run(argv, cwd=cwd or Path(path).parent).returncode != 0:
            print(f"refused: acceptance check failed for {issue_id}; passes stays false")
            return 1
    issue["status"] = "done"
    issue["passes"] = True
    save(path, data)
    print(f"{issue_id}: passes")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--map", type=Path, default=DEFAULT_MAP)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    n = sub.add_parser("next")
    n.add_argument("--owner", choices=sorted(OWNERS))
    n.add_argument("--all", action="store_true", help="list every ready issue")
    c = sub.add_parser("complete")
    c.add_argument("issue_id")
    args = p.parse_args(argv)

    if args.cmd == "validate":
        problems = validate(load(args.map))
        if problems:
            print("issue map invalid:", *problems, sep="\n  ")
            return 1
        print("issue map ok")
        return 0
    if args.cmd == "next":
        found = ready(load(args.map), args.owner)
        if not found:
            print("no ready issue")
            return 1
        for i in found if args.all else found[:1]:
            print(f"{i['id']}\t{i['owner']}\t{i['title']}")
        return 0
    return complete(args.map, args.issue_id)


if __name__ == "__main__":
    raise SystemExit(main())
