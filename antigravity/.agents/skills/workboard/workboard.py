#!/usr/bin/env python3
"""workboard — a cross-repo dashboard of specs, tasks, sessions, and agent state.

Scans local git repos and Claude Code state on this machine and emits a
JSON snapshot of all open work (with --json; consumed by agent-console's
live dashboard and /list-specs). With no --json flag it prints a one-line
summary. It covers:

  - toolkit specs   specs/<slug>/SPEC.md + specs/<slug>/tasks/NN-*.md (Status: lines)
  - Kiro specs      .kiro/specs/<name>/tasks.md checkbox state ([ ] [-] [x])
  - Antigravity     ~/.gemini/antigravity*/brain/<id>/ artifacts (task.md + metadata)
  - handoffs        HANDOFF.md files (blocked-on-human, resumable)
  - batons          specs/*/DRAIN-BATON.md (a parked drain generation to relaunch)
  - sessions        ~/.claude/projects/<escaped>/<sessionId>.jsonl transcripts
                    (repo, branch, first prompt, last activity, live PID)
  - git             branch, dirty files, unpushed commits, worktrees

Stdlib only. Read-only: it never mutates any of the state it reports on,
except two explicit, --flag-gated actions: `--abandon`/`--abandon-stale`
(Antigravity skip-marker) and `--prune-stale-sessions` (deletes dead-pid
~/.claude/sessions/*.json records).

Usage:
  workboard.py [ROOTS ...] [--json] [--stale-days 7]
               [--max-depth 3] [--quiet]

With no ROOTS it scans common code directories (~/code ~/src ~/projects
~/dev ~/repos ~/work, plus the cwd) and every repo any Claude Code session
has touched (derived from session records' cwd field).
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent.parent / "_shared"))
from headers import DEPENDS_RE, PRIORITY_RE, STATUS_RE  # noqa: E402

# runtimes/ ships alongside the toolkit's .claude/, four levels up from this
# file (.claude/skills/workboard/workboard.py). parse_headless resolves each
# profile relative to its own directory, so the regex table is always built
# from the toolkit installation this scanner ships with — never from a
# scanned target repo's tree.
sys.path.insert(0, str(SCRIPT.parents[3] / "runtimes"))
import parse_headless  # noqa: E402

STALE_DAYS_DEFAULT = 7
# A `task/*` worktree counts as a live drain only if its newest activity is
# younger than this window (matches drain/reference.md's grace window). Older ⇒
# stranded ⇒ still flags. Deliberately NOT --stale-days (7d is far too coarse).
DRAIN_WINDOW_DEFAULT = 900  # 15 minutes, in seconds
RECENT_HOURS = 48
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    "dist",
    "build",
    "target",
    ".next",
    ".cache",
    "vendor",
}
DEFAULT_ROOT_CANDIDATES = ["code", "src", "projects", "dev", "repos", "work"]

# ---------------------------------------------------------------- utilities


def now_ts():
    return time.time()


def age_str(ts):
    """Human age like '3h' / '4d' for a unix timestamp, or '?' if unknown."""
    if not ts:
        return "?"
    delta = max(0, now_ts() - ts)
    if delta < 3600:
        return f"{int(delta // 60)}m"
    if delta < 86400:
        return f"{int(delta // 3600)}h"
    return f"{int(delta // 86400)}d"


def iso_to_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def run_git(repo, *args):
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def read_text(path, limit=200_000):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


# ---------------------------------------------------------------- discovery


def find_repos(roots, max_depth):
    """Walk roots (depth-limited, pruned) and yield git repo toplevels."""
    seen = set()
    for root in roots:
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            continue
        base_depth = len(root.parts)
        for dirpath, dirnames, _ in os.walk(root):
            depth = len(Path(dirpath).parts) - base_depth
            if (Path(dirpath) / ".git").exists() or (Path(dirpath) / ".jj").exists():
                p = str(Path(dirpath).resolve())
                if p not in seen:
                    seen.add(p)
                    yield Path(p)
                dirnames[:] = []  # don't descend into a repo for more repos
                continue
            if depth >= max_depth:
                dirnames[:] = []
                continue
            dirnames[:] = [
                d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
            ]


def default_roots():
    home = Path.home()
    roots = [Path.cwd()]
    roots += [home / d for d in DEFAULT_ROOT_CANDIDATES if (home / d).is_dir()]
    return roots


# ---------------------------------------------------------------- git state


def _worktree_activity(wt_path, branch, repo):
    """Newest-activity timestamp for a worktree: the max file mtime under it
    (excluding .git/ and node_modules/), floored by the branch tip-commit time.
    Recency — never the worktree lock's pid — decides live vs. stranded."""
    newest = 0.0
    try:
        for root, dirs, files in os.walk(wt_path):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
            for name in files:
                try:
                    m = os.lstat(os.path.join(root, name)).st_mtime
                    if m > newest:
                        newest = m
                except OSError:
                    pass
    except OSError:
        pass
    if branch:
        tip = run_git(repo, "log", "-1", "--format=%ct", branch)
        if tip:
            newest = max(newest, float(tip))
    return newest or None


def git_info(repo):
    branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD") or "?"
    porcelain = run_git(repo, "status", "--porcelain")
    dirty = len(porcelain.splitlines()) if porcelain else 0
    ahead = behind = 0
    lr = run_git(repo, "rev-list", "--left-right", "--count", "@{u}...HEAD")
    if lr and "\t" in lr:
        b, a = lr.split("\t")
        ahead, behind = int(a), int(b)
    last_commit = run_git(repo, "log", "-1", "--format=%ct")
    worktrees = []
    wt = run_git(repo, "worktree", "list", "--porcelain") or ""
    cur = {}
    for line in wt.splitlines() + [""]:
        if line.startswith("worktree "):
            cur = {"path": line[9:]}
        elif line.startswith("branch "):
            cur["branch"] = line[7:].replace("refs/heads/", "")
        elif not line and cur:
            if Path(cur.get("path", "")).resolve() != Path(repo).resolve():
                # Newest-activity timestamp drives live-vs-stale drain coverage
                # in attention_items(). Only task/* worktrees consult it, so
                # only they pay the filesystem walk.
                if (cur.get("branch") or "").startswith("task/"):
                    cur["activity_ts"] = _worktree_activity(
                        cur.get("path", ""), cur.get("branch"), repo
                    )
                worktrees.append(cur)
            cur = {}
    return {
        "branch": branch,
        "dirty": dirty,
        "ahead": ahead,
        "behind": behind,
        "last_commit_ts": float(last_commit) if last_commit else None,
        "worktrees": worktrees,
    }


# ---------------------------------------------------------------- specs

# STATUS_RE, DEPENDS_RE, PRIORITY_RE now live in _shared/headers.py (imported
# at the top of this module) so /workboard and /prioritize parse the same
# header one way. PRIORITY_RE there is range-restricted to P0-P3.
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
UNBLOCK_RE = re.compile(r"^Unblock:\s*(run|agent|ask):\s*(\S.*?)\s*$", re.MULTILINE)
DEFERRED_RE = re.compile(
    r"^#{2,}\s+Deferred questions\s*$(.*?)(?=^#{1,6}\s|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
OPEN_TASK_STATUSES = {
    "pending",
    "open",
    "todo",
    "ready",
    "in-progress",
    "in_progress",
    "claimed",
    # completed-but-unverified: agent-bounded (the verifier proceeds), so it
    # is open in-flight work — never a blocked flag, never done.
    "needs-verification",
    "needs_verification",
}
CLOSED_TASK_STATUSES = {"done", "deferred", "skipped"}


def _task_is_blocked(status):
    """A task status that is neither open nor closed reads as blocked (matches
    scan_toolkit_specs' `tasks_blocked` rule): blocked, waiting, failed, …"""
    return status not in CLOSED_TASK_STATUSES and status not in OPEN_TASK_STATUSES


def parse_unblock(text):
    """The `Unblock: <run|agent|ask>: <step>` line → {type, step}; None when the
    line is absent or malformed (unknown type, or empty step)."""
    m = UNBLOCK_RE.search(text)
    if not m:
        return None
    return {"type": m.group(1), "step": m.group(2).strip()}


def parse_deferred_questions(text):
    """Bullet items under a `## Deferred questions` section, as a list of
    strings; [] when the section is absent."""
    m = DEFERRED_RE.search(text)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        bm = re.match(r"\s*[-*]\s+(.+)", line)
        if bm and bm.group(1).strip():
            out.append(bm.group(1).strip())
    return out


_TASK_NUM_RE = re.compile(r"^(\d+)-")


def scan_toolkit_specs(repo):
    """specs/<slug>/SPEC.md + tasks/NN-*.md with 'Status: <value>' lines."""
    specs = []
    specs_dir = repo / "specs"
    if not specs_dir.is_dir():
        return specs
    for spec_dir in sorted(specs_dir.iterdir()):
        spec_md = spec_dir / "SPEC.md"
        if not spec_dir.is_dir() or not spec_md.is_file():
            continue
        text = read_text(spec_md, 20_000)
        m = TITLE_RE.search(text)
        pm = PRIORITY_RE.search(text)
        tasks = []
        tasks_dir = spec_dir / "tasks"
        mtimes = [spec_md.stat().st_mtime]
        unparseable = 0
        if tasks_dir.is_dir():
            for tf in sorted(tasks_dir.glob("*.md")):
                t_text = read_text(tf, 10_000)
                sm = STATUS_RE.search(t_text)
                status = sm.group(1).lower() if sm else "pending"
                tm = TITLE_RE.search(t_text)
                task = {
                    "file": str(tf.relative_to(repo)),
                    "abs": str(tf),
                    "title": tm.group(1).strip() if tm else tf.stem,
                    "status": status,
                    "deps": parse_deps(t_text),
                }
                if _task_is_blocked(status):
                    ub = parse_unblock(t_text)
                    if ub:
                        task["unblock"] = ub
                dq = parse_deferred_questions(t_text)
                if dq:
                    task["deferred_questions"] = dq
                tasks.append(task)
                mtimes.append(tf.stat().st_mtime)
                if not _TASK_NUM_RE.match(tf.name):
                    unparseable += 1
        spec_sm = STATUS_RE.search(text)
        spec_status = spec_sm.group(1).lower() if spec_sm else None
        done = sum(1 for t in tasks if t["status"] in CLOSED_TASK_STATUSES)
        doing = sum(
            1 for t in tasks if t["status"] in ("in-progress", "in_progress", "claimed")
        )
        blocked = [
            t
            for t in tasks
            if t["status"] not in CLOSED_TASK_STATUSES
            and t["status"] not in OPEN_TASK_STATUSES
        ]
        spec_rec = {
            "kind": "toolkit",
            "slug": spec_dir.name,
            "title": (m.group(1).strip() if m else spec_dir.name),
            "priority": (pm.group(1) if pm else ""),
            "path": str(spec_md.relative_to(repo)),
            "tasks_total": len(tasks),
            "tasks_done": done,
            "tasks_doing": doing,
            "tasks_blocked": [t["file"] for t in blocked],
            "tasks": tasks,
            "tasks_unparseable": unparseable,
            "last_touched": max(mtimes),
        }
        if spec_status == "waiting":
            spec_rec["status"] = spec_status
            ub = parse_unblock(text)
            if ub:
                spec_rec["unblock"] = ub
        specs.append(spec_rec)
    return specs


# ---------------------------------------------------------------- readiness


def parse_deps(text):
    """The `Depends on:` header as a list of raw entries; none/empty ⇒ []."""
    m = DEPENDS_RE.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw or raw.lower() == "none":
        return []
    return [e.strip() for e in raw.split(",") if e.strip()]


def _glob_task(tasks_dir, num):
    """First `NN-*.md` in tasks_dir matching the (possibly unpadded) prefix."""
    if not tasks_dir.is_dir():
        return None
    for pat in dict.fromkeys((f"{num}-*.md", f"{int(num):02d}-*.md")):
        matches = sorted(tasks_dir.glob(pat))
        if matches:
            return matches[0]
    return None


def resolve_dep(entry, task_dir, repo_root):
    """Resolve one `Depends on:` entry to a task file the way /drain does.

    - bare numeric (`01`)        → sibling `NN-*.md` in the same spec's tasks/
    - `<slug>/NN` shorthand      → `../<slug>/tasks/NN-*.md` (another spec)
    - task-file-relative path    → resolved against the current task dir
    - `specs/...`-rooted path    → also tried against the repo root
    Returns the resolved Path (existing file) or None if unresolvable.
    """
    entry = entry.strip()
    if not entry:
        return None
    if re.fullmatch(r"\d+", entry):
        return _glob_task(task_dir, entry)
    m = re.fullmatch(r"([A-Za-z0-9_.-]+)/(\d+)", entry)
    if m:
        return _glob_task(task_dir.parent.parent / m.group(1) / "tasks", m.group(2))
    # path form: try task-dir-relative first, then repo-root for specs/ roots
    bases = [task_dir]
    if entry.startswith("specs/") or entry.startswith("/"):
        bases.append(repo_root)
    for base in bases:
        cand = base / entry
        if any(ch in entry for ch in "*?["):
            parent = cand.parent
            matches = sorted(parent.glob(cand.name)) if parent.is_dir() else []
            if matches:
                return matches[0]
        elif cand.is_file():
            return cand
    return None


def _dep_is_done(path):
    m = STATUS_RE.search(read_text(path, 10_000))
    return bool(m) and m.group(1).lower() == "done"


def ready_items(repos):
    """Dispatchable toolkit-spec tasks (Status: pending, all deps done).

    Per spec: one ready task ⇒ a `/build <file>` item; two or more ready in a
    spec ⇒ a single `/drain specs/<slug>` item. A task with an unresolvable
    dep id is not ready but is surfaced as blocked-by-unresolved."""
    items, blocked = [], []
    for r in repos:
        repo_path = r["path"]
        repo_root = Path(repo_path)
        for s in r["specs"]:
            if s.get("kind") != "toolkit":
                continue
            spec_ready = []
            for t in s["tasks"]:
                if t["status"] != "pending":
                    continue
                task_dir = Path(t["abs"]).parent
                # Scan every dep so an unresolvable id is always surfaced (R1),
                # even when a resolvable-but-unfinished dep precedes it.
                satisfied, unresolved = True, None
                for dep in t.get("deps", []):
                    resolved = resolve_dep(dep, task_dir, repo_root)
                    if resolved is None:
                        unresolved = dep
                        break
                    if not _dep_is_done(resolved):
                        satisfied = False
                if unresolved is not None:
                    blocked.append(
                        {
                            "repo": r["name"],
                            "slug": s["slug"],
                            "task": t["file"],
                            "dep": unresolved,
                        }
                    )
                elif satisfied:
                    spec_ready.append(t)
            if len(spec_ready) >= 2:
                cmd = (
                    f'cd {shlex.quote(repo_path)} && claude "/drain specs/{s["slug"]}"'
                )
                items.append(
                    {
                        "repo": r["name"],
                        "slug": s["slug"],
                        "task": f"{len(spec_ready)} ready tasks",
                        "cmd": cmd,
                        "kind": "drain",
                    }
                )
            elif spec_ready:
                t = spec_ready[0]
                cmd = f'cd {shlex.quote(repo_path)} && claude "/build {t["file"]}"'
                items.append(
                    {
                        "repo": r["name"],
                        "slug": s["slug"],
                        "task": t["title"],
                        "cmd": cmd,
                        "kind": "build",
                    }
                )
    return {"items": items, "blocked_unresolved": blocked}


CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ x-])\]", re.MULTILINE)

# An open `## Agent-filed blockers` entry (.claude/rules/human-blockers.md):
#   - [ ] <ISO date> · <source path> · <ask|run|provision|decide> — <action>
# Anchored on `[ ]` so checked (`- [x]`) / in-progress (`- [-]`) entries never
# match — tools skip them. A line that doesn't fit the grammar is skipped, not
# an error (graceful degradation).
HUMAN_BLOCKER_RE = re.compile(
    r"^\s*-\s*\[ \]\s*"
    r"(?P<date>\S+)\s*·\s*"
    r"(?P<source>.+?)\s*·\s*"
    r"(?P<type>ask|run|provision|decide)\s*—\s*"
    r"(?P<ask>.+?)\s*$",
    re.MULTILINE,
)


def scan_kiro_specs(repo):
    """.kiro/specs/<name>/tasks.md — checkboxes [ ] todo, [-] doing, [x] done."""
    specs = []
    kiro = repo / ".kiro" / "specs"
    if not kiro.is_dir():
        return specs
    for spec_dir in sorted(kiro.iterdir()):
        tasks_md = spec_dir / "tasks.md"
        if not spec_dir.is_dir():
            continue
        boxes = CHECKBOX_RE.findall(read_text(tasks_md)) if tasks_md.is_file() else []
        total = len(boxes)
        done = boxes.count("x")
        doing = boxes.count("-")
        phase = [
            f
            for f in ("requirements.md", "design.md", "tasks.md")
            if (spec_dir / f).is_file()
        ]
        mtime = max(
            (f.stat().st_mtime for f in spec_dir.glob("*.md")),
            default=spec_dir.stat().st_mtime,
        )
        specs.append(
            {
                "kind": "kiro",
                "slug": spec_dir.name,
                "title": spec_dir.name,
                "path": str(spec_dir.relative_to(repo)),
                "tasks_total": total,
                "tasks_done": done,
                "tasks_doing": doing,
                "phase": phase,
                "last_touched": mtime,
            }
        )
    return specs


def scan_handoffs(repo):
    """HANDOFF.md anywhere shallow in the repo = work parked for a human/next session."""
    handoffs = []
    for pattern in (
        "HANDOFF.md",
        "*/HANDOFF.md",
        "*/*/HANDOFF.md",
        ".claude/HANDOFF.md",
        "specs/*/HANDOFF.md",
    ):
        for f in repo.glob(pattern):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            text = read_text(f, 4_000)
            m = TITLE_RE.search(text)
            handoffs.append(
                {
                    "path": str(f.relative_to(repo)),
                    "title": m.group(1).strip() if m else "Handoff",
                    "mtime": f.stat().st_mtime,
                }
            )
    # de-dup (patterns can overlap)
    seen, out = set(), []
    for h in handoffs:
        if h["path"] not in seen:
            seen.add(h["path"])
            out.append(h)
    return out


BATON_GEN_RE = re.compile(r"generation[:\s]+(\d+)", re.IGNORECASE)


def _build_runtime_regexes():
    """Map every runtime profile name to its baton match-shape regex.

    A profile with a scriptable ``## Headless`` template maps to the regex
    derived from it by ``runtimes/parse_headless.py``; a profile with no
    fenced template (e.g. fake-runtime-no-headless — antigravity graduated
    2026-07-12 when ``agy -p`` proved scriptable) maps to ``None`` — a known
    runtime with no scriptable relaunch (manual only). Non-profile ``*.md``
    files in ``runtimes/`` (README) are skipped. Built once at import from
    the toolkit's own ``runtimes/`` dir, not per scanned repo."""
    table = {}
    runtimes_dir = Path(parse_headless.__file__).resolve().parent
    for f in sorted(runtimes_dir.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if not re.search(r"^## Headless\b", text, re.MULTILINE):
            continue  # not a runtime profile (e.g. README.md)
        template = parse_headless.headless_template(f.stem)
        table[f.stem] = (
            None
            if template == parse_headless.NONE
            else parse_headless.derive_match_regex(template)
        )
    return table


#: {runtime-name: compiled regex or None}. None ⇒ manual-relaunch-only runtime.
RUNTIME_REGEXES = _build_runtime_regexes()


def resolve_repo_runtime(repo):
    """Active runtime name for a scanned repo, matching drain's rule.

    Reads ``<repo>/.claude/runtime.md`` — its first non-comment line
    ``runtime: <name>`` selects the profile (convention in
    ``runtimes/README.md``). An absent or malformed file defaults to
    ``claude-code``, so a repo that never opts in keeps today's behavior."""
    rt = Path(repo) / ".claude" / "runtime.md"
    if not rt.exists():
        return parse_headless.DEFAULT_RUNTIME
    try:
        text = rt.read_text(encoding="utf-8")
    except OSError:
        return parse_headless.DEFAULT_RUNTIME
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"runtime:\s*(\S+)", s, re.IGNORECASE)
        return m.group(1) if m else parse_headless.DEFAULT_RUNTIME
    return parse_headless.DEFAULT_RUNTIME


def _parse_baton_command(text, runtime_name):
    """Extract a baton's relaunch command for a repo on ``runtime_name``.

    Returns ``(command, manual_relaunch, parse_warning)`` — exactly one of the
    three is meaningfully set:

    - The resolved runtime is manual-relaunch-only (no scriptable headless
      template, e.g. antigravity): no regex is attempted; ``manual_relaunch``
      names how to reopen it, ``command`` stays ``""``.
    - Otherwise the resolved runtime's regex is tried first, then every other
      known runtime's regex in a stable order; the first match is ``command``.
    - No known shape matches: ``command`` stays ``""`` and ``parse_warning``
      flags it for the needs-attention inbox.

    An unresolvable ``runtime_name`` (no matching profile) falls back to
    ``claude-code`` (R11) — never raises."""
    if runtime_name not in RUNTIME_REGEXES:
        runtime_name = parse_headless.DEFAULT_RUNTIME
    if RUNTIME_REGEXES.get(runtime_name) is None:
        return (
            "",
            f"No scriptable relaunch for {runtime_name} — "
            f"reopen from {runtime_name}'s Agent Manager",
            "",
        )
    order = [runtime_name] + [n for n in sorted(RUNTIME_REGEXES) if n != runtime_name]
    for name in order:
        rx = RUNTIME_REGEXES.get(name)
        if rx is None:
            continue
        m = rx.search(text)
        if m:
            return m.group(0), "", ""
    return (
        "",
        "",
        "Relaunch command matches no known runtime shape — "
        "check the baton's relaunch block",
    )


def _section_body(text, *heading_patterns):
    """Body of the first markdown section whose heading matches, '' if none."""
    for pat in heading_patterns:
        m = re.search(
            rf"^#+\s*{pat}[^\n]*\n(.*?)(?=\n#+\s|\Z)",
            text,
            re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def scan_human_blockers(repo):
    """HUMAN.md `## Agent-filed blockers` = human-actionable items an agent
    can't clear (.claude/rules/human-blockers.md). Returns the OPEN entries
    (`- [ ]`) parsed into {date, source, type, ask}; checked (`- [x]`) entries
    are skipped. Absent file or absent section returns [] — never raises."""
    text = read_text(repo / "HUMAN.md", 20_000)
    if not text:
        return []
    body = _section_body(text, "agent.?filed blockers")
    if not body:
        return []
    return [
        {
            "date": m.group("date"),
            "source": m.group("source").strip(),
            "type": m.group("type"),
            "ask": m.group("ask").strip(),
        }
        for m in HUMAN_BLOCKER_RE.finditer(body)
    ]


def scan_batons(repo):
    """DRAIN-BATON.md = a parked drain generation to relaunch (self-managed,
    not a human handoff — the final generation deletes it)."""
    batons = []
    runtime_name = resolve_repo_runtime(repo)
    for pattern in ("DRAIN-BATON.md", "specs/*/DRAIN-BATON.md"):
        for f in repo.glob(pattern):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            text = read_text(f, 8_000)
            gm = BATON_GEN_RE.search(text)
            command, manual_relaunch, parse_warning = _parse_baton_command(
                text, runtime_name
            )
            batons.append(
                {
                    "path": str(f.relative_to(repo)),
                    "generation": int(gm.group(1)) if gm else None,
                    "command": command,
                    "manual_relaunch": manual_relaunch,
                    "parse_warning": parse_warning,
                    "needs_attention": _section_body(
                        text, "needs.?attention", "deferred"
                    ),
                    "mtime": f.stat().st_mtime,
                }
            )
    seen, out = set(), []
    for b in batons:
        if b["path"] not in seen:
            seen.add(b["path"])
            out.append(b)
    return out


# ---------------------------------------------------------------- sessions


def _first_prompt_and_meta(path):
    """First user prompt + cwd/branch from the head of a session transcript."""
    prompt, cwd, branch = None, None, None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = cwd or rec.get("cwd")
                branch = branch or rec.get("gitBranch")
                if prompt is None and rec.get("type") == "queue-operation":
                    prompt = rec.get("content")
                if prompt is None and rec.get("type") == "user":
                    content = (rec.get("message") or {}).get("content")
                    if isinstance(content, str):
                        prompt = content
                    elif isinstance(content, list):
                        texts = [
                            c.get("text", "")
                            for c in content
                            if isinstance(c, dict) and c.get("type") == "text"
                        ]
                        prompt = " ".join(texts).strip() or None
                if prompt and cwd and branch:
                    break
    except OSError:
        pass
    if prompt:
        prompt = re.sub(r"<[^>]+>", " ", prompt)  # strip system-reminder tags
        prompt = re.sub(r"\s+", " ", prompt).strip()[:200]
    return prompt, cwd, branch


def _first_record_ts(path):
    """Timestamp of the earliest parseable record via a head read (mirrors
    `_first_prompt_and_meta`'s 50-line cap)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = iso_to_ts(rec.get("timestamp", ""))
                if ts:
                    return ts
    except OSError:
        pass
    return None


def _last_record_ts(path):
    """Timestamp (+branch if present) of the last parseable record via a tail read."""
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            f.seek(max(0, size - 65_536))
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None, None
    ts, branch = None, None
    for line in reversed(tail.splitlines()):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = ts or iso_to_ts(rec.get("timestamp", ""))
        branch = branch or rec.get("gitBranch")
        if ts:
            break
    return ts, branch


def _claude_agents_json():
    """Parse `claude agents --json`. None if `claude` is absent from PATH,
    errors, times out, or its stdout isn't a JSON list — any of which sends
    live_session_ids() to the PID-record fallback (SPEC.md R1)."""
    try:
        out = subprocess.run(
            ["claude", "agents", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def _live_session_ids_from_pids(claude_home):
    """Fallback: sessionIds with a live Claude Code process, from
    ~/.claude/sessions/*.json + pid_alive()."""
    live = {}
    sess_dir = claude_home / "sessions"
    if not sess_dir.is_dir():
        return live
    for f in sess_dir.glob("*.json"):
        try:
            rec = json.loads(read_text(f, 10_000))
        except json.JSONDecodeError:
            continue
        pid = rec.get("pid")
        sid = rec.get("sessionId")
        if sid and pid and pid_alive(pid):
            live[sid] = {"pid": pid, "kind": rec.get("kind", "?")}
    return live


def prune_stale_session_pids(claude_home):
    """Delete ~/.claude/sessions/*.json records whose pid is no longer
    alive. These accumulate forever otherwise: the liveness scan above
    already filters dead ones out of its own output, but never removes the
    file. Malformed records (unreadable JSON, missing/non-int pid) are left
    untouched rather than guessed at. Returns (removed, kept): removed is
    the sorted list of deleted records' sessionId (or filename if absent);
    kept is the count of records left in place."""
    sess_dir = claude_home / "sessions"
    if not sess_dir.is_dir():
        return [], 0
    removed, kept = [], 0
    for f in sess_dir.glob("*.json"):
        try:
            rec = json.loads(read_text(f, 10_000))
        except json.JSONDecodeError:
            kept += 1
            continue
        pid = rec.get("pid")
        if isinstance(pid, int) and not pid_alive(pid):
            removed.append(rec.get("sessionId") or f.name)
            f.unlink()
        else:
            kept += 1
    return sorted(removed), kept


def live_session_ids(claude_home):
    """sessionIds with a live Claude Code process.

    Primary source: `claude agents --json` — any record carrying both
    `sessionId` and `pid` counts as live, regardless of its `status` string.
    Falls back to the PID-record scan (_live_session_ids_from_pids) when the
    CLI is absent or its output isn't a JSON list.

    Returns (live, liveness_unknown): `live` keeps the `{sid: {...}}` shape
    in both paths; `liveness_unknown` is True only when the CLI returned a
    non-empty list but none of its records counted as live (SPEC.md R1/R4) —
    the PID-record fallback never sets it.
    """
    records = _claude_agents_json()
    if records is None:
        return _live_session_ids_from_pids(claude_home), False

    live = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        sid, pid = rec.get("sessionId"), rec.get("pid")
        if sid and pid:
            live[sid] = {"pid": pid, "status": rec.get("status")}
    liveness_unknown = bool(records) and not live
    return live, liveness_unknown


_last_liveness_unknown = (
    False  # set by scan_sessions(); read by assemble() (SPEC.md R4)
)


def scan_sessions(claude_home, stale_days):
    global _last_liveness_unknown
    sessions = []
    projects = claude_home / "projects"
    if not projects.is_dir():
        _last_liveness_unknown = False
        return sessions
    live, _last_liveness_unknown = live_session_ids(claude_home)
    for proj_dir in projects.iterdir():
        if not proj_dir.is_dir():
            continue
        for jl in proj_dir.glob("*.jsonl"):
            sid = jl.stem
            prompt, cwd, branch = _first_prompt_and_meta(jl)
            last_ts, last_branch = _last_record_ts(jl)
            last_ts = last_ts or jl.stat().st_mtime
            # start_ts resolution order (SPEC.md R6): earliest transcript
            # record -> transcript st_birthtime -> last-activity (never left
            # None; viz.timeline() raises on a missing start_ts).
            start_ts = _first_record_ts(jl)
            if start_ts is None:
                try:
                    start_ts = jl.stat().st_birthtime
                except (OSError, AttributeError):
                    start_ts = None
            if start_ts is None:
                start_ts = last_ts
            age_days = (now_ts() - last_ts) / 86400
            if sid in live:
                state = "active"
            elif age_days * 24 < RECENT_HOURS:
                state = "recent"
            elif age_days > stale_days:
                state = "stale"
            else:
                state = "idle"
            sessions.append(
                {
                    "id": sid,
                    "cwd": cwd,
                    "branch": last_branch or branch,
                    "prompt": prompt or "(no prompt found)",
                    "last_ts": last_ts,
                    "start_ts": start_ts,
                    "end_ts": last_ts,
                    "bytes": jl.stat().st_size,
                    "state": state,
                }
            )
    sessions.sort(key=lambda s: s["last_ts"], reverse=True)
    return sessions


# ------------------------------------------------------ agent spawn tree

# Harness tool names that spawn a sub-agent (Task is the legacy alias).
_AGENT_TOOL_NAMES = ("Agent", "Task")


def _normalize_agent_status(raw):
    """Map a harness-recorded `toolUseResult.status` onto fleet's status
    vocabulary (running / completed / failed).

    Fleet derives status from the harness's own record of the run: an
    errored/BLOCKED outcome is `failed`, a clean terminal outcome is
    `completed`, and anything still in flight is `running`. The transcript
    equivalent of that record is the tool_result's `toolUseResult.status`:
      - "error" / "blocked" / "failed"       -> failed
      - "completed" / "deferred" / "success" -> completed
      - "async_launched" / absent / other    -> running (spawned, but no
        terminal outcome is recorded in the spawning transcript — a
        background launch records only "async_launched" there)
    """
    if raw in ("error", "blocked", "failed"):
        return "failed"
    if raw in ("completed", "deferred", "success", "done"):
        return "completed"
    return "running"


def _agent_spawn_calls(path):
    """Every Agent/Task `tool_use` in one transcript, paired with its
    `tool_result`, in file order. Returns a list of dicts:
      {"tool_use_id", "started_ts", "ended_ts", "result_status"}.
    A missing/unreadable file yields []. A spawn with no matching
    `tool_result` keeps ended_ts=None and result_status=None (still running).
    The terminal outcome is read from the result record's top-level
    `toolUseResult.status`."""
    calls = []  # ordered by first appearance of the tool_use
    by_id = {}  # tool_use_id -> its call dict
    try:
        f = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return calls
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = iso_to_ts(rec.get("timestamp", "") or "")
            content = (rec.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "tool_use" and block.get("name") in _AGENT_TOOL_NAMES:
                    tuid = block.get("id")
                    if not tuid or tuid in by_id:
                        continue
                    call = {
                        "tool_use_id": tuid,
                        "started_ts": ts,
                        "ended_ts": None,
                        "result_status": None,
                    }
                    calls.append(call)
                    by_id[tuid] = call
                elif btype == "tool_result":
                    call = by_id.get(block.get("tool_use_id"))
                    if call is None:
                        continue
                    if call["ended_ts"] is None:
                        call["ended_ts"] = ts
                    tur = rec.get("toolUseResult")
                    if isinstance(tur, dict) and call["result_status"] is None:
                        call["result_status"] = tur.get("status")
    return calls


def extract_agent_tree(session_jsonl_path):
    """Parse a session transcript's Agent/Task spawns into a nested tree.

    Returns a list of root node dicts — the sub-agents spawned directly by the
    session — each of the shape:
        {agentId, agentType, description, status, spawnDepth,
         started_ts, ended_ts, children: [...]}
    and recurses through every sub-agent's own transcript so a sub-agent that
    itself spawned further sub-agents nests its grandchildren beneath it
    (SPEC.md R1/R4).

    On-disk layout (confirmed on this machine): the parent transcript is
    `<proj>/<sessionId>.jsonl`; its sub-agents live flat in a sibling
    `<proj>/<sessionId>/subagents/` directory as `agent-<agentId>.jsonl` +
    `agent-<agentId>.meta.json` pairs. The meta carries `agentType`,
    `description`, `toolUseId` (the parent tool_use that spawned it), and
    `spawnDepth`; the `agentId` is the filename stem. Parent→child linkage is
    by `toolUseId`: a sub-agent is a child of whichever transcript contains a
    tool_use whose id equals that sub-agent's `toolUseId`.

    A session that spawned nothing — or whose subagents directory is absent —
    returns [] with no error (R3). This function is pure: it only reads the
    transcripts under the session directory and never mutates anything.
    """
    session_jsonl_path = Path(session_jsonl_path)
    subdir = session_jsonl_path.parent / session_jsonl_path.stem / "subagents"
    if not subdir.is_dir():
        return []

    metas = {}  # agentId -> meta dict
    tuid_to_aid = {}  # spawning toolUseId -> agentId
    suffix = ".meta.json"
    for mp in sorted(subdir.glob("agent-*.meta.json")):
        aid = mp.name[len("agent-") : -len(suffix)]
        try:
            meta = json.loads(read_text(mp, 20_000))
        except json.JSONDecodeError:
            continue
        if not isinstance(meta, dict):
            continue
        metas[aid] = meta
        tuid = meta.get("toolUseId")
        if tuid:
            tuid_to_aid[tuid] = aid

    visited = set()  # cycle guard: never recurse into one agent twice

    def build(aid, call):
        meta = metas.get(aid, {})
        node = {
            "agentId": aid,
            "agentType": meta.get("agentType"),
            "description": meta.get("description"),
            "status": _normalize_agent_status(call.get("result_status")),
            "spawnDepth": meta.get("spawnDepth"),
            "started_ts": call.get("started_ts"),
            "ended_ts": call.get("ended_ts"),
            "children": [],
        }
        if aid in visited:
            return node
        visited.add(aid)
        for child_call in _agent_spawn_calls(subdir / f"agent-{aid}.jsonl"):
            caid = tuid_to_aid.get(child_call["tool_use_id"])
            if caid is not None and caid in metas:
                node["children"].append(build(caid, child_call))
        return node

    roots = []
    for call in _agent_spawn_calls(session_jsonl_path):
        aid = tuid_to_aid.get(call["tool_use_id"])
        if aid is not None and aid in metas:
            roots.append(build(aid, call))
    return roots


def scan_session_spawns(claude_home):
    """Per-session agent spawn trees, following the scan_*() contract
    (reference.md: records keyed with last_touched/last_ts). Returns a dict
    mapping session id -> {"spawn_tree", "last_touched", "last_ts"}, so
    assemble() can merge each tree onto that session's existing record
    without any other scan_*() function changing shape (SPEC.md R5/R8).

    `spawn_tree` is extract_agent_tree()'s output for that session's
    transcript — `[]` for a session that spawned nothing. Read-only: it
    parses the same `projects/<proj>/<sid>.jsonl` transcripts scan_sessions()
    reads, never live state, and mutates nothing.
    """
    spawns = {}
    projects = claude_home / "projects"
    if not projects.is_dir():
        return spawns
    for proj_dir in projects.iterdir():
        if not proj_dir.is_dir():
            continue
        for jl in proj_dir.glob("*.jsonl"):
            last_ts, _ = _last_record_ts(jl)
            if last_ts is None:
                try:
                    last_ts = jl.stat().st_mtime
                except OSError:
                    last_ts = None
            spawns[jl.stem] = {
                "spawn_tree": extract_agent_tree(jl),
                "last_touched": last_ts,
                "last_ts": last_ts,
            }
    return spawns


def scan_todos(claude_home):
    """~/.claude/todos/*.json — in-session todo lists, when the install has them."""
    items = []
    todos_dir = claude_home / "todos"
    if not todos_dir.is_dir():
        return items
    for f in todos_dir.glob("*.json"):
        try:
            data = json.loads(read_text(f, 100_000))
        except json.JSONDecodeError:
            continue
        todos = data.get("todos", data) if isinstance(data, dict) else data
        if not isinstance(todos, list):
            continue
        open_items = [
            t
            for t in todos
            if isinstance(t, dict) and t.get("status") in ("pending", "in_progress")
        ]
        if open_items:
            items.append(
                {
                    "session": f.stem.split("-agent-")[0],
                    "open": len(open_items),
                    "total": len(todos),
                    "next": open_items[0].get("content", "")[:120],
                    "mtime": f.stat().st_mtime,
                }
            )
    return items


# ---------------------------------------------------------------- antigravity

# The one deliberate exception to "read-only": --abandon/--abandon-stale drop
# this marker file into a conversation dir. The scanner then skips it forever.
# Nothing of Antigravity's own state (task.md, metadata) is ever modified.
ABANDON_MARKER = ".workboard-abandoned"


def _brain_conversations():
    """Yield (store_name, conversation_dir) across all Antigravity variants."""
    gemini = Path.home() / ".gemini"
    if not gemini.is_dir():
        return
    for variant in gemini.glob("antigravity*"):
        brain = variant / "brain"
        if not brain.is_dir():
            continue
        for conv in brain.iterdir():
            if conv.is_dir():
                yield variant.name, conv


def abandon_conversations(ids):
    """Mark the named conversations abandoned. Returns (marked, missing)."""
    wanted, marked = set(ids), []
    for _, conv in _brain_conversations():
        if conv.name in wanted:
            (conv / ABANDON_MARKER).write_text(
                f"abandoned via workboard {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n",
                encoding="utf-8",
            )
            marked.append(conv.name)
            wanted.discard(conv.name)
    return marked, sorted(wanted)


def abandon_stale(stale_days):
    """Mark every stale conversation (open items, idle past threshold)."""
    stale = [
        c["id"]
        for c in scan_antigravity()
        if c["open"] > 0 and (now_ts() - c["last_ts"]) > stale_days * 86400
    ]
    marked, _ = abandon_conversations(stale)
    return marked


def scan_antigravity():
    """~/.gemini/antigravity*/brain/<conversation>/ artifact dirs."""
    convs = []
    for store, conv in _brain_conversations():
        if (conv / ABANDON_MARKER).is_file():
            continue
        task_md = conv / "task.md"
        boxes = CHECKBOX_RE.findall(read_text(task_md)) if task_md.is_file() else []
        summary, updated = None, None
        meta = conv / "task.md.metadata.json"
        if meta.is_file():
            try:
                md = json.loads(read_text(meta, 10_000))
                summary = md.get("summary")
                updated = iso_to_ts(md.get("updatedAt", ""))
            except json.JSONDecodeError:
                pass
        mtime = updated or conv.stat().st_mtime
        done = boxes.count("x")
        convs.append(
            {
                "id": conv.name,
                "store": store,
                "summary": (summary or conv.name)[:160],
                "tasks_total": len(boxes),
                "tasks_done": done,
                "open": len(boxes) - done,
                "last_ts": mtime,
            }
        )
    convs.sort(key=lambda c: c["last_ts"], reverse=True)
    return convs


# ---------------------------------------------------------------- assembly


def _actively_covered(rp, r, active_toplevels, drain_window):
    """True if a live human session OR a live drain owns this repo's WIP.

    Human coverage is git-toplevel EQUALITY (not path-prefix): a session inside
    a nested child repo/worktree has a different toplevel, so it never falsely
    covers the parent. Drain coverage is any `task/*` worktree whose newest
    activity is within `drain_window` — catches both the .claude/worktrees/*
    background path and the sibling headless-fallback path, with zero extra
    globbing. A parked baton is NOT a coverage signal (no pid/session linkage;
    a stranded generation looks identical to a live one)."""
    if rp in active_toplevels:
        return True
    now = now_ts()
    for wt in r["git"].get("worktrees", []):
        if (wt.get("branch") or "").startswith("task/"):
            act = wt.get("activity_ts")
            if act is not None and (now - act) <= drain_window:
                return True
    return False


def attention_total(inbox):
    """Headline attention count: inbox items EXCEPT reclassified in-progress
    (Active) items — a live session/drain's WIP is not neglected work."""
    return sum(1 for i in inbox if i["state"] != "in-progress")


def _iso_date_ts(date_str):
    """Epoch seconds for an ISO `YYYY-MM-DD` HUMAN.md date, None if unparsable —
    None sorts as oldest (`age_ts or 0`), so a malformed date never crashes."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").timestamp()
    except (ValueError, TypeError):
        return None


# A human-filed blocker type maps onto an existing inbox state so it renders in
# a known group: a question/decision needs an answer; a command/access is blocked.
_HUMAN_BLOCKER_STATE = {
    "ask": "needs-answer",
    "decide": "needs-answer",
    "run": "blocked",
    "provision": "blocked",
}


def attention_items(
    repos, sessions, antigravity, stale_days, drain_window=DRAIN_WINDOW_DEFAULT
):
    """The inbox: everything that needs a human decision, most severe first.

    severity: critical > serious > warning  (rendered with icon + word, never
    color alone). Items owned by a live session/drain carry state
    `in-progress` / category `active` and are grouped/counted separately."""
    items = []
    active_toplevels = {
        s.get("toplevel")
        for s in sessions
        if s.get("state") == "active" and s.get("toplevel")
    }

    for r in repos:
        rp = r["path"]
        covered_by_active = _actively_covered(rp, r, active_toplevels, drain_window)
        for h in r["handoffs"]:
            resume_prompt = (
                f"Resume the parked handoff in {h['path']}; "
                "delete the file once fully resumed"
            )
            items.append(
                {
                    "severity": "serious",
                    "state": "blocked",
                    "repo": r["name"],
                    "what": f"Handoff parked: {h['title']}",
                    "why": f"{h['path']} — resume it in a fresh session, then delete the file (/handoff wrote it):",
                    "cmd": f"cd {shlex.quote(rp)} && claude {shlex.quote(resume_prompt)}",
                    "age_ts": h["mtime"],
                }
            )
        # Human-filed blockers (HUMAN.md) rank above spec/task rows: a person
        # asked for these explicitly. Serious severity, filed before the specs
        # loop so they lead the repo's items within the same severity band.
        for hb in r.get("human_blockers", []):
            items.append(
                {
                    "severity": "serious",
                    "state": _HUMAN_BLOCKER_STATE.get(hb["type"], "needs-answer"),
                    "repo": r["name"],
                    "what": f"Human blocker ({hb['type']}): {hb['ask']}",
                    "why": f"filed {hb['date']} · {hb['source']} — see HUMAN.md",
                    "age_ts": _iso_date_ts(hb["date"]),
                }
            )
        for s in r["specs"]:
            open_tasks = s["tasks_total"] - s["tasks_done"]
            # Needs-your-answer surfaces: ask-typed unblocks + deferred questions.
            # No dispatch cmd — these are human decisions only (R6).
            for t in s.get("tasks", []):
                ub = t.get("unblock")
                if ub and ub["type"] == "ask":
                    items.append(
                        {
                            "severity": "serious",
                            "state": "needs-answer",
                            "repo": r["name"],
                            "what": f"Answer needed: {t['title']}",
                            "why": ub["step"],
                            "unblock": ub,
                            "age_ts": s["last_touched"],
                        }
                    )
                for q in t.get("deferred_questions", []):
                    items.append(
                        {
                            "severity": "serious",
                            "state": "needs-answer",
                            "repo": r["name"],
                            "what": f"Deferred question: {t['title']}",
                            "why": q,
                            "deferred_questions": [q],
                            "age_ts": s["last_touched"],
                        }
                    )
            # A spec-level `Status: waiting` header (spec-only status): ask →
            # needs-answer; run/agent → agent-bounded, proceeds (R7 recheck owns
            # it), NOT an attention item; missing → unknown-bounded, surface.
            if s.get("status") == "waiting":
                ub = s.get("unblock")
                if ub and ub["type"] == "ask":
                    items.append(
                        {
                            "severity": "serious",
                            "state": "needs-answer",
                            "repo": r["name"],
                            "what": f"Answer needed: spec {s['slug']}",
                            "why": ub["step"],
                            "unblock": ub,
                            "age_ts": s["last_touched"],
                        }
                    )
                elif not ub:
                    items.append(
                        {
                            "severity": "serious",
                            "state": "blocked",
                            "repo": r["name"],
                            "what": f"Spec {s['slug']}: waiting",
                            "why": "no unblock step recorded — add an Unblock: line",
                            "unblock": None,
                            "unblock_missing": True,
                            "age_ts": s["last_touched"],
                        }
                    )
            # Inbox principle: agent-bounded work proceeds (drafts → intake,
            # run:/agent: unblocks → recheck/dispatch, done specs → verifier);
            # only human-bounded or unknown-bounded blockage is the human's
            # attention item. Ask-typed unblocks already have their own
            # needs-answer row above; the spec-level row covers only blocked
            # tasks with NO recorded unblock step.
            needs_human = [
                t
                for t in s.get("tasks", [])
                if _task_is_blocked(t["status"])
                and t["status"] != "draft"
                and not t.get("unblock")
            ]
            if needs_human:
                why = (
                    ", ".join(t["file"] for t in needs_human[:3])
                    + " — no unblock step recorded: answer its open question or"
                    " add an Unblock: line, flip its Status:, re-dispatch via"
                    " /build or /drain"
                )
                items.append(
                    {
                        "severity": "serious",
                        "state": "blocked",
                        "repo": r["name"],
                        "what": f"Spec {s['slug']}: task(s) blocked",
                        "why": why,
                        "unblock": None,
                        "unblock_missing": True,
                        "age_ts": s["last_touched"],
                    }
                )
            elif open_tasks > 0 and (now_ts() - s["last_touched"]) > stale_days * 86400:
                items.append(
                    {
                        "severity": "warning",
                        "state": "stale",
                        "repo": r["name"],
                        "what": f"Spec {s['slug']}: {open_tasks} open task(s), idle {age_str(s['last_touched'])}",
                        "why": "resume it, defer it (Status: deferred), or delete it — open work decays; deciding is the point",
                        "age_ts": s["last_touched"],
                    }
                )
        if r["git"]["dirty"]:
            if covered_by_active:
                items.append(
                    {
                        "severity": "warning",
                        "state": "in-progress",
                        "category": "active",
                        "repo": r["name"],
                        "what": f"{r['git']['dirty']} uncommitted change(s) — a live session/drain is working here",
                        "why": f"on branch {r['git']['branch']} — owned work-in-progress, not neglected",
                        "age_ts": r["git"]["last_commit_ts"],
                    }
                )
            else:
                items.append(
                    {
                        "severity": "warning",
                        "state": "needs-review",
                        "repo": r["name"],
                        "what": f"{r['git']['dirty']} uncommitted change(s), no live session",
                        "why": f"on branch {r['git']['branch']} — commit (then push) or stash; small focused commits",
                        "age_ts": r["git"]["last_commit_ts"],
                    }
                )
        if r["git"]["ahead"]:
            if covered_by_active:
                items.append(
                    {
                        "severity": "warning",
                        "state": "in-progress",
                        "category": "active",
                        "repo": r["name"],
                        "what": f"{r['git']['ahead']} unpushed commit(s) on {r['git']['branch']} — a live session/drain is working here",
                        "why": "owned work-in-progress — a live session/drain will push when it lands:",
                        "cmd": f"git -C {shlex.quote(rp)} push",
                        "age_ts": r["git"]["last_commit_ts"],
                    }
                )
            else:
                items.append(
                    {
                        "severity": "warning",
                        "state": "needs-review",
                        "repo": r["name"],
                        "what": f"{r['git']['ahead']} unpushed commit(s) on {r['git']['branch']}",
                        "why": "push or open a PR — local-only work is invisible work:",
                        "cmd": f"git -C {shlex.quote(rp)} push",
                        "age_ts": r["git"]["last_commit_ts"],
                    }
                )
        for b in r.get("batons", []):
            # A parked baton with a needs-attention section carries deferred
            # questions the human must answer; promote it into the inbox so it
            # ranks among blocked work, not just as a repo card (oc-06).
            if b.get("needs_attention"):
                gen = b["generation"] if b["generation"] is not None else "?"
                items.append(
                    {
                        "severity": "serious",
                        "state": "blocked",
                        "repo": r["name"],
                        "what": f"Drain baton (gen {gen}): needs attention",
                        "why": f"{b['needs_attention']} — answer it, then relaunch the parked generation:",
                        "cmd": b.get("command") or "",
                        "age_ts": b.get("mtime"),
                    }
                )
            # A baton whose relaunch command matched no known runtime shape
            # can't be relaunched from its card; promote the parse_warning into
            # the inbox the same way (R9) so it doesn't vanish silently.
            if b.get("parse_warning"):
                gen = b["generation"] if b["generation"] is not None else "?"
                items.append(
                    {
                        "severity": "warning",
                        "state": "needs-review",
                        "repo": r["name"],
                        "what": f"Drain baton (gen {gen}): unparsable relaunch command",
                        "why": f"{b['parse_warning']} — {b['path']}",
                        "cmd": "",
                        "age_ts": b.get("mtime"),
                    }
                )

    for c in antigravity:
        if c["open"] > 0 and (now_ts() - c["last_ts"]) > stale_days * 86400:
            items.append(
                {
                    "severity": "warning",
                    "state": "stale",
                    "repo": f"antigravity:{c['store']}",
                    "what": f"{c['open']} open checklist item(s): {c['summary'][:60]}",
                    "why": "stale Antigravity conversation — resume it, or abandon:",
                    "cmd": f"python3 {shlex.quote(str(SCRIPT))} --abandon {shlex.quote(c['id'])}",
                    "age_ts": c["last_ts"],
                }
            )

    sev_rank = {"critical": 0, "serious": 1, "warning": 2}
    items.sort(key=lambda i: (sev_rank.get(i["severity"], 3), -(i["age_ts"] or 0)))
    return items


def _attach_sessions(repos, sessions):
    """Attach each session to the repo whose path it's under, matching on
    realpath (R2: a session cwd that's a symlink into a repo still
    attributes to it). Mutates repos in place with a "sessions" list;
    returns the set of matched session ids."""
    real_cwds = {s["id"]: os.path.realpath(s["cwd"]) for s in sessions if s["cwd"]}
    for r in repos:
        r_real = os.path.realpath(r["path"])
        r["sessions"] = [
            s
            for s in sessions
            if s["id"] in real_cwds
            and (
                real_cwds[s["id"]] == r_real
                or real_cwds[s["id"]].startswith(r_real + os.sep)
            )
        ]
    return {s["id"] for r in repos for s in r["sessions"]}


SPEND_TIMEOUT_SEC = 30
_SPEND_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
)


def _locate_agentprof():
    """agentprof binary lookup order (R5): $AGENTPROF_BIN, then `agentprof`
    on PATH, then the committed toolkit binary."""
    return (
        os.environ.get("AGENTPROF_BIN")
        or shutil.which("agentprof")
        or str(Path.home() / "claude/agentprof/agentprof")
    )


def _unavailable_spend(reason):
    return {"by_model": [], "by_session": {}, "available": False, "reason": reason}


def _new_model_agg():
    agg = {field: 0 for field in _SPEND_TOKEN_FIELDS}
    agg["cost_microusd"] = 0
    agg["priced"] = False
    return agg


def _run_spend(argv, id_set):
    """Shell out to agentprof and join its per-(session, model) summary rows to
    the ids in `id_set`. Shared by the Claude and Antigravity spend calls, which
    differ only in `argv` (subcommand + directory flag) and the id-space they
    filter against. Any failure — missing binary, timeout, non-zero exit,
    invalid JSON — degrades to an unavailable structure with a `reason` rather
    than raising, so the dashboard never breaks (R8)."""
    binary = argv[0]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=SPEND_TIMEOUT_SEC,
        )
    except FileNotFoundError:
        return _unavailable_spend(f"agentprof not found: {binary}")
    except subprocess.TimeoutExpired:
        return _unavailable_spend(f"agentprof timed out after {SPEND_TIMEOUT_SEC}s")
    except OSError as e:
        return _unavailable_spend(f"agentprof failed to run: {e}")

    if proc.returncode != 0:
        detail = (proc.stderr or "").strip().splitlines()
        return _unavailable_spend(
            f"agentprof exited {proc.returncode}" + (f": {detail[0]}" if detail else "")
        )
    try:
        rows = json.loads(proc.stdout)
    except (ValueError, TypeError):
        return _unavailable_spend("agentprof emitted invalid JSON")
    if not isinstance(rows, list):
        return _unavailable_spend("agentprof emitted invalid JSON")

    by_session = {}
    by_model = {}
    for row in rows:
        sid = row.get("session")
        if sid not in id_set:
            continue
        model = row.get("model")
        cost = int(row.get("cost_microusd", 0))
        priced = bool(row.get("priced", False))

        sess = by_session.setdefault(sid, {"cost_microusd": 0, "models": {}})
        sess["cost_microusd"] += cost
        smodel = sess["models"].setdefault(model, _new_model_agg())
        agg = by_model.setdefault(model, _new_model_agg())
        for target in (smodel, agg):
            for field in _SPEND_TOKEN_FIELDS:
                target[field] += int(row.get(field, 0))
            target["cost_microusd"] += cost
            target["priced"] = target["priced"] or priced

    by_model_list = sorted(
        ({"model": model, **agg} for model, agg in by_model.items()),
        key=lambda m: (-m["cost_microusd"], m["model"]),
    )
    return {
        "by_model": by_model_list,
        "by_session": by_session,
        "available": True,
        "reason": None,
    }


def compute_spend(claude_home, session_ids):
    """Shell out to `agentprof claude` and join its per-(session, model) summary
    rows to the Claude sessions workboard assembled (R5/R8)."""
    binary = _locate_agentprof()
    argv = [
        binary,
        "claude",
        "-o",
        "summary",
        "--days",
        "3650",
        "--claude-dir",
        str(claude_home),
    ]
    return _run_spend(argv, session_ids)


def compute_antigravity_spend(antigravity_dir, cascade_ids):
    """Shell out to `agentprof antigravity` and join its per-(session, model)
    summary rows to the Antigravity cascade ids workboard assembled (R4). The
    id-space here is the cascade-conversation ids — filtering against the
    Claude-only `session_ids` would silently zero every Antigravity row out,
    which is the id-space bug R4 exists to fix."""
    binary = _locate_agentprof()
    argv = [
        binary,
        "antigravity",
        "-o",
        "summary",
        "--antigravity-dir",
        str(antigravity_dir),
        "--days",
        "3650",
    ]
    return _run_spend(argv, cascade_ids)


def merge_spend(claude_spend, antigravity_spend):
    """Merge two harness spend structures into one drop-in replacement for what
    `compute_spend` returns (R4), so downstream consumers of the --json spend
    payload (agent-console's spend view) need no changes.

    `by_model` is the concatenation of both harnesses' lists, RE-SORTED by
    `(-cost_microusd, model)` (not two separately-sorted blocks). `by_session`
    is the union of both dicts (cascade ids and Claude session ids are disjoint
    UUID spaces, so no key collision). Top-level `available` is the OR of the
    two harnesses. Per-harness availability is preserved under
    `claude_available`/`claude_reason` and
    `antigravity_available`/`antigravity_reason`, so a failure in one harness
    never blanks out the rows the other already populated."""
    c_avail = bool(claude_spend.get("available"))
    a_avail = bool(antigravity_spend.get("available"))
    by_model = sorted(
        list(claude_spend.get("by_model") or [])
        + list(antigravity_spend.get("by_model") or []),
        key=lambda m: (-m["cost_microusd"], m["model"]),
    )
    by_session = {
        **(claude_spend.get("by_session") or {}),
        **(antigravity_spend.get("by_session") or {}),
    }
    available = c_avail or a_avail
    reason = None
    if not available:
        reasons = [
            r
            for r in (claude_spend.get("reason"), antigravity_spend.get("reason"))
            if r
        ]
        reason = "; ".join(reasons) if reasons else None
    return {
        "by_model": by_model,
        "by_session": by_session,
        "available": available,
        "reason": reason,
        "claude_available": c_avail,
        "claude_reason": claude_spend.get("reason"),
        "antigravity_available": a_avail,
        "antigravity_reason": antigravity_spend.get("reason"),
    }


def default_claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))


def default_antigravity_dir():
    """Antigravity CLI conversation-database directory — mirrors the agentprof
    binary's own `defaultAntigravityDir` (`$HOME/.gemini/antigravity-cli`), so
    the workboard and the binary agree on where the cascade DBs live."""
    return Path(
        os.environ.get("ANTIGRAVITY_DIR", Path.home() / ".gemini" / "antigravity-cli")
    )


def assemble(roots, max_depth, stale_days, quiet, drain_window=DRAIN_WINDOW_DEFAULT):
    claude_home = default_claude_home()
    sessions = scan_sessions(claude_home, stale_days)

    # attach each session's agent spawn tree (SPEC.md R5/R8) — scan_session_spawns()
    # is a separate read-only scan, so no other scan_*() output shape changes.
    spawns = scan_session_spawns(claude_home)
    for s in sessions:
        s["spawn_tree"] = spawns.get(s["id"], {}).get("spawn_tree", [])

    # every repo a session touched joins the scan set; the git toplevel is
    # attached to each session so attention_items() can test toplevel EQUALITY
    # for human coverage (not the old path-prefix, which over-matched parents).
    session_dirs = []
    for s in sessions:
        s["toplevel"] = None
        if s["cwd"] and Path(s["cwd"]).is_dir():
            top = run_git(s["cwd"], "rev-parse", "--show-toplevel")
            if top:
                s["toplevel"] = top
                session_dirs.append(Path(top))

    repo_paths = sorted(
        {str(p) for p in list(find_repos(roots, max_depth)) + session_dirs}
    )
    repos = []
    for rp in repo_paths:
        p = Path(rp)
        if not quiet:
            print(f"  scanning {rp}", file=sys.stderr)
        repos.append(
            {
                "path": rp,
                "name": p.name,
                "git": git_info(p),
                "specs": scan_toolkit_specs(p) + scan_kiro_specs(p),
                "handoffs": scan_handoffs(p),
                "batons": scan_batons(p),
                "human_blockers": scan_human_blockers(p),
            }
        )

    matched = _attach_sessions(repos, sessions)
    orphan_sessions = [s for s in sessions if s["id"] not in matched]

    antigravity = scan_antigravity()
    todos = scan_todos(claude_home)
    inbox = attention_items(repos, sessions, antigravity, stale_days, drain_window)
    ready = ready_items(repos)

    return {
        "generated_at": datetime.now(timezone.utc)
        .astimezone()
        .isoformat(timespec="seconds"),
        "stale_days": stale_days,
        "repos": repos,
        "sessions": sessions,
        "orphan_sessions": orphan_sessions,
        "antigravity": antigravity,
        "todos": todos,
        "inbox": inbox,
        "ready": ready,
        "spend": merge_spend(
            compute_spend(claude_home, {s["id"] for s in sessions}),
            compute_antigravity_spend(
                default_antigravity_dir(), {c["id"] for c in antigravity}
            ),
        ),
        "liveness_unknown": _last_liveness_unknown,
        "totals": {
            "repos": len(repos),
            "specs_open": sum(
                1
                for r in repos
                for s in r["specs"]
                if s["tasks_total"] == 0 or s["tasks_done"] < s["tasks_total"]
            ),
            "tasks_open": sum(
                s["tasks_total"] - s["tasks_done"] for r in repos for s in r["specs"]
            ),
            "sessions_active": sum(1 for s in sessions if s["state"] == "active"),
            "attention": attention_total(inbox),
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Cross-repo agent/spec/session workboard")
    ap.add_argument("roots", nargs="*", help="directories to scan for git repos")
    ap.add_argument("--json", action="store_true", help="print JSON to stdout instead")
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS_DEFAULT)
    ap.add_argument(
        "--drain-window-min",
        type=int,
        default=DRAIN_WINDOW_DEFAULT // 60,
        help="a task/* worktree counts as a live drain only if its "
        "newest activity is within this many minutes (default 15)",
    )
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument(
        "--abandon",
        nargs="+",
        metavar="CONV_ID",
        default=[],
        help="mark Antigravity conversation(s) abandoned (skip-marker only), then rescan",
    )
    ap.add_argument(
        "--abandon-stale",
        action="store_true",
        help="abandon every stale Antigravity conversation, then rescan",
    )
    ap.add_argument(
        "--prune-stale-sessions",
        action="store_true",
        help="delete ~/.claude/sessions/*.json records whose pid is dead, then rescan",
    )
    args = ap.parse_args()

    if args.abandon:
        marked, missing = abandon_conversations(args.abandon)
        for cid in marked:
            print(f"abandoned: {cid}", file=sys.stderr)
        for cid in missing:
            print(f"not found: {cid}", file=sys.stderr)
        if missing:
            sys.exit(1)
    if args.abandon_stale:
        for cid in abandon_stale(args.stale_days):
            print(f"abandoned (stale): {cid}", file=sys.stderr)
    if args.prune_stale_sessions:
        removed, kept = prune_stale_session_pids(default_claude_home())
        for sid in removed:
            print(f"pruned dead-pid session record: {sid}", file=sys.stderr)
        print(f"pruned {len(removed)}, kept {kept}", file=sys.stderr)

    roots = [Path(r) for r in args.roots] if args.roots else default_roots()
    data = assemble(
        roots, args.max_depth, args.stale_days, args.quiet, args.drain_window_min * 60
    )

    if args.json:
        json.dump(data, sys.stdout, indent=2, default=str)
        print()
        return

    t = data["totals"]
    print(
        f"workboard: {t['repos']} repos · {t['specs_open']} open specs · "
        f"{t['tasks_open']} open tasks · {t['sessions_active']} active sessions · "
        f"{t['attention']} need attention"
    )


if __name__ == "__main__":
    main()
