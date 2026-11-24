import json
import subprocess

import pytest

from tools import conflict_fix as cf


def git(repo, *args):
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def write(repo, files):
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def save(repo, files, message="change"):
    write(repo, files)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def make(tmp_path):
    """Build a repo whose head and base branches both changed the given files."""

    def build(base, head, start):
        repo = tmp_path / "repo"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "base")
        git(repo, "config", "user.name", "Test Bot")
        git(repo, "config", "user.email", "bot@example.test")
        git(repo, "config", "core.autocrlf", "false")
        save(repo, start)
        git(repo, "switch", "-q", "-c", "head")
        head_sha = save(repo, head)
        git(repo, "switch", "-q", "base")
        base_sha = save(repo, base)
        return repo, head_sha, base_sha

    return build


def issues(**passes):
    return json.dumps(
        {"issues": [{"id": k, "passes": v, "files_allowed": ["x/**"]} for k, v in passes.items()]}
    )


# --- planning ---------------------------------------------------------------


@pytest.mark.integration
def test_plan_lists_the_conflicted_files(make):
    repo, head, base = make({"a.txt": "base\n"}, {"a.txt": "head\n"}, {"a.txt": "start\n"})
    assert cf.plan(repo, head, base) == {
        "status": "conflicts", "files": ["a.txt"], "auto": [], "reason": "",
    }


@pytest.mark.integration
def test_the_progress_log_keeps_both_sides_without_an_agent(make, tmp_path):
    start = "# Log\n\n## One\n\n- first\n"
    repo, head, base = make(
        {"progress.md": start + "\n## Two\n\n- from base\n- Next: x\n"},
        {"progress.md": start + "\n## Three\n\n- from head\n- Next: x\n"},
        {"progress.md": start},
    )
    planned = cf.plan(repo, head, base)
    assert (planned["status"], planned["files"], planned["auto"]) == (
        "conflicts", [], ["progress.md"],
    )
    out = tmp_path / "out"
    out.mkdir()
    cf.apply(repo, head, base, out)
    assert (repo / "progress.md").read_text(encoding="utf-8") == (
        start + "\n## Two\n\n- from base\n- Next: x\n" + "\n## Three\n\n- from head\n- Next: x\n"
    )


def test_log_entry_edited_on_one_side_keeps_the_edit():
    old, new = "# Log\n\n## One\n\n- a\n", "# Log\n\n## One\n\n- b\n"
    added = "\n## Two\n\n- c\n"
    assert cf.combine_log(base=new, start=old, head=old + added) == new + added
    assert cf.combine_log(base=old + added, start=old, head=new) == new + added


@pytest.mark.parametrize(
    ("base", "start", "head"),
    [
        ("## One\n\n- b\n", "## One\n\n- a\n", "## One\n\n- c\n"),  # edited differently
        ("## One\n\n- b\n", "", "## One\n\n- c\n"),  # added differently
        ("", "## One\n\n- a\n", "## One\n\n- b\n"),  # removed on one side
        ("## One\n\n- a\n\n## One\n\n- b\n", "", "## Two\n\n- c\n"),  # heading used twice
    ],
)
def test_log_entries_that_cannot_be_combined_safely_are_not_guessed(base, start, head):
    assert cf.combine_log(base=base, start=start, head=head) is None


@pytest.mark.integration
def test_a_log_that_cannot_be_combined_goes_to_the_agent(make):
    repo, head, base = make(
        {"progress.md": "## One\n\n- b\n"},
        {"progress.md": "## One\n\n- c\n"},
        {"progress.md": "## One\n\n- a\n"},
    )
    planned = cf.plan(repo, head, base)
    assert (planned["files"], planned["auto"]) == (["progress.md"], [])


@pytest.mark.integration
def test_plan_reports_a_clean_merge(make):
    repo, head, base = make({"a.txt": "base\n"}, {"b.txt": "head\n"}, {"a.txt": "start\n"})
    assert cf.plan(repo, head, base)["status"] == "clean"


@pytest.mark.integration
@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/ci.yml",
        ".claude/settings.json",
        ".cursor/cli.json",
        "tools/queue.py",
        "tests/privacy/test_x.py",
        "AGENTS.md",
        "src/medici/fetch/AGENTS.md",
        "CLAUDE.md",
        "pyproject.toml",
        "Makefile",
    ],
)
def test_plan_leaves_protected_files_to_a_human(make, path):
    repo, head, base = make({path: "base\n"}, {path: "head\n"}, {path: "start\n"})
    planned = cf.plan(repo, head, base)
    assert planned["status"] == "human"
    assert path in planned["reason"]


@pytest.mark.integration
def test_plan_leaves_deleted_files_to_a_human(make):
    repo, head, base = make({"b.txt": "x\n"}, {"a.txt": "head\n"}, {"a.txt": "start\n"})
    git(repo, "rm", "-q", "a.txt")
    git(repo, "commit", "-q", "-m", "delete")
    planned = cf.plan(repo, head, git(repo, "rev-parse", "HEAD"))
    assert planned["status"] == "human"
    assert "a.txt" in planned["reason"]


@pytest.mark.integration
def test_plan_leaves_very_large_conflicts_to_a_human(make):
    names = [f"f{i}.txt" for i in range(cf.MAX_FILES + 1)]
    repo, head, base = make(*[{n: f"{side}\n" for n in names} for side in ("b", "h", "s")])
    assert cf.plan(repo, head, base)["status"] == "human"


# --- collecting and applying ------------------------------------------------


