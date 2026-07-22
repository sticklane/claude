"""Shared pytest helpers: a live server fixture over an ephemeral port."""

import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest

from router import make_server


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class Client:
    """A minimal HTTP client returning ``(status, parsed_json)``."""

    def __init__(self, base):
        self.base = base

    def request(self, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, body):
        return self.request("POST", path, body)


@pytest.fixture
def client():
    port = _free_port()
    server, _store = make_server(port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:%d" % port
    # wait for readiness
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/notes", timeout=0.2).read()
            break
        except Exception:
            time.sleep(0.05)
    try:
        yield Client(base)
    finally:
        server.shutdown()
        thread.join(timeout=2)
