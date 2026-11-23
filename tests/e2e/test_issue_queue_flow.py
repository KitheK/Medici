"""End-to-end: drive the issue-map CLI the way an agent session does."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

ROOT = Path(__file__).resolve().parents[2]


def issue(iid, deps=(), owner="claude-code", cmd="$ python -c 'pass'"):
    return {
        "id": iid, "title": iid, "epic": iid.split("-")[0], "depends_on": list(deps),
        "owner": owner, "labels": [], "files_allowed": ["src/**"], "acceptance": [cmd],
        "status": "todo", "passes": False, "notes": "",
    }


def cli(map_path, *args):
    return subprocess.run(
        [sys.executable, "-m", "tools.issue_map", "--map", str(map_path), *args],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_pick_complete_unblocks_the_next_issue(tmp_path):
    path = tmp_path / "issue_map.json"
    path.write_text(json.dumps({"version": 1, "issues": [
        issue("E2-1"), issue("E2-2", deps=["E2-1"]),
    ]}))
    assert cli(path, "next").stdout.startswith("E2-1")
    assert cli(path, "complete", "E2-1").returncode == 0
    assert cli(path, "next").stdout.startswith("E2-2")


def test_failing_acceptance_keeps_the_queue_blocked(tmp_path):
    path = tmp_path / "issue_map.json"
    bad = issue("E2-1", cmd="$ python -c 'raise SystemExit(3)'")
    path.write_text(json.dumps({"version": 1, "issues": [bad, issue("E2-2", deps=["E2-1"])]}))
    assert cli(path, "complete", "E2-1").returncode == 1
    assert cli(path, "next").stdout.startswith("E2-1")  # still the head of the queue