@pytest.mark.integration
def test_collect_then_apply_produces_a_merge_with_only_the_resolved_file(make, tmp_path):
    repo, head, base = make({"a.txt": "base\n"}, {"a.txt": "head\n"}, {"a.txt": "start\n"})
    files = cf.plan(repo, head, base)["files"]
    write(repo, {"a.txt": "head and base\n", "stray.txt": "not asked for\n"})
    out = tmp_path / "out"
    cf.collect(repo, files, out)
    git(repo, "reset", "-q", "--hard")
    git(repo, "clean", "-fdq")

    cf.apply(repo, head, base, out)
    git(repo, "commit", "-q", "-m", "merge")

    assert (repo / "a.txt").read_text(encoding="utf-8") == "head and base\n"
    assert not (repo / "stray.txt").exists()
    assert git(repo, "rev-list", "--parents", "-n1", "HEAD").split()[1:] == [head, base]


@pytest.mark.integration
def test_collect_rejects_leftover_conflict_markers(make, tmp_path):
    repo, head, base = make({"a.txt": "base\n"}, {"a.txt": "head\n"}, {"a.txt": "start\n"})
    files = cf.plan(repo, head, base)["files"]
    with pytest.raises(cf.Rejected, match="conflict marker"):
        cf.collect(repo, files, tmp_path / "out")


@pytest.mark.integration
def test_apply_rejects_files_that_were_not_in_conflict(make, tmp_path):
    repo, head, base = make({"a.txt": "base\n"}, {"a.txt": "head\n"}, {"a.txt": "start\n"})
    out = tmp_path / "out"
    write(out, {"a.txt": "ok\n", ".github/workflows/ci.yml": "evil\n"})
    with pytest.raises(cf.Rejected, match="not exactly"):
        cf.apply(repo, head, base, out)


@pytest.mark.integration
def test_apply_rejects_an_issue_marked_passing_by_neither_side(make, tmp_path):
    name = "issue_map.json"
    repo, head, base = make(
        {name: issues(A=False, B=True)},
        {name: issues(A=False, C=True)},
        {name: issues(A=False)},
    )
    out = tmp_path / "out"
    write(out, {name: issues(A=True, B=True, C=True)})
    with pytest.raises(cf.Rejected, match="A.*passes"):
        cf.apply(repo, head, base, out)


@pytest.mark.integration
def test_apply_accepts_an_issue_map_that_keeps_both_sides(make, tmp_path):
    name = "issue_map.json"
    repo, head, base = make(
        {name: issues(A=False, B=True)},
        {name: issues(A=False, C=True)},
        {name: issues(A=False)},
    )
    out = tmp_path / "out"
    write(out, {name: issues(A=False, B=True, C=True)})
    cf.apply(repo, head, base, out)
    assert git(repo, "diff", "--name-only", "--diff-filter=U") == ""


# --- content checks ---------------------------------------------------------


def test_invalid_json_is_rejected():
    with pytest.raises(cf.Rejected, match="JSON"):
        cf.check_text("data.json", "{oops")


@pytest.mark.parametrize("prefix", ["sk-ant-", "ghp_", "ghs_", "github_pat_"])
def test_text_that_looks_like_a_secret_is_rejected(prefix):
    with pytest.raises(cf.Rejected, match="secret"):
        cf.check_text("a.txt", "x = " + prefix + "a1B2c3D4e5F6g7H8i9J0k1L2")


def test_a_plain_row_of_equals_signs_is_not_a_marker():
    cf.check_text("README.md", "Title\n=======\n")


# --- comment ----------------------------------------------------------------


def comment(**kw):
    base = {
        "outcome": "fixed", "fixer": "cursor", "files": ["a.txt"], "notes": "Kept both lines.",
        "auto": [], "commit": "abc1234", "ci_starts": True, "reason": "",
    }
    return cf.comment(**(base | kw))


def test_comment_says_what_was_fixed_by_whom_and_where():
    text = comment()
    for part in ("Cursor", "`a.txt`", "Kept both lines.", "abc1234"):
        assert part in text


def test_comment_separates_automatic_merges_from_agent_fixes():
    text = comment(files=[], auto=["progress.md"], notes="")
    assert "`progress.md`" in text
    assert "kept both sides" in text
    assert "Cursor" not in text  # no agent ran, so none is credited
    assert "did not leave notes" not in text


def test_comment_warns_when_checks_will_not_start_by_themselves():
    assert "GH_PAT" in comment(ci_starts=False)
    assert "GH_PAT" not in comment(ci_starts=True)


def test_comment_for_a_failure_gives_the_reason_and_claims_no_fix():
    text = comment(outcome="human", reason="AGENTS.md is protected", commit="")
    assert "AGENTS.md is protected" in text
    assert "Nothing was pushed" in text
    assert "Fixed" not in text


def test_comment_for_a_clean_pr_says_there_was_nothing_to_fix():
    assert "no merge conflicts" in comment(outcome="clean", files=[], commit="").lower()


def test_agent_notes_cannot_mention_people_or_hide_content():
    text = comment(notes="ping @someone <!-- hidden --> <img src=x>")
    assert "@someone" not in text
    assert "<!--" not in text
    assert "<img" not in text


def test_agent_notes_are_cut_short_and_secrets_are_dropped():
    assert len(comment(notes="x" * 50_000)) < 8_000
    assert "ghp_" not in comment(notes="token ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2")


def test_missing_notes_are_stated_plainly():
    assert "did not leave notes" in comment(notes="")
