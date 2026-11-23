import copy
import json

from tools import check_files_allowed as cfa
from tools import issue_map as im


def issue(iid, deps=(), status="todo", passes=False, owner="claude-code", acceptance=None):
    return {
        "id": iid, "title": iid, "epic": iid.split("-")[0], "depends_on": list(deps),
        "owner": owner, "labels": [], "files_allowed": ["src/**"],
        "acceptance": acceptance or ["$ python -c 'pass'"],
        "status": status, "passes": passes, "notes": "",
    }


def mapof(*issues):
    return {"version": 1, "issues": list(issues)}


def write(tmp_path, data):
    p = tmp_path / "issue_map.json"
    p.write_text(json.dumps(data))
    return p


# --- picker -----------------------------------------------------------------

def test_picker_returns_first_ready_issue():
    data = mapof(
        issue("H0-1", status="done", passes=True),
        issue("E2-1", deps=["H0-1"]),
        issue("E2-2", deps=["E2-1"]),
    )
    assert [i["id"] for i in im.ready(data)] == ["E2-1"]


def test_picker_skips_dependency_that_is_done_but_not_passing():
    data = mapof(issue("H0-1", status="done", passes=False), issue("E2-1", deps=["H0-1"]))
    assert im.ready(data) == []


def test_picker_ignores_in_progress_and_filters_by_owner():
    data = mapof(
        issue("E2-1", status="in_progress"),
        issue("E2-2", owner="cursor"),
        issue("E2-3"),
    )
    assert [i["id"] for i in im.ready(data)] == ["E2-2", "E2-3"]
    assert [i["id"] for i in im.ready(data, owner="cursor")] == ["E2-2"]


# --- validator --------------------------------------------------------------

def test_validator_accepts_good_map():
    assert im.validate(mapof(issue("H0-1"), issue("E2-1", deps=["H0-1"]))) == []


def test_validator_rejects_duplicate_ids():
    problems = im.validate(mapof(issue("H0-1"), issue("H0-1")))
    assert any("duplicate" in p for p in problems)


def test_validator_rejects_cycles():
    problems = im.validate(mapof(issue("E2-1", deps=["E2-2"]), issue("E2-2", deps=["E2-1"])))
    assert any("cycle" in p for p in problems)


def test_validator_rejects_self_dependency_and_unknown_dependency():
    problems = im.validate(mapof(issue("E2-1", deps=["E2-1", "E9-9"])))
    assert any("itself" in p for p in problems)
    assert any("unknown" in p for p in problems)


def test_validator_rejects_passes_without_done():
    problems = im.validate(mapof(issue("E2-1", passes=True, status="todo")))
    assert any("passes" in p for p in problems)


def test_validator_rejects_missing_field_and_empty_files_allowed():
    bad = issue("E2-1")
    del bad["notes"]
    bad["files_allowed"] = []
    problems = im.validate(mapof(bad))
    assert any("missing field" in p for p in problems)
    assert any("files_allowed" in p for p in problems)


def test_real_issue_map_is_valid_and_complete():
    data = im.load(im.DEFAULT_MAP)
    assert im.validate(data) == []
    assert len(data["issues"]) == 37
    index = im.by_id(data)
    for i in data["issues"]:
        if i["owner"] != "human":
            assert im.command_checks(i), i["id"]
        if i["owner"] != "human" and i["epic"] != "H0":
            assert {"H0-2", "H0-3"} <= set(i["depends_on"]), i["id"]
    assert index["E2-3"]["depends_on"][:2] == ["H0-4", "E1-2"]


# --- completion script ------------------------------------------------------

def test_complete_sets_passes_when_checks_pass(tmp_path):
    p = write(tmp_path, mapof(issue("E2-1")))
    assert im.complete(p, "E2-1") == 0
    got = im.by_id(im.load(p))["E2-1"]
    assert got["passes"] is True and got["status"] == "done"


def test_complete_refuses_passes_when_tests_fail(tmp_path):
    failing = issue("E2-1", acceptance=["$ python -c 'raise SystemExit(1)'"])
    p = write(tmp_path, mapof(failing))
    before = p.read_text()
    assert im.complete(p, "E2-1") == 1
    assert p.read_text() == before
    assert im.by_id(im.load(p))["E2-1"]["passes"] is False


def test_prose_that_starts_with_a_command_word_is_not_run(tmp_path):
    prose = issue("E2-1", acceptance=["make ci runs lint and tests", "$ python -c 'pass'"])
    assert len(im.command_checks(prose)) == 1


def test_complete_refuses_issue_with_no_command_check(tmp_path):
    p = write(tmp_path, mapof(issue("E2-1", acceptance=["looks fine to me"])))
    assert im.complete(p, "E2-1") == 2
    assert im.by_id(im.load(p))["E2-1"]["passes"] is False


def test_complete_refuses_human_issues_and_unknown_ids(tmp_path):
    p = write(tmp_path, mapof(issue("E0-1", owner="human")))
    assert im.complete(p, "E0-1") == 2
    assert im.complete(p, "E9-9") == 2


def test_complete_refuses_invalid_map(tmp_path):
    data = mapof(issue("E2-1"), copy.deepcopy(issue("E2-1")))
    p = write(tmp_path, data)
    assert im.complete(p, "E2-1") == 2


# --- files_allowed diff check -----------------------------------------------

def test_files_allowed_glob_matching():
    allowed = ["src/fetch/**", "tests/fetch/**"]
    assert cfa.disallowed(["src/fetch/a.py", "src/fetch/x/y.py", "issue_map.json"], allowed) == []
    stray = ["src/other.py", "src/fetch.py"]
    assert cfa.disallowed(stray, allowed) == stray
