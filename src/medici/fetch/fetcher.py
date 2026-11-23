"""Public fetch API."""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from medici.fetch.allowlist import assert_allowed
from medici.fetch.html import html_to_markdown
from medici.fetch.ratelimit import RateLimiter
from medici.fetch.robots import USER_AGENT, RobotsCache

MAX_REDIRECT_HOPS = 3
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_REDIRECT_CODES = frozenset({301, 302, 303, 307, 308})


class ResponseTooLarge(Exception):
    """Raised when a response body exceeds the configured cap."""


class TooManyRedirects(Exception):
    """Raised when a redirect chain exceeds the hop limit."""


@dataclass(frozen=True)
class Page:
    markdown: str
    url: str
    fetched_at: float


@dataclass(frozen=True)
class Skipped:
    reason: Literal["robots"]
    url: str


@lru_cache(maxsize=1)
def _no_redirect_opener():
    class _NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
            return None

    return build_opener(_NoRedirect)


def _read_limited(resp, limit: int = MAX_RESPONSE_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = resp.read(min(65536, limit - total + 1))
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise ResponseTooLarge(limit)
        chunks.append(chunk)
    return b"".join(chunks)


class Fetcher:
    def __init__(
        self,
        *,
        company_hosts: frozenset[str] = frozenset(),
        allow_fixture_hosts: bool = False,
        clock=None,
        sleep=None,
        urlopen_fn=None,
    ) -> None:
        self._company_hosts = company_hosts
        self._allow_fixture_hosts = allow_fixture_hosts
        self._limiter = RateLimiter(clock=clock, sleep=sleep)
        self._robots = RobotsCache()
        self._use_default_urlopen = urlopen_fn is None
        self._urlopen = urlopen if urlopen_fn is None else urlopen_fn

    def _open(self, req: Request, timeout: int = 30):
        if self._use_default_urlopen:
            return _no_redirect_opener().open(req, timeout=timeout)
        return self._urlopen(req, timeout=timeout)

    def get(self, url: str) -> Page | Skipped:
        """Fetch a URL when allowed, or return Skipped when robots rules block it."""
        current = url
        for hop in range(MAX_REDIRECT_HOPS + 1):
            assert_allowed(
                current,
                company_hosts=self._company_hosts,
                allow_fixture_hosts=self._allow_fixture_hosts,
            )
            if not self._robots.can_fetch(current, urlopen_fn=self._urlopen):
                return Skipped(reason="robots", url=current)
            host = urlparse(current).netloc
            self._limiter.wait(host)
            req = Request(current, headers={"User-Agent": USER_AGENT})
            try:
                resp = self._open(req)
            except HTTPError as err:
                if err.code not in _REDIRECT_CODES:
                    raise
                if hop >= MAX_REDIRECT_HOPS:
                    raise TooManyRedirects(current) from err
                location = err.headers.get("Location")
                if not location:
                    raise
                current = urljoin(err.geturl() or current, location)
                continue
            with resp:
                final_url = resp.geturl()
                charset = resp.headers.get_content_charset() or "utf-8"
                html = _read_limited(resp).decode(charset, errors="replace")
            return Page(
                markdown=html_to_markdown(html),
                url=final_url,
                fetched_at=time.time(),
            )
        raise TooManyRedirects(url)