"""Every folder an agent issue may write to must have an AGENTS.md guide."""

from pathlib import Path

from tools import issue_map as im

ROOT = Path(__file__).resolve().parents[2]
GUIDED_ROOTS = ("src/medici/", "web/src/", "templates/", "migrations/")


def guided_dirs():
    for i in im.load(im.DEFAULT_MAP)["issues"]:
        if i["owner"] == "human":
            continue
        for pattern in i["files_allowed"]:
            if pattern.endswith("/**") and pattern.startswith(GUIDED_ROOTS):
                yield i["id"], pattern[:-3]


def test_every_writable_area_has_a_guide():
    missing = [(iid, d) for iid, d in guided_dirs() if not (ROOT / d / "AGENTS.md").is_file()]
    assert missing == []


def test_guides_name_their_issue():
    for iid, d in guided_dirs():
        text = (ROOT / d / "AGENTS.md").read_text()
        assert iid in text, (iid, d)
