"""robots.txt checks, cached per host."""

from __future__ import annotations

import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

USER_AGENT = "Medici/0.0.1 (respects robots.txt; job-posting research helper)"

_CACHE_TTL = 3600.0
_DISALLOW_ALL = ["User-agent: *", "Disallow: /"]


class RobotsCache:
    def __init__(self) -> None:
        self._parsers: dict[str, RobotFileParser] = {}
        self._loaded_at: dict[str, float] = {}

    def can_fetch(self, url: str, *, urlopen_fn=urlopen) -> bool:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        host = parsed.netloc
        parser = self._parser_for(host, parsed, urlopen_fn=urlopen_fn)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        return parser.can_fetch(USER_AGENT, urljoin(f"{parsed.scheme}://{host}", path))

    def _parser_for(
        self, host: str, parsed, *, urlopen_fn
    ) -> RobotFileParser:
        now = time.time()
        if host in self._parsers and now - self._loaded_at.get(host, 0) < _CACHE_TTL:
            return self._parsers[host]
        rp = RobotFileParser()
        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        try:
            req = Request(robots_url, headers={"User-Agent": USER_AGENT})
            with urlopen_fn(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            rp.parse(body.splitlines())
        except HTTPError as err:
            if 400 <= err.code < 500:
                rp.parse([])
            else:
                rp.parse(_DISALLOW_ALL)
        except (OSError, URLError):
            rp.parse(_DISALLOW_ALL)
        self._parsers[host] = rp
        self._loaded_at[host] = now
        return rp