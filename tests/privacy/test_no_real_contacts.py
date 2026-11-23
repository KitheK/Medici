"""Repo-wide scan: no real-looking email addresses may be committed."""

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.privacy

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_DOMAINS = (
    "example.test",
    "example.invalid",
    "example.com",
    "users.noreply.github.com",
    "anthropic.com",
)
EMAIL = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
TEXT_SUFFIXES = {".md", ".py", ".json", ".html", ".yml", ".yaml", ".txt", ".sh", ".mdc"}


def tracked_text_files():
    names = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    for name in names.splitlines():
        path = ROOT / name
        if path.suffix in TEXT_SUFFIXES and path.is_file():
            yield path


def test_only_reserved_or_noreply_domains_appear():
    bad = []
    for path in tracked_text_files():
        for domain in EMAIL.findall(path.read_text(errors="ignore")):
            d = domain.lower().rstrip(".")
            if not d.endswith(ALLOWED_DOMAINS):
                bad.append((path.name, d))
    assert bad == []
