"""Placeholder privacy test.

Keeps `make privacy` and CI wired from day one. Real privacy tests arrive with
E2-5 (expiry, suppression), E3-3 (injection, log hygiene) and E6-3 (isolation);
each of them replaces or extends this file's job.
"""

import pytest

pytestmark = pytest.mark.privacy


def test_no_send_capability_exists():
    """Medici never sends messages. No module may expose a send function."""
    import pkgutil

    import medici

    names = [m.name for m in pkgutil.walk_packages(medici.__path__, "medici.")]
    assert not [n for n in names if n.rsplit(".", 1)[-1] in {"send", "sender", "mailer"}]
