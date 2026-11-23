from tools import queue as q


def issue(iid, owner="claude-code", deps=(), status="todo", passes=False):
    return {
        "id": iid, "title": iid, "epic": iid.split("-")[0], "depends_on": list(deps),
        "owner": owner, "labels": [], "files_allowed": ["x/**"], "acceptance": ["$ true"],
        "status": status, "passes": passes, "notes": "",
    }


def data(*issues):
    return {"version": 1, "issues": list(issues)}


def test_each_builder_gets_its_own_issue_at_the_same_time():
    d = data(issue("E2-1"), issue("E5-5", owner="cursor"), issue("E2-2"))
    assert q.pick(d, "claude-code") == "E2-1"
    assert q.pick(d, "cursor") == "E5-5"


def test_lane_never_takes_another_builders_issue():
    d = data(issue("E5-5", owner="cursor"))
    assert q.pick(d, "claude-code") is None


def test_busy_issue_is_skipped_and_wip_limit_holds():
    d = data(issue("E2-1"), issue("E2-2"))
    assert q.pick(d, "claude-code", busy={"E2-1"}, wip=2) == "E2-2"
    assert q.pick(d, "claude-code", busy={"E2-1"}, wip=1) is None


def test_busy_issue_of_the_other_lane_does_not_use_up_this_lanes_wip():
    d = data(issue("E2-1"), issue("E5-5", owner="cursor"))
    assert q.pick(d, "claude-code", busy={"E5-5"}, wip=1) == "E2-1"


def test_unmet_dependencies_block_the_pick():
    d = data(issue("E2-1"), issue("E2-2", deps=["E2-1"]))
    assert q.pick(d, "claude-code", busy={"E2-1"}, wip=2) is None


def test_forced_issue_must_still_be_ready():
    d = data(issue("E2-1"), issue("E2-2", deps=["E2-1"]))
    assert q.pick(d, "claude-code", force="E2-1") == "E2-1"
    assert q.pick(d, "claude-code", force="E2-2") is None


def test_real_queue_offers_no_product_issue_until_the_human_gates_pass():
    from tools import issue_map as im

    real = im.load(im.DEFAULT_MAP)
    gates = {"E0-1", "E1-1", "E1-2"}
    if not all(im.by_id(real)[g]["passes"] for g in gates):
        for owner in q.BUILDERS:
            picked = q.pick(real, owner)
            assert picked is None or picked.startswith(("H0", "H1"))
