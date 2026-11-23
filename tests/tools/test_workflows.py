"""Meta-tests for the workflows: structure, parallel lanes, cross-review, injection safety."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github" / "workflows"
FILES = sorted(WF.glob("*.yml"))
UNTRUSTED = re.compile(
    r"\$\{\{\s*github\.(head_ref|event\.(pull_request|issue|comment)\.(title|body|head))"
)


def load(name):
    return yaml.safe_load((WF / name).read_text())


def triggers(wf):
    return wf.get("on") or wf.get(True)  # PyYAML reads the bare key `on` as True


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_workflow_parses_and_declares_permissions(path):
    wf = yaml.safe_load(path.read_text())
    assert "permissions" in wf, "set least-privilege permissions explicitly"
    assert triggers(wf)
    assert "pull_request_target" not in triggers(wf)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_untrusted_text_never_lands_in_a_run_script(path):
    text = path.read_text()
    run_bodies = re.findall(r"run: \|?\n?(.*?)(?=\n\s{6}- |\n\s{4}\w|\Z)", text, re.S)
    for body in run_bodies:
        assert not UNTRUSTED.search(body), "pass untrusted values through env:, not inline in run:"


def test_ci_has_every_test_layer_and_one_required_aggregate():
    ci = load("ci.yml")
    assert {"lint-unit", "integration", "e2e", "scope", "ci"} <= set(ci["jobs"])
    assert set(ci["jobs"]["ci"]["needs"]) == {"lint-unit", "integration", "e2e", "scope"}
    text = (WF / "ci.yml").read_text()
    for target in ("test-unit", "test-integration", "test-e2e", "privacy"):
        assert f"make {target}" in text


def test_builders_run_in_parallel_lanes():
    claude, cursor = load("build-claude.yml"), load("build-cursor.yml")
    assert claude["concurrency"]["group"] != cursor["concurrency"]["group"]
    assert "owner: claude-code" in (WF / "build-claude.yml").read_text()
    assert "owner: cursor" in (WF / "build-cursor.yml").read_text()


def test_builders_are_opt_in():
    for name in ("build-claude.yml", "build-cursor.yml"):
        assert "vars.ENABLE_AGENTS == 'true'" in (WF / name).read_text()


def test_nobody_reviews_their_own_pull_request():
    wf = load("agent-review.yml")
    assert "!startsWith(github.head_ref, 'claude/')" in wf["jobs"]["claude-review"]["if"]
    assert "!startsWith(github.head_ref, 'cursor/')" in wf["jobs"]["cursor-review"]["if"]
    assert set(wf["jobs"]["review-gate"]["needs"]) == {"claude-review", "cursor-review"}


def test_reviewers_are_read_only_and_share_one_rubric():
    text = (WF / "agent-review.yml").read_text()
    assert text.count(".github/review-prompt.md") >= 2
    assert '--allowedTools "Read,Glob,Grep,Write"' in text
    assert "Shell(*)" in text  # cursor reviewer has no shell
    assert (ROOT / ".github" / "review-prompt.md").is_file()


def test_builders_cannot_touch_workflows_or_tooling():
    cfg = (ROOT / ".cursor" / "cli.json").read_text()
    for denied in ("Write(.github/**)", "Write(tools/**)", "Shell(git)", "Shell(gh)"):
        assert denied in cfg
    assert "Never edit .github/ or tools/" in (WF / "build-claude.yml").read_text()


def test_branch_names_match_between_hygiene_scope_check_and_builders():
    from tools.check_files_allowed import ID_IN_BRANCH

    for branch in ("issue/E2-3", "claude/issue-E2-3", "cursor/issue-E5-5"):
        assert ID_IN_BRANCH.search(branch)
    hygiene = (WF / "pr-hygiene.yml").read_text()
    assert "claude/issue" in hygiene and "cursor/issue" in hygiene


def test_injection_detector_catches_a_bad_script():
    assert UNTRUSTED.search('echo "${{ github.event.pull_request.title }}"')
    assert not UNTRUSTED.search('echo "$TITLE"')
