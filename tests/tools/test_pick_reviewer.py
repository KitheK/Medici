import io
import json

import pytest

from tools import pick_reviewer as pr

CURSOR_BODY = "Adds a parser.\n<!-- CURSOR_AGENT_PR_BODY_BEGIN -->\nx"
CLAUDE_BODY = "Adds a parser.\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"


def commit(*logins):
    return {"authors": [{"login": name} for name in logins]}


def pull(head="issue/E2-3", body="", commits=()):
    return {"headRefName": head, "body": body, "commits": list(commits)}


@pytest.mark.parametrize(
    ("head", "reviewer"),
    [("cursor/issue-E2-3", "claude"), ("claude/issue-E2-3", "cursor")],
)
def test_builder_branch_is_reviewed_by_the_other_agent(head, reviewer):
    assert pr.reviewer(pull(head=head)) == reviewer


@pytest.mark.parametrize(("body", "reviewer"), [(CURSOR_BODY, "claude"), (CLAUDE_BODY, "cursor")])
def test_pr_body_marker_names_the_author_on_a_plain_issue_branch(body, reviewer):
    assert pr.reviewer(pull(body=body)) == reviewer


def test_naming_an_agent_in_prose_is_not_a_marker():
    assert pr.author(pull(body="Cursor and Claude Code can now build in parallel")) is None


@pytest.mark.parametrize(
    ("made", "reviewer"),
    [
        (commit("cursoragent", "KitheK"), "claude"),
        (commit("claude"), "cursor"),
        (commit("KitheK", "claude"), "cursor"),
    ],
)
def test_commit_authors_decide_when_branch_and_body_do_not(made, reviewer):
    assert pr.reviewer(pull(commits=[made])) == reviewer


def test_the_agent_with_most_commits_is_the_author():
    commits = [commit("cursoragent"), commit("cursoragent"), commit("claude")]
    assert pr.author(pull(commits=commits)) == "cursor"


def test_builder_branch_wins_over_commits():
    assert pr.author(pull(head="claude/issue-E2-3", commits=[commit("cursoragent")])) == "claude"


def test_body_marker_wins_over_commits():
    assert pr.author(pull(body=CURSOR_BODY, commits=[commit("claude")])) == "cursor"


def test_both_body_markers_fall_back_to_commits():
    both = CURSOR_BODY + CLAUDE_BODY
    assert pr.author(pull(body=both, commits=[commit("claude")])) == "claude"


@pytest.mark.parametrize(
    "commits", [[], [commit("KitheK")], [commit("claude"), commit("cursoragent")]]
)
def test_human_or_evenly_mixed_pr_has_no_agent_author_and_gets_the_default_reviewer(commits):
    assert pr.author(pull(commits=commits)) is None
    assert pr.reviewer(pull(commits=commits)) == pr.DEFAULT_REVIEWER == "claude"


def test_missing_body_is_handled():
    assert pr.reviewer(pull(body=None)) == "claude"


def test_command_prints_only_the_reviewer_on_stdout(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pull(head="claude/issue-E2-3"))))
    assert pr.main() == 0
    assert capsys.readouterr().out == "cursor\n"
