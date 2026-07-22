"""stdlib HTTP router for the notes service.

Run directly to serve on a port (default 8000)::

    python3 router.py 8080

Only the Python standard library is used.
"""

import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import handlers
from store import NoteStore

NOTE_ID_RE = re.compile(r"^/notes/(\d+)$")


def make_handler(store):
    class NotesHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status, body):
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/notes":
                query = parse_qs(parsed.query)
                status, body = handlers.list_notes(store, query)
                self._send(status, body)
                return
            match = NOTE_ID_RE.match(parsed.path)
            if match:
                status, body = handlers.get_note(store, int(match.group(1)))
                self._send(status, body)
                return
            self._send(404, handlers.error_body("not_found", "unknown route"))

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path == "/notes":
                length = int(self.headers.get("Content-Length", 0) or 0)
                raw = self.rfile.read(length).decode("utf-8") if length else ""
                status, body = handlers.create_note(store, raw)
                self._send(status, body)
                return
            self._send(404, handlers.error_body("not_found", "unknown route"))

    return NotesHandler


def make_server(port, store=None):
    """Build a server bound to ``port`` and the store it serves."""
    store = store if store is not None else NoteStore()
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(store))
    return server, store


def main(argv):
    port = int(argv[1]) if len(argv) > 1 else 8000
    server, _ = make_server(port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main(sys.argv)
