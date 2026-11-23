#!/usr/bin/env python3
"""Task queue: choose the next issue for one builder, so Claude Code and Cursor run in parallel.

Each builder (`claude-code`, `cursor`) has its own lane with a work-in-progress limit. An issue is
pickable when it is `todo`, its dependencies are done and passing, it is owned by that builder, and
nothing is already working on it (open PR or branch). Lanes never share an issue, so two builders
can work at the same moment without touching the same files.

Usage:
  python -m tools.queue pick --owner claude-code [--busy E2-1,E2-2] [--wip 1] [--issue E2-3]
                             [--only E2-3,E2-4]
Prints the issue ID, or nothing (exit 1) if the lane has no work.
"""

from __future__ import annotations

import argparse
import sys

from tools.issue_map import DEFAULT_MAP, by_id, load, ready

BUILDERS = ("claude-code", "cursor")


def pick(
    data: dict,
    owner: str,
    busy: set[str] | None = None,
    wip: int = 1,
    force: str | None = None,
    only: set[str] | None = None,
) -> str | None:
    """Return the issue ID this builder should take, or None.

    `busy` holds IDs that already have an open PR or live branch (any builder). The lane's
    work-in-progress limit counts busy IDs this owner holds; when it is full, nothing is picked.
    `force` lets a human label name a specific issue; it must still be ready.
    `only` restricts the queue to IDs a person opted in with a GitHub label (`agent-queue` for
    on-demand runs, `agent-night` for the scheduled run). None means no label filter.
    """
    busy = busy or set()
    index = by_id(data)
    held = [i for i in busy if i in index and index[i]["owner"] == owner]
    if len(held) >= wip:
        return None
    candidates = [
        i for i in ready(data, owner)
        if i["id"] not in busy and (only is None or i["id"] in only)
    ]
    if force:
        return force if any(i["id"] == force for i in candidates) else None
    return candidates[0]["id"] if candidates else None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("pick")
    s.add_argument("--owner", required=True, choices=BUILDERS)
    s.add_argument("--busy", default="", help="comma-separated IDs with an open PR or branch")
    s.add_argument("--wip", type=int, default=1)
    s.add_argument("--issue", help="only take this issue (label-triggered runs)")
    s.add_argument("--only", help="comma-separated IDs that carry the opt-in label")
    args = p.parse_args(argv)
    busy = {b for b in args.busy.split(",") if b}
    only = None if args.only is None else {x for x in args.only.split(",") if x}
    chosen = pick(load(DEFAULT_MAP), args.owner, busy, args.wip, args.issue, only)
    if chosen is None:
        print("no ready issue in this lane", file=sys.stderr)
        return 1
    print(chosen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
