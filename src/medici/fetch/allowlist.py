"""Host allowlist for outbound fetches."""

from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_SUFFIXES = (".example.test", ".example.invalid")
FIXTURE_HOSTS = frozenset({"127.0.0.1", "localhost"})


class NotAllowed(Exception):
    """Raised when a URL's host is not on the allowlist."""


def host_allowed(host: str, *, company_hosts: frozenset[str] = frozenset()) -> bool:
    """Return True when the host may be fetched."""
    name = host.lower().split(":", 1)[0]
    if name in FIXTURE_HOSTS or name in company_hosts:
        return True
    return any(name == sfx[1:] or name.endswith(sfx) for sfx in ALLOWED_SUFFIXES)


def assert_allowed(url: str, *, company_hosts: frozenset[str] = frozenset()) -> None:
    """Raise NotAllowed when the URL host is off the allowlist."""
    host = urlparse(url).hostname
    if not host or not host_allowed(host, company_hosts=company_hosts):
        raise NotAllowed(url)