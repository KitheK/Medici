from tools import post_feedback as pf

DIFF = """diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -1,3 +1,5 @@
 import os
+import sys
+import json
 x = 1
-y = 2
+y = 3
diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1,1 +0,0 @@
-gone = 1
"""


def comment(**kw):
    return {"path": "src/a.py", "line": 2, "category": "design", "severity": "consider",
            "body": "why", **kw}


def test_commentable_lines_cover_added_and_context_lines_only():
    lines = pf.commentable_lines(DIFF)
    assert lines["src/a.py"] == {1, 2, 3, 4, 5}
    assert "old.py" not in lines  # deleted files cannot be commented on the new side


def test_comment_on_a_changed_line_becomes_inline_with_a_suggestion_block():
    r = pf.build_review({"comments": [comment(suggestion="import sys  # used below")]}, DIFF)
    assert len(r["comments"]) == 1
    body = r["comments"][0]["body"]
    assert "```suggestion\nimport sys  # used below\n```" in body
    assert r["comments"][0]["line"] == 2 and r["comments"][0]["side"] == "RIGHT"


def test_comment_outside_the_diff_moves_to_the_review_body():
    r = pf.build_review({"comments": [comment(line=99)]}, DIFF)
    assert r["comments"] == []
    assert "More notes" in r["body"] and "src/a.py:99" in r["body"]


def test_unknown_file_is_not_anchored():
    r = pf.build_review({"comments": [comment(path="nope.py")]}, DIFF)
    assert r["comments"] == [] and "nope.py:2" in r["body"]


def test_multi_line_suggestion_needs_every_line_in_the_diff():
    ok = pf.build_review({"comments": [comment(start_line=2, line=3, suggestion="a\nb")]}, DIFF)
    assert ok["comments"][0]["start_line"] == 2
    bad = pf.build_review({"comments": [comment(start_line=3, line=9)]}, DIFF)
    assert bad["comments"] == []


def test_mentions_and_hidden_html_are_neutralised():
    r = pf.build_review({"summary": "ping @KitheK <!-- secret -->", "comments": [
        comment(body="thanks @someone")]}, DIFF)
    assert "@KitheK" not in r["body"] and "secret" not in r["body"]
    assert "@someone" not in r["comments"][0]["body"]


def test_suggestion_containing_backticks_gets_a_longer_fence():
    r = pf.build_review({"comments": [comment(suggestion="x = '''```'''")]}, DIFF)
    assert "````suggestion" in r["comments"][0]["body"]


def test_inline_comments_are_capped_and_most_important_first():
    many = [comment(severity="learn", body=f"n{i}") for i in range(30)]
    many.append(comment(severity="fix", body="important"))
    r = pf.build_review({"comments": many}, DIFF)
    assert len(r["comments"]) == pf.MAX_INLINE
    assert "important" in r["comments"][0]["body"]


def test_bad_enum_values_fall_back_and_junk_entries_are_dropped():
    r = pf.build_review({"comments": [comment(severity="BLOCKER", category="vibes"),
                                      {"nonsense": True}, comment(line="2")]}, DIFF)
    assert len(r["comments"]) == 1
    assert r["comments"][0]["body"].startswith("**consider · design**")


def test_body_has_learning_sections_marker_and_advisory_footer():
    r = pf.build_review({
        "summary": "Adds a thing.", "purpose_check": {"verdict": "matches", "notes": "ok"},
        "strengths": ["small functions"],
        "alternatives": [{"title": "Use a queue", "idea": "decouple", "tradeoffs": "more code"}],
        "concepts": [{"name": "Single responsibility", "explanation": "one reason to change"}],
    }, DIFF)
    for needle in (pf.MARKER, "Does it do what it is for?", "Another way to think about it",
                   "Concepts worth learning", "never blocks a merge"):
        assert needle in r["body"]


def test_unusable_feedback_posts_nothing_and_does_not_fail(tmp_path, capsys):
    bad = tmp_path / "feedback.json"
    bad.write_text("not json")
    assert pf.main(["--repo", "o/r", "--pr", "1", "--feedback", str(bad)]) == 0
    assert "nothing posted" in capsys.readouterr().out
    assert pf.main(["--repo", "o/r", "--pr", "1", "--feedback", str(tmp_path / "missing")]) == 0
