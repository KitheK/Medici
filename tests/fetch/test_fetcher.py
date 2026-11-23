"""Tests for the fetch wrapper (issue E2-3)."""

from __future__ import annotations

import time
from urllib.error import HTTPError

import pytest

from fixtures.serve import start_in_thread
from medici.fetch.allowlist import NotAllowed, assert_allowed
from medici.fetch.fetcher import Fetcher, Page, Skipped
from medici.fetch.html import html_to_markdown
from medici.fetch.ratelimit import RateLimiter


@pytest.fixture(scope="module")
def fixture_base():
    server, url = start_in_thread()
    yield url
    server.shutdown()


def test_rejects_off_allowlist_host():
    fetcher = Fetcher()
    with pytest.raises(NotAllowed):
        fetcher.get("http://evil.example/")


def test_rejects_off_allowlist_before_request(monkeypatch):
    called = []

    def fake_urlopen(_req, timeout=0):  # noqa: ARG001
        called.append(1)
        raise AssertionError("network should not run")

    fetcher = Fetcher(urlopen_fn=fake_urlopen)
    with pytest.raises(NotAllowed):
        fetcher.get("https://not-in-allowlist.com/team/")
    assert not called


def test_skips_robots_blocked_path(fixture_base):
    fetcher = Fetcher()
    result = fetcher.get(fixture_base + "/private/")
    assert isinstance(result, Skipped)
    assert result.url.endswith("/private/")


def test_fetches_allowlisted_fixture_page(fixture_base):
    fetcher = Fetcher()
    result = fetcher.get(fixture_base + "/team/")
    assert isinstance(result, Page)
    assert "Marisol Quenby" in result.markdown
    assert "Technical Recruiter" in result.markdown
    assert result.fetched_at > 0


def test_hidden_injected_instructions_omitted_from_markdown(fixture_base):
    fetcher = Fetcher()
    result = fetcher.get(fixture_base + "/careers/injected.html")
    assert isinstance(result, Page)
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" not in result.markdown
    assert "Software Intern" in result.markdown


def test_html_to_markdown_drops_script_style_and_hidden():
    html = """
    <html><head><style>.x{color:red}</style>
    <script>alert(1)</script></head>
    <body>
    <h1>Visible</h1>
    <p style="display:none">Secret agent text</p>
    <p>Hello <strong>world</strong></p>
    </body></html>
    """
    md = html_to_markdown(html)
    assert "Visible" in md
    assert "Hello" in md and "world" in md
    assert "Secret agent text" not in md
    assert "alert" not in md


def test_rate_limit_one_request_per_second_per_host():
    clock = [0.0]
    slept: list[float] = []

    def fake_clock() -> float:
        return clock[0]

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        clock[0] += seconds

    limiter = RateLimiter(clock=fake_clock, sleep=fake_sleep)
    limiter.wait("a.example.test")
    limiter.wait("a.example.test")
    limiter.wait("b.example.test")
    assert slept == [1.0]
    assert clock[0] == 1.0


def test_fetcher_rate_limits_same_host(fixture_base, monkeypatch):
    calls: list[float] = []
    clock = [1000.0]

    def fake_monotonic() -> float:
        return clock[0]

    real_sleep = time.sleep

    def recording_sleep(seconds: float) -> None:
        calls.append(seconds)
        real_sleep(0)

    monkeypatch.setattr("medici.fetch.ratelimit.time.monotonic", fake_monotonic)
    fetcher = Fetcher(clock=fake_monotonic, sleep=recording_sleep)
    fetcher.get(fixture_base + "/about/")
    clock[0] += 0.2
    fetcher.get(fixture_base + "/team/")
    assert calls and calls[-1] >= 0.79


def test_localhost_in_allowlist(fixture_base):
    assert_allowed(fixture_base + "/team/")


def test_example_test_suffix_hosts_allowed():
    assert_allowed("https://brightloom.example.test/about/")
    with pytest.raises(NotAllowed):
        assert_allowed("https://brightloom.example.com/about/")


def test_extra_company_host_allowed():
    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        class R:
            def read(self):
                if req.full_url.endswith("/robots.txt"):
                    return b"User-agent: *\nAllow: /"
                return b"<html><body><h1>Acme</h1></body></html>"

            def geturl(self):
                return req.full_url

            @property
            def headers(self):
                from email.message import EmailMessage

                msg = EmailMessage()
                msg["content-type"] = "text/html; charset=utf-8"
                return msg

            def __enter__(self):
                return self

            def __exit__(self, *args):  # noqa: ARG001
                pass

        return R()

    fetcher = Fetcher(company_hosts=frozenset({"careers.acme.com"}), urlopen_fn=fake_urlopen)
    result = fetcher.get("https://careers.acme.com/jobs/")
    assert isinstance(result, Page)
    assert "Acme" in result.markdown


def test_page_records_final_url(fixture_base):
    fetcher = Fetcher()
    result = fetcher.get(fixture_base + "/team/")
    assert isinstance(result, Page)
    assert result.url == fixture_base + "/team/"


def test_robots_disallowed_does_not_hit_origin(fixture_base):
    fetches: list[str] = []

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        fetches.append(req.full_url)
        if req.full_url.endswith("/robots.txt"):
            body = b"User-agent: *\nDisallow: /private/\n"
        else:
            raise HTTPError(req.full_url, 404, "", {}, None)

        class R:
            def read(self):
                return body

            def __enter__(self):
                return self

            def __exit__(self, *args):  # noqa: ARG001
                pass

        return R()

    fetcher = Fetcher(urlopen_fn=fake_urlopen)
    result = fetcher.get(fixture_base + "/private/index.html")
    assert isinstance(result, Skipped)
    assert not any("/private/" in u for u in fetches)