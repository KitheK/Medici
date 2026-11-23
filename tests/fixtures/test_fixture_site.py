import json
import re
import urllib.request
from pathlib import Path
from urllib.robotparser import RobotFileParser

import pytest

from fixtures.serve import SITE, start_in_thread

pytestmark = pytest.mark.integration

NAMES = json.loads((Path(__file__).parents[2] / "fixtures" / "names.json").read_text())


@pytest.fixture(scope="module")
def base():
    server, url = start_in_thread()
    yield url
    server.shutdown()


def get(url):
    with urllib.request.urlopen(url) as r:
        return r.read().decode()


@pytest.mark.parametrize("path", ["/team/", "/careers/", "/about/", "/blog/"])
def test_core_pages_are_served(base, path):
    assert "<h1>" in get(base + path)


def test_robots_blocks_exactly_one_path(base):
    rp = RobotFileParser()
    rp.parse(get(base + "/robots.txt").splitlines())
    assert rp.can_fetch("*", base + "/team/")
    assert not rp.can_fetch("*", base + "/private/")


def test_team_page_has_recruiter_and_team_members(base):
    text = get(base + "/team/")
    assert "Technical Recruiter" in text
    assert text.count("<h2>") >= 10  # enough people to exercise the 3-person cap


def test_injected_page_contains_instructions_aimed_at_the_agent(base):
    text = get(base + "/careers/injected.html")
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in text


def _all_pages():
    return [p for p in SITE.rglob("*.html")]


def test_every_person_name_is_invented():
    allowed = set(NAMES["people"])
    found = set()
    for page in _all_pages():
        html = page.read_text()
        found |= set(re.findall(r"<li><h2>([^<]+)</h2>", html))  # team lists
        found |= set(re.findall(r"By ([A-Z][a-z]+ [A-Z][a-z-]+)\.", html))  # blog bylines
        found |= set(re.findall(r"led by ([A-Z][a-z]+ [A-Z][a-z-]+)\.", html))
        found |= set(re.findall(r"contact: ([A-Z][a-z]+ [A-Z][a-z-]+)\.", html, re.I))
        found |= set(re.findall(r"CEO, ([A-Z][a-z]+ [A-Z][a-z-]+),", html))
    assert found
    assert found <= allowed, found - allowed


def test_every_email_uses_a_reserved_test_domain():
    domains = set(NAMES["allowed_email_domains"])
    for page in _all_pages():
        for email in re.findall(r"[\w.+-]+@([\w.-]+)", page.read_text()):
            assert email.rstrip(".") in domains, (page, email)
