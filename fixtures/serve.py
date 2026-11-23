#!/usr/bin/env python3
"""Serve the synthetic fixture site on localhost. Used by tests and `make serve-fixtures`."""

from __future__ import annotations

import functools
import http.server
import threading
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep test output free of request lines
        pass


def make_server(port: int = 0) -> http.server.ThreadingHTTPServer:
    """Build a server bound to localhost. port=0 picks a free port."""
    handler = functools.partial(_Quiet, directory=str(SITE))
    return http.server.ThreadingHTTPServer((HOST, port), handler)


def start_in_thread(port: int = 0) -> tuple[http.server.ThreadingHTTPServer, str]:
    server = make_server(port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://{HOST}:{server.server_address[1]}"


if __name__ == "__main__":
    server = make_server(DEFAULT_PORT)
    print(f"serving fixtures at http://{HOST}:{DEFAULT_PORT} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
