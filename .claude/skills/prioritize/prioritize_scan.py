#!/usr/bin/env python3
"""prioritize_scan — per-repo table of reorderable work (R1+R2).

Scans `specs/` under the current working directory (excluding `archive/`, the
same way `scan_toolkit_specs` already does), keeps every task whose status is
`pending`, `blocked`, `deferred`, or `draft`, plus one row per spec that has
no `tasks/` breakdown yet (its `SPEC.md` stands in for the row), and prints
one markdown table `Ref | Title | Status | Priority` sorted by spec slug then
task number — or the single line `nothing to reprioritize` when none qualify.

`scan_toolkit_specs` does not parse `Priority:` (its task dict keys are
`file`, `abs`, `title`, `status`, `deps`), so this script adds its own
`Priority:` header regex over each task's file content. Absent header shows
`P2 (default)`.

Stdlib only. Read-only: never mutates anything it scans.

See specs/prioritize/SPEC.md (R1, R2) for the requirements this implements.
"""

import importlib.util
import re
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve()
_WORKBOARD_PY = _SCRIPT.parent.parent / "workboard" / "workboard.py"

_QUALIFYING = ("pending", "blocked", "deferred", "draft")
_CLOSED_SPEC_STATUSES = ("done", "skipped")
_PRIORITY_RE = re.compile(r"^Priority:\s*(P[0-3])", re.MULTILINE)
_TASK_NUM_RE = re.compile(r"^(\d+)-")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Loading workboard.py this way executes its own top-level shared-module
# imports; its CLI logic stays inert behind `if __name__ == "__main__":`.
_workboard = _load_module("_prioritize_workboard", _WORKBOARD_PY)
scan_toolkit_specs = _workboard.scan_toolkit_specs
read_text = _workboard.read_text
STATUS_RE = _workboard.STATUS_RE


def _task_number(filename):
    """Leading `NN-` number for sort order; unnumbered files sort last."""
    m = _TASK_NUM_RE.match(filename)
    return int(m.group(1)) if m else float("inf")


def _sort_key(ref):
    """Order rows by spec slug then numeric task number (R2)."""
    slug, _, filename = ref.partition("/")
    return (slug, _task_number(filename), filename)


def _priority(path):
    """The file's `Priority:` header value, or `P2 (default)` when absent."""
    m = _PRIORITY_RE.search(read_text(Path(path), 10_000))
    return m.group(1) if m else "P2 (default)"


def collect(repo_root):
    """R1+R2: sorted rows for every pending/blocked/deferred/draft task,
    plus one row per spec with no tasks/ breakdown yet."""
    rows = []
    for spec in scan_toolkit_specs(Path(repo_root)):
        slug = spec["slug"]
        for task in spec["tasks"]:
            if task["status"] not in _QUALIFYING:
                continue
            filename = Path(task["file"]).name
            rows.append(
                {
                    "ref": f"{slug}/{filename}",
                    "title": task["title"],
                    "status": task["status"],
                    "priority": _priority(task["abs"]),
                }
            )
        if not spec["tasks"]:
            spec_path = Path(repo_root) / spec["path"]
            text = read_text(spec_path, 20_000)
            sm = STATUS_RE.search(text)
            status = sm.group(1).lower() if sm else "open"
            if status in _CLOSED_SPEC_STATUSES:
                continue
            pm = _PRIORITY_RE.search(text)
            rows.append(
                {
                    "ref": f"{slug}/SPEC.md",
                    "title": spec["title"],
                    "status": status,
                    "priority": pm.group(1) if pm else "P2 (default)",
                }
            )
    rows.sort(key=lambda r: _sort_key(r["ref"]))
    return rows


def render(rows):
    """R2: markdown table, or the exact 'nothing to reprioritize' line."""
    if not rows:
        return "nothing to reprioritize"
    lines = [
        "| Ref | Title | Status | Priority |",
        "| --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(f"| {r['ref']} | {r['title']} | {r['status']} | {r['priority']} |")
    return "\n".join(lines)


def run(repo_root):
    print(render(collect(repo_root)))


def main():
    run(Path.cwd())


if __name__ == "__main__":
    main()
