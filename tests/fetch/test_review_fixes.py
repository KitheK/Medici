"""Review-hardening tests for E2-3 (add before each fix)."""

from __future__ import annotations

from email.message import EmailMessage
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from fixtures.serve import start_in_thread
from medici.fetch.allowlist import NotAllowed, assert_allowed
from medici.fetch.fetcher import Fetcher, Page, ResponseTooLarge, Skipped
from medici.fetch.html import html_to_markdown


def _html_response(body: bytes, *, url: str) -> object:
    class R:
        def __init__(self) -> None:
            self._buf = BytesIO(body)

        def read(self, n: int = -1) -> bytes:
            return self._buf.read(n)

        def geturl(self) -> str:
            return url

        @property
        def headers(self) -> EmailMessage:
            msg = EmailMessage()
            msg["content-type"] = "text/html; charset=utf-8"
            return msg

        def __enter__(self):
            return self

        def __exit__(self, *args):  # noqa: ARG001
            pass

    return R()


def test_localhost_not_allowed_without_fixture_flag():
    with pytest.raises(NotAllowed):
        assert_allowed("http://127.0.0.1/team/", allow_fixture_hosts=False)


@pytest.fixture(scope="module")
def fixture_base():
    server, url = start_in_thread()
    yield url
    server.shutdown()


def test_fixture_fetcher_requires_fixture_flag(fixture_base):
    with pytest.raises(NotAllowed):
        Fetcher().get(fixture_base + "/team/")


def test_void_br_inside_hidden_does_not_drop_following_content():
    html = "<div hidden>secret<br>more</div><p>After hidden</p>"
    md = html_to_markdown(html)
    assert "After hidden" in md
    assert "secret" not in md


def test_redirect_revalidates_allowlist_on_each_hop():
    seen: list[str] = []

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        seen.append(req.full_url)
        if req.full_url.endswith("/robots.txt"):
            return _html_response(b"User-agent: *\nAllow: /", url=req.full_url)
        if req.full_url == "https://door.example.test/entry":
            raise HTTPError(
                req.full_url,
                302,
                "Found",
                {"Location": "https://evil.example/loot"},
                None,
            )
        raise AssertionError(f"unexpected fetch {req.full_url}")

    fetcher = Fetcher(urlopen_fn=fake_urlopen)
    with pytest.raises(NotAllowed):
        fetcher.get("https://door.example.test/entry")
    assert not any("evil.example" in u for u in seen)


def test_redirect_hop_rate_limit_applied_per_host():
    hosts_waited: list[str] = []
    clock = [0.0]

    def fake_clock() -> float:
        return clock[0]

    def fake_sleep(seconds: float) -> None:
        clock[0] += seconds

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        if req.full_url.endswith("/robots.txt"):
            return _html_response(b"User-agent: *\nAllow: /", url=req.full_url)
        if req.full_url == "https://a.example.test/start":
            raise HTTPError(
                req.full_url,
                302,
                "Found",
                {"Location": "https://b.example.test/landing"},
                None,
            )
        if req.full_url == "https://b.example.test/landing":
            return _html_response(b"<html><body><p>done</p></body></html>", url=req.full_url)
        raise AssertionError(req.full_url)

    original_wait = None

    def tracking_wait(self, host: str) -> None:  # type: ignore[no-untyped-def]
        hosts_waited.append(host)
        original_wait(self, host)

    from medici.fetch import ratelimit

    original_wait = ratelimit.RateLimiter.wait
    ratelimit.RateLimiter.wait = tracking_wait  # type: ignore[method-assign]
    try:
        fetcher = Fetcher(urlopen_fn=fake_urlopen, clock=fake_clock, sleep=fake_sleep)
        result = fetcher.get("https://a.example.test/start")
    finally:
        ratelimit.RateLimiter.wait = original_wait

    assert isinstance(result, Page)
    assert "a.example.test" in hosts_waited and "b.example.test" in hosts_waited


def test_robots_txt_5xx_disallows_fetch():
    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        if req.full_url.endswith("/robots.txt"):
            raise HTTPError(req.full_url, 503, "unavailable", {}, None)
        raise AssertionError("page should not be fetched")

    fetcher = Fetcher(
        company_hosts=frozenset({"busy.example.test"}),
        urlopen_fn=fake_urlopen,
    )
    result = fetcher.get("https://busy.example.test/page")
    assert isinstance(result, Skipped)


def test_robots_txt_404_allows_fetch():
    page_hits: list[str] = []

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        if req.full_url.endswith("/robots.txt"):
            raise HTTPError(req.full_url, 404, "missing", {}, None)
        page_hits.append(req.full_url)
        return _html_response(b"<html><body><h1>OK</h1></body></html>", url=req.full_url)

    fetcher = Fetcher(urlopen_fn=fake_urlopen)
    result = fetcher.get("https://open.example.test/welcome")
    assert isinstance(result, Page)
    assert page_hits == ["https://open.example.test/welcome"]


def test_robots_txt_network_error_disallows_fetch():
    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        if req.full_url.endswith("/robots.txt"):
            raise URLError("timeout")
        raise AssertionError("page should not be fetched")

    fetcher = Fetcher(urlopen_fn=fake_urlopen)
    result = fetcher.get("https://down.example.test/page")
    assert isinstance(result, Skipped)


def test_response_body_capped_at_two_megabytes():
    huge = b"x" * (2 * 1024 * 1024 + 1)

    def fake_urlopen(req, timeout=0):  # noqa: ARG001
        if req.full_url.endswith("/robots.txt"):
            return _html_response(b"User-agent: *\nAllow: /", url=req.full_url)
        return _html_response(huge, url=req.full_url)

    fetcher = Fetcher(urlopen_fn=fake_urlopen)
    with pytest.raises(ResponseTooLarge):
        fetcher.get("https://big.example.test/huge")