"""Public fetch API."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from medici.fetch.allowlist import assert_allowed
from medici.fetch.html import html_to_markdown
from medici.fetch.ratelimit import RateLimiter
from medici.fetch.robots import USER_AGENT, RobotsCache


@dataclass(frozen=True)
class Page:
    markdown: str
    url: str
    fetched_at: float


@dataclass(frozen=True)
class Skipped:
    reason: Literal["robots"]
    url: str


class Fetcher:
    def __init__(
        self,
        *,
        company_hosts: frozenset[str] = frozenset(),
        clock=None,
        sleep=None,
        urlopen_fn=None,
    ) -> None:
        self._company_hosts = company_hosts
        self._limiter = RateLimiter(clock=clock, sleep=sleep)
        self._robots = RobotsCache()
        self._urlopen = urlopen if urlopen_fn is None else urlopen_fn

    def get(self, url: str) -> Page | Skipped:
        """Fetch a URL when allowed, or return Skipped when robots rules block it."""
        assert_allowed(url, company_hosts=self._company_hosts)
        if not self._robots.can_fetch(url, urlopen_fn=self._urlopen):
            return Skipped(reason="robots", url=url)
        host = urlparse(url).netloc
        self._limiter.wait(host)
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with self._urlopen(req, timeout=30) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            html = resp.read().decode(charset, errors="replace")
            final_url = resp.geturl()
        return Page(
            markdown=html_to_markdown(html),
            url=final_url,
            fetched_at=time.time(),
        )