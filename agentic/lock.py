"""D8: the repo-level write lock.

Every ``agentic`` write command takes this lock before touching the tracker,
so two concurrent processes on one machine cannot lose an export and a human
running ``agentic verdict`` by hand during a loop is safe. The lock is a file
at ``.beads/agentic.lock`` holding the owner's PID, host, and acquire time.

Acquisition is atomic via ``O_CREAT | O_EXCL`` — only one process can create
the file. A live holder is honored (its PID is alive) until it releases the
lock; a waiter spins up to ``acquire_timeout``. An ABANDONED lock — a dead PID
whose file mtime is older than the stale timeout — is reclaimed (D8's
stale-lock recovery), so a crashed process never wedges the tracker forever.
"""

import json
import os
import socket
import time

LOCK_NAME = "agentic.lock"

# How long to wait for a live holder before giving up (seconds).
DEFAULT_ACQUIRE_TIMEOUT = 60.0
# How old an abandoned lock must be before it is reclaimed (seconds). Tunable
# via the environment so tests can drive takeover quickly.
DEFAULT_STALE_SECS = 30.0
_POLL = 0.05


class LockTimeout(Exception):
    """A live lock holder did not release within ``acquire_timeout``."""


def _stale_secs():
    raw = os.environ.get("AGENTIC_LOCK_STALE_SECS")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return DEFAULT_STALE_SECS


def _pid_alive(pid, host):
    """True if ``pid`` is a live process on THIS host.

    A lock recorded on another host cannot be probed, so we report the PID as
    NOT alive there and let the mtime age decide staleness.
    """
    if host != socket.gethostname():
        return False
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    return True


def _is_stale(path):
    """An abandoned lock: its owner PID is not alive AND the file mtime is
    older than the stale timeout. A live holder is never stale, however old
    its file — so a legitimately long write is not stolen mid-operation."""
    try:
        raw = os.stat(path)
        age = time.time() - raw.st_mtime
    except FileNotFoundError:
        return False
    if age < _stale_secs():
        return False
    try:
        with open(path) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        # Unparseable and old -> treat as abandoned.
        return True
    return not _pid_alive(data.get("pid"), data.get("host", ""))


class RepoLock:
    """Context manager holding the repo write lock for its ``with`` block."""

    def __init__(self, repo_root, acquire_timeout=DEFAULT_ACQUIRE_TIMEOUT):
        self.path = os.path.join(str(repo_root), ".beads", LOCK_NAME)
        self.acquire_timeout = acquire_timeout
        self._held = False

    def acquire(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        deadline = time.time() + self.acquire_timeout
        payload = json.dumps(
            {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "time": time.time(),
            }
        ).encode()
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                if _is_stale(self.path):
                    # Reclaim: the O_EXCL create below is the real arbiter, so
                    # two racers both unlinking still yields one winner.
                    try:
                        os.unlink(self.path)
                    except FileNotFoundError:
                        pass
                    continue
                if time.time() > deadline:
                    raise LockTimeout(
                        f"could not acquire {self.path} within "
                        f"{self.acquire_timeout}s (held by a live process)"
                    )
                time.sleep(_POLL)
                continue
            else:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                self._held = True
                return self

    def release(self):
        if self._held:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass
            self._held = False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
        return False
