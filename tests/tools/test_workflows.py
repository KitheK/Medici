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
    assert wf["jobs"]["claude-review"]["if"] == "needs.prepare.outputs.run_claude == 'true'"
    assert wf["jobs"]["cursor-review"]["if"] == "needs.prepare.outputs.run_cursor == 'true'"
    assert set(wf["jobs"]["review-gate"]["needs"]) == {"prepare", "claude-review", "cursor-review"}


def test_one_reviewer_is_designated_per_pull_request():
    text = (WF / "agent-review.yml").read_text(encoding="utf-8")
    assert "python3 -m tools.pick_reviewer" in text
    # no line may switch both reviewers on, and the other agent's label is dropped
    assert not re.search(r"run_claude=true;?\s*run_cursor=true", text)
    assert not re.search(r"--add-label review:cursor --add-label review:claude", text)


def test_gate_fails_when_no_reviewer_could_be_designated():
    gate = load("agent-review.yml")["jobs"]["review-gate"]
    assert gate["if"] == "always()"  # a skipped required check counts as passing
    step = gate["steps"][0]
    assert (gate["env"] | step.get("env", {}))["PREPARE"] == "${{ needs.prepare.result }}"
    assert '[ "$PREPARE" != success ]' in step["run"]


def test_reviewers_are_read_only_and_share_one_rubric():
    text = (WF / "agent-review.yml").read_text()
    assert text.count(".github/review-prompt.md") >= 2
    assert "review-rerequest-prompt.md" in text
    assert '--allowedTools "Read,Glob,Grep,Write"' in text
    assert "Shell(*)" in text  # cursor reviewer has no shell
    assert (ROOT / ".github" / "review-prompt.md").is_file()


def test_review_request_labels_exist():
    labels = {e["name"] for e in yaml.safe_load((ROOT / ".github" / "labels.json").read_text())}
    for name in (
        "review:claude",
        "review:cursor",
        "review:request",
        "review:rerequest",
        "review:pass",
        "review:changes",
    ):
        assert name in labels


def test_agent_review_can_be_requested_safely():
    wf = load("agent-review.yml")
    on = triggers(wf)
    assert "labeled" in on["pull_request"]["types"]
    assert "issue_comment" in on
    assert "workflow_dispatch" in on
    text = (WF / "agent-review.yml").read_text()
    assert "review:request" in text
    assert "/review" in text
    assert "collaborators" in text  # comment commands check write permission
    assert "prepare" in wf["jobs"]


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


def test_hygiene_accepts_dependency_bot_branches_without_an_issue_link():
    hygiene = (WF / "pr-hygiene.yml").read_text()
    assert "dependabot" in hygiene
    # the "Closes #n" rule only applies to branches that name an issue
    assert "contains(github.head_ref, 'issue')" in hygiene


CLAUDE_WORKFLOWS = ("agent-review.yml", "build-claude.yml", "fix-conflicts.yml")


def claude_steps(name):
    for job in load(name)["jobs"].values():
        for step in job.get("steps", []):
            if "claude-code-action" in step.get("uses", ""):
                yield step


@pytest.mark.parametrize("name", CLAUDE_WORKFLOWS)
def test_trusted_bots_may_start_claude(name):
    steps = list(claude_steps(name))
    assert steps
    for step in steps:
        assert step["with"]["allowed_bots"] == "${{ env.TRUSTED_BOTS }}"
    assert "cursor[bot]" in load(name)["env"]["TRUSTED_BOTS"].split(",")


@pytest.mark.parametrize("name", CLAUDE_WORKFLOWS)
def test_bots_are_named_one_by_one_because_the_repo_is_public(name):
    assert "*" not in load(name)["env"]["TRUSTED_BOTS"]


def test_trusted_bots_may_comment_commands_even_with_a_footer():
    text = (WF / "agent-review.yml").read_text(encoding="utf-8")
    assert '*",$COMMENT_USER,"*' in text
    assert "first=${COMMENT_BODY%%" in text  # only the first line has to be the command


def test_an_ordinary_comment_does_not_cancel_a_running_review():
    group = load("agent-review.yml")["concurrency"]["group"]
    assert "github.run_id" in group
    assert "startsWith(github.event.comment.body, '/review')" in group
    assert "startsWith(github.event.comment.body, '/rereview')" in group


def test_conflict_fixer_triggers_work_on_a_conflicting_pr():
    on = triggers(load("fix-conflicts.yml"))
    # GitHub does not run pull_request workflows while a PR has conflicts
    assert set(on) == {"issue_comment", "workflow_dispatch", "push"}


def test_conflict_fixer_keeps_agents_away_from_write_tokens():
    jobs = load("fix-conflicts.yml")["jobs"]
    assert jobs["resolve"]["permissions"] == {"contents": "read"}
    assert jobs["verify"]["permissions"] == {"contents": "read"}
    assert "secrets." not in yaml.safe_dump(jobs["verify"])
    assert "GH_PAT" not in yaml.safe_dump(jobs["resolve"])
    writers = [n for n, j in jobs.items() if j.get("permissions", {}).get("contents") == "write"]
    assert writers == ["finish"]
    finish = yaml.safe_dump(jobs["finish"])
    assert "make " not in finish and "claude-code-action" not in finish


def test_conflict_fixer_agents_can_only_edit_files():
    text = (WF / "fix-conflicts.yml").read_text(encoding="utf-8")
    assert '--allowedTools "Read,Glob,Grep,Edit,Write"' in text
    assert '"deny": ["Shell(*)"' in text
    assert "Bash" not in text


def test_conflict_fixer_tests_before_it_pushes_and_never_forces():
    wf = load("fix-conflicts.yml")
    assert "verify" in wf["jobs"]["finish"]["needs"]
    text = (WF / "fix-conflicts.yml").read_text(encoding="utf-8")
    assert "make ci" in text
    assert "--force-with-lease" not in text and "push -f" not in text and "push --force" not in text


def test_conflict_fixer_always_comments_on_the_outcome():
    finish = load("fix-conflicts.yml")["jobs"]["finish"]
    assert finish["if"].startswith("always()")
    assert "gh pr comment" in yaml.safe_dump(finish)


def test_automatic_conflict_sweep_is_opt_in():
    sweep = load("fix-conflicts.yml")["jobs"]["sweep"]
    assert "vars.ENABLE_CONFLICT_SWEEP == 'true'" in sweep["if"]
    assert "vars.ENABLE_AGENTS == 'true'" in sweep["if"]


@pytest.mark.parametrize(
    "name",
    [
        "AGENTS.md",
        ".github/workflows/build-claude.yml",
        ".github/workflows/build-cursor.yml",
        ".github/pull_request_template.md",
    ],
)
def test_agents_are_told_to_add_their_own_progress_file(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    assert "progress/" in text
    for old in ("entry to progress.md", "entry to `progress.md`", "`progress.md` has a dated"):
        assert old not in text, "a shared log makes every open PR conflict"


def test_any_issue_branch_may_add_a_progress_file():
    from tools.check_files_allowed import disallowed

    assert disallowed(["progress/2026-11-24-E2-3.md"], []) == []
    assert disallowed(["progress/nested/x.md", "progress/x.py"], []) != []
    assert "Write(progress/**)" in (ROOT / ".cursor" / "cli.json").read_text(encoding="utf-8")


def test_the_old_progress_log_points_to_the_new_place():
    preamble = (ROOT / "progress.md").read_text(encoding="utf-8").split("## ", 1)[0]
    assert "progress/" in preamble
    assert (ROOT / "progress" / "README.md").is_file()
