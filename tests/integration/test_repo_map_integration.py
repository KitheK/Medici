"""Integration: the real issue map, the real area guides and the real CLI agree."""

import subprocess
import sys
from pathlib import Path

import pytest

from tools import issue_map as im

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]


def test_cli_validate_passes_on_the_real_map():
    out = subprocess.run(
        [sys.executable, "-m", "tools.issue_map", "validate"], cwd=ROOT, capture_output=True,
        text=True,
    )
    assert out.returncode == 0, out.stdout + out.stderr


def test_every_agent_issue_has_a_runnable_check_and_a_reviewable_scope():
    for i in im.load(im.DEFAULT_MAP)["issues"]:
        if i["owner"] == "human":
            continue
        assert im.command_checks(i), i["id"]
        assert i["files_allowed"], i["id"]
