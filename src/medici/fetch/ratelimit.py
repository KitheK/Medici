"""Per-host request rate limiting (1 request per second)."""

from __future__ import annotations

import time
from collections.abc import Callable

DEFAULT_INTERVAL = 1.0


class RateLimiter:
    def __init__(
        self,
        *,
        interval: float = DEFAULT_INTERVAL,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self._interval = interval
        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep
        self._last: dict[str, float] = {}

    def wait(self, host: str) -> None:
        """Block until another request to this host is allowed."""
        now = self._clock()
        prev = self._last.get(host)
        if prev is not None:
            delay = self._interval - (now - prev)
            if delay > 0:
                self._sleep(delay)
                now = self._clock()
        self._last[host] = now