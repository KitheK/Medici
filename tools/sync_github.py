#!/usr/bin/env python3
"""Create or update GitHub labels, milestones and issues from issue_map.json.

Idempotent: issues are matched by their "[ID] " title prefix. issue_map.json is the source of
truth; issue bodies are overwritten on every sync. Needs `gh` authenticated (GH_TOKEN).

Usage: python3 -m tools.sync_github [--repo OWNER/NAME] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from tools.issue_map import DEFAULT_MAP, by_id, load

ROOT = Path(__file__).resolve().parent.parent
ASSIGNEE = "KitheK"
EPICS = {
    "H0": "Setup", "E0": "Decisions", "E1": "Feasibility spike", "E2": "Walking skeleton",
    "E3": "People lane", "E4": "Email step", "E5": "Resume engine", "E6": "Saved network",
    "E7": "Review screen", "E8": "Launch checks", "E9": "Batch runner",
}
GUIDED_ROOTS = ("src/medici/", "web/src/", "templates/", "migrations/")
MARKER = "<!-- medici-issue-id: {id} -->"


def title_of(issue: dict) -> str:
    return f"[{issue['id']}] {issue['title']}"


def labels_of(issue: dict) -> list[str]:
    kind = "human" if issue["owner"] == "human" else "agent"
    return sorted({kind, f"owner:{issue['owner']}", f"epic:{issue['epic']}",
                   f"status:{issue['status']}", *issue["labels"]} - {"human:decision"})


def guides_of(issue: dict) -> list[str]:
    return [p[:-3] + "/AGENTS.md" for p in issue["files_allowed"]
            if p.endswith("/**") and p.startswith(GUIDED_ROOTS)]


def render_body(issue: dict, index: dict[str, dict], numbers: dict[str, int]) -> str:
    def dep_line(d: str) -> str:
        n = numbers.get(d)
        return f"- {'#' + str(n) if n else d} {index[d]['title']} (`{d}`)"

    acc = []
    for line in issue["acceptance"]:
        acc.append(f"- [ ] `{line[2:]}`" if line.startswith("$ ") else f"- [ ] {line}")
    out = [
        f"**ID** `{issue['id']}` · **Owner** `{issue['owner']}` · **Epic** {issue['epic']} "
        f"{EPICS[issue['epic']]}",
        "",
        "> Source of truth is `issue_map.json`. Edit that file, not this body; sync overwrites it.",
        "",
        "### Depends on",
        *([dep_line(d) for d in issue["depends_on"]] or ["- nothing"]),
        "",
    ]
    if issue["files_allowed"]:
        out += ["### Files allowed", *(f"- `{p}`" for p in issue["files_allowed"]), ""]
    out += ["### Acceptance", *acc, ""]
    if issue["owner"] == "human":
        out += ["### How this closes",
                "Close by hand once done, with a comment saying who reviewed it. "
                "`complete` refuses human issues.", ""]
    else:
        out += [
            "### Read first",
            "- `AGENTS.md` (shared rules) and `progress.md`",
            *(f"- `{g}` (what to produce here)" for g in guides_of(issue)),
            "",
            "### Workflow",
            f"1. `bash init.sh`, then branch `issue/{issue['id']}` in its own worktree "
            "(`make hooks` adds the co-author trailer).",
            "2. Failing test first, then code. Touch only `files_allowed`.",
            f"3. `python3 tools/issue_map.py complete {issue['id']}`; open a PR that says "
            f"`Closes #<this issue>`.",
            "",
        ]
    out += [f"Requested by @{ASSIGNEE}.", "", MARKER.format(id=issue["id"])]
    return "\n".join(out)


class Gh:
    def __init__(self, repo: str, dry: bool):
        self.repo, self.dry = repo, dry

    def call(self, method: str, path: str, payload: dict | None = None):
        cmd = ["gh", "api", "-X", method, f"repos/{self.repo}/{path}"]
        if payload is not None:
            cmd += ["--input", "-"]
        if self.dry and method != "GET":
            label = (payload or {}).get("title") or (payload or {}).get("name") or ""
            print("DRY", method, path, label)
            return {"number": 0}
        res = subprocess.run(cmd, input=json.dumps(payload) if payload is not None else None,
                             capture_output=True, text=True)
        if res.returncode:
            raise SystemExit(f"{method} {path} failed: {res.stderr or res.stdout}")
        return json.loads(res.stdout) if res.stdout.strip() else {}

    def list(self, path: str) -> list[dict]:
        out, page = [], 1
        sep = "&" if "?" in path else "?"
        while True:
            chunk = self.call("GET", f"{path}{sep}per_page=100&page={page}")
            out += chunk
            if len(chunk) < 100:
                return out
            page += 1


def sync(repo: str, dry: bool) -> None:
    gh = Gh(repo, dry)
    data = load(DEFAULT_MAP)
    index = by_id(data)

    have = {label["name"]: label for label in gh.list("labels")}
    for want in json.loads((ROOT / ".github/labels.json").read_text()):
        cur = have.get(want["name"])
        if cur is None:
            gh.call("POST", "labels", want)
        elif cur["color"] != want["color"] or (cur["description"] or "") != want["description"]:
            gh.call("PATCH", f"labels/{want['name']}", want)

    milestones = {m["title"]: m["number"] for m in gh.list("milestones?state=all")}
    for epic, name in EPICS.items():
        title = f"{epic} {name}"
        if title not in milestones:
            milestones[title] = gh.call("POST", "milestones", {"title": title})["number"]

    existing = {}
    for it in gh.list("issues?state=all"):
        if "pull_request" not in it and it["title"].startswith("["):
            existing[it["title"].split("]")[0][1:]] = it
    numbers = {iid: it["number"] for iid, it in existing.items()}

    for issue in data["issues"]:  # pass 1: make sure every issue exists
        if issue["id"] not in existing:
            created = gh.call("POST", "issues", {
                "title": title_of(issue), "body": "creating...", "assignees": [ASSIGNEE],
                "labels": labels_of(issue),
                "milestone": milestones[f"{issue['epic']} {EPICS[issue['epic']]}"],
            })
            numbers[issue["id"]] = created["number"]
            existing[issue["id"]] = created
            print("created", issue["id"], created["number"])

    for issue in data["issues"]:  # pass 2: bodies now know every dependency number
        done = issue["status"] == "done" and issue["passes"]
        gh.call("PATCH", f"issues/{numbers[issue['id']]}", {
            "title": title_of(issue), "body": render_body(issue, index, numbers),
            "labels": labels_of(issue), "assignees": [ASSIGNEE],
            "milestone": milestones[f"{issue['epic']} {EPICS[issue['epic']]}"],
            "state": "closed" if done else "open",
            **({"state_reason": "completed"} if done else {}),
        })
    print(f"synced {len(data['issues'])} issues to {repo}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="KitheK/Medici")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sync(args.repo, args.dry_run)
