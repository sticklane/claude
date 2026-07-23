"""Shadow mode: one-way markdown task headers -> bd tracker sync.

Markdown stays the source of truth; bd mirrors the queue. ``shadow-sync``
reads every ``specs/*/tasks/*.md`` header (Status, Depends on, Priority,
Budget, Touch, Rigor) via the shared ``_shared/headers.py`` regexes, maps each
task to a bd issue with a deterministic id, and force-imports the whole set so
bd reflects the current markdown. It NEVER writes markdown, and it takes the
D8 write lock like any other writer.

Status is mapped into bd's frontier equivalence classes rather than preserved
verbatim, so ``agentic ready`` over the imported queue classifies each task
exactly as the pre-cutover ``drain_frontier.py`` classifies it over markdown
(the differential the test asserts):

    pending/open/todo/ready        -> open       (dispatchable candidate)
    done/skipped/closed            -> closed     (satisfies dependents)
    in-progress/in_progress/claimed-> in_progress(an in-flight claim)
    everything else                -> blocked    (not dispatchable, still blocks)

The raw markdown status is retained in metadata (``md_status``) so the mirror
does not lose the true state. Dependencies become bd ``blocks`` edges; Touch,
Budget, and Rigor land in issue metadata.
"""

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Bootstrap the shared header regexes the workboard.py way: put _shared/ on
# sys.path, then a regular ``import headers`` (path-loading the loader would
# need a loader to load the loader).
_SHARED = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "_shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
from headers import DEPENDS_RE, PRIORITY_RE, STATUS_RE  # noqa: E402

from agentic import bd  # noqa: E402

# Header regexes not carried by _shared/headers.py (Touch/Budget/Rigor).
_TOUCH_RE = re.compile(r"^Touch:\s*(.*)$", re.MULTILINE)
_BUDGET_RE = re.compile(r"^Budget:\s*(.*)$", re.MULTILINE)
_RIGOR_RE = re.compile(r"^Rigor:\s*(.*)$", re.MULTILINE)
_LEADING_NUM_RE = re.compile(r"^(\d+)")

# markdown Status value -> bd status equivalence class (see module docstring).
_OPEN = {"pending", "open", "todo", "ready"}
_CLOSED = {"done", "skipped", "closed"}
_IN_PROGRESS = {"in-progress", "in_progress", "claimed"}


def bd_status_for(md_status):
    """Map a markdown Status value onto bd's frontier equivalence class."""
    v = (md_status or "").lower()
    if v in _OPEN:
        return "open"
    if v in _CLOSED:
        return "closed"
    if v in _IN_PROGRESS:
        return "in_progress"
    return "blocked"


def _priority_int(text):
    """bd integer priority from a ``Priority:`` header (missing/oob -> P2=2)."""
    m = PRIORITY_RE.search(text)
    return int(m.group(1)[1:]) if m else 2


def _status_value(text):
    """The raw markdown Status value, or ``pending`` when the header is absent."""
    m = STATUS_RE.search(text)
    return m.group(1).lower() if m else "pending"


def _task_number(filename):
    """The leading integer of a task filename, or None (``02-x.md`` -> 2)."""
    m = _LEADING_NUM_RE.match(filename)
    return int(m.group(1)) if m else None


def _parse_touch(text):
    m = _TOUCH_RE.search(text)
    if not m:
        return set()
    return {e.strip() for e in m.group(1).split(",") if e.strip()}


def _parse_single(regex, text):
    m = regex.search(text)
    return m.group(1).strip() if m and m.group(1).strip() else None


def _parse_deps(text):
    """Depends-on entries as ``{'kind': 'number'|'path', ...}`` tokens."""
    m = DEPENDS_RE.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw or raw.lower() == "none":
        return []
    deps = []
    for entry in raw.split(","):
        e = entry.strip()
        if not e:
            continue
        if re.fullmatch(r"\d+", e):
            deps.append({"kind": "number", "num": int(e)})
        elif "/" in e or e.endswith(".md"):
            deps.append({"kind": "path", "raw": e})
    return deps


def task_id(rel_path):
    """A deterministic, stable bd id for a task's relative path (upsert key)."""
    digest = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:8]
    return f"md-{digest}"


def discover_spec_dirs(root):
    """Every ``specs/<name>/`` directory under ``root`` that has a ``tasks/``."""
    specs = Path(root) / "specs"
    if not specs.is_dir():
        return []
    return sorted(
        str(d) for d in specs.iterdir() if d.is_dir() and (d / "tasks").is_dir()
    )


def parse_task(path, root):
    """Parse one task file into the fields shadow-sync mirrors into bd.

    ``path`` is the task file; ``root`` is the base the emitted ``rel`` path is
    relative to, so the bd title matches ``drain_frontier``'s task path.
    """
    text = Path(path).read_text(encoding="utf-8")
    rel = os.path.relpath(str(path), str(root))
    md_status = _status_value(text)
    return {
        "rel": rel,
        "spec": str(Path(path).parents[1]),
        "num": _task_number(Path(path).name),
        "md_status": md_status,
        "status": bd_status_for(md_status),
        "priority": _priority_int(text),
        "touch": sorted(_parse_touch(text)),
        "budget": _parse_single(_BUDGET_RE, text),
        "rigor": _parse_single(_RIGOR_RE, text),
        "deps": _parse_deps(text),
    }


def _resolve_dep(dep, task, by_spec_num, by_rel):
    """Resolve a dep token to another scanned task's rel path, or None."""
    if dep["kind"] == "number":
        target = by_spec_num.get((task["spec"], dep["num"]))
        return target["rel"] if target else None
    resolved = (Path(task["spec"]) / "tasks" / dep["raw"]).resolve()
    # Also accept a repo-relative or same-dir reference.
    candidates = {
        str(resolved),
        str((Path(task["spec"]) / "tasks" / Path(dep["raw"]).name)),
    }
    for rel, t in by_rel.items():
        if str(Path(t["rel"]).resolve()) in candidates or rel.endswith(dep["raw"]):
            return t["rel"]
    return None


def build_rows(spec_dirs, root):
    """Build the bd issue rows for every task in ``spec_dirs`` (one-way mirror)."""
    tasks = []
    for sd in spec_dirs:
        tasks_dir = Path(sd) / "tasks"
        if not tasks_dir.is_dir():
            continue
        for tf in sorted(tasks_dir.glob("*.md")):
            tasks.append(parse_task(tf, root))

    by_spec_num = {(t["spec"], t["num"]): t for t in tasks if t["num"] is not None}
    by_rel = {t["rel"]: t for t in tasks}

    rows = []
    for t in tasks:
        meta = {"touch": t["touch"], "md_status": t["md_status"], "source": t["rel"]}
        if t["budget"]:
            meta["budget"] = t["budget"]
        if t["rigor"]:
            meta["rigor"] = t["rigor"]

        deps = []
        tid = task_id(t["rel"])
        for dep in t["deps"]:
            target_rel = _resolve_dep(dep, t, by_spec_num, by_rel)
            if target_rel is None:
                continue  # dep points outside the scanned set -> not an edge
            deps.append(
                {
                    "issue_id": tid,
                    "depends_on_id": task_id(target_rel),
                    "type": "blocks",
                }
            )

        row = {
            "id": tid,
            "title": t["rel"],
            "status": t["status"],
            "priority": t["priority"],
            "issue_type": "task",
            "metadata": meta,
        }
        if deps:
            row["dependencies"] = deps
        rows.append(row)
    return rows


def sync(store_cwd=None, spec_dirs=None, *, take_lock=True, acquire_timeout=None):
    """One-way sync of markdown task headers into the bd store at ``store_cwd``.

    Reads ``spec_dirs`` (default: every ``specs/*/`` with a ``tasks/`` under
    ``store_cwd``) and force-imports the mirrored rows into bd, so markdown
    always wins. Returns the number of rows synced. Never writes markdown.

    ``acquire_timeout`` (seconds) is forwarded to the write lock when
    ``take_lock`` is set; ``None`` uses the lock's default.
    """
    root = store_cwd or os.getcwd()
    if spec_dirs is None:
        spec_dirs = discover_spec_dirs(root)
    rows = build_rows(spec_dirs, root)

    def _do_import():
        with tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", dir=root, delete=False
        ) as fh:
            tmp = fh.name
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        try:
            # Markdown is the source of truth: force every row in, even over a
            # newer bd row (one-way, last-writer-is-markdown).
            bd.bd_import(tmp, cwd=root, allow_stale=True)
        finally:
            os.unlink(tmp)

    if take_lock:
        # Import lazily to avoid a circular import at module load.
        from agentic.lock import DEFAULT_ACQUIRE_TIMEOUT, RepoLock
        from agentic.sync import repo_root

        timeout = (
            DEFAULT_ACQUIRE_TIMEOUT if acquire_timeout is None else acquire_timeout
        )
        with RepoLock(repo_root(root), acquire_timeout=timeout):
            _do_import()
    else:
        _do_import()
    return len(rows)


def run(args=None):
    count = sync(os.getcwd())
    print(f"shadow-sync: {count} task(s) mirrored into bd")
    return 0


if __name__ == "__main__":
    sys.exit(run())
