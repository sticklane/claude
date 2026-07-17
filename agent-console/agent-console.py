#!/usr/bin/env python3
"""Agent Console — a local, zero-LLM dashboard for this machine's Claude setup.

Two views, served by one pure-Python stdlib HTTP server (no network calls to
Claude or anything else, so it costs nothing to run):

  /            Skills   — every installed agent skill & subagent (personal,
                          project, plugin, and best-effort session built-ins).
  /workboard   Workboard — open work across all repos: specs, tasks, handoffs,
                          git state, and Claude Code sessions, with a
                          needs-attention inbox up top.

Each request re-scans on demand (workboard git state is cached briefly), so the
views are always current. Run:  skills-dashboard.py
Env: SKILLS_DASHBOARD_PORT (8899), SKILLS_DASHBOARD_HOST (127.0.0.1)
"""

from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

HOME = Path.home()
PORT = int(os.environ.get("SKILLS_DASHBOARD_PORT", "8899"))
HOST = os.environ.get("SKILLS_DASHBOARD_HOST", "127.0.0.1")


def _skills_root() -> Path:
    """`.claude/skills/` for this checkout, derived from this file's own
    location (`<repo>/agent-console/agent-console.py` -> `<repo>/.claude/skills`).
    `AGENT_CONSOLE_SKILLS_ROOT` overrides it for a non-checkout layout."""
    env = os.environ.get("AGENT_CONSOLE_SKILLS_ROOT")
    if env:
        return Path(os.path.expanduser(env))
    return Path(__file__).resolve().parent.parent / ".claude" / "skills"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SKILLS_ROOT = _skills_root()
viz = _load_module("viz", SKILLS_ROOT / "_shared" / "viz.py")  # import viz.py
# import workboard.py (assemble()/attention_items()/ready_items() — R4)
workboard = _load_module("workboard", SKILLS_ROOT / "workboard" / "workboard.py")

PID_DIR = HOME / ".claude" / "sessions"
REPOS_MD = Path(os.environ.get("AGENT_CONSOLE_REPOS", str(HOME / "REPOS.md")))


def _is_plugin_source(repo: Path) -> bool:
    """A repo that is the SOURCE of a Claude Code plugin — its `.claude/skills`
    are the dev versions of skills you'd normally use via the installed plugin."""
    d = repo / ".claude-plugin"
    return (d / "plugin.json").exists() or (d / "marketplace.json").exists()


def project_roots() -> list[Path]:
    """Repos that contribute project-scoped skills/agents — discovered, not
    hardcoded. Env override `AGENT_CONSOLE_PROJECT_ROOTS` (os.pathsep list).

    Otherwise every tracked repo (+ cwd) with a `.claude/` dir, EXCEPT a
    plugin-source repo, whose dev-source skills would just duplicate the
    installed plugin — those show only when a session is actively working in
    that repo (i.e. you're modifying the plugin)."""
    env = os.environ.get("AGENT_CONSOLE_PROJECT_ROOTS")
    if env:
        return [Path(os.path.expanduser(p)) for p in env.split(os.pathsep) if p]
    active = active_repo_reals()
    roots, seen = [], set()
    for r in parse_repos() + [Path.cwd()]:
        if r in seen or not (r / ".claude").is_dir():
            continue
        seen.add(r)
        if _is_plugin_source(r) and os.path.realpath(str(r)) not in active:
            continue  # using the plugin, not modifying its repo → skip the source copy
        roots.append(r)
    return roots


STALE_DAYS = 7
GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}


# --------------------------------------------------------------------------- #
# Frontmatter + skill/agent collection
# --------------------------------------------------------------------------- #
def _parse_frontmatter(text: str) -> dict:
    """Flat key: value pairs from a leading `---` YAML block (scalars only)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    key, buf = None, []

    def flush():
        nonlocal key, buf
        if key is not None:
            data[key] = " ".join(p.strip() for p in buf).strip().strip("\"'")
        key, buf = None, []

    for line in text[3:end].splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s?(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            flush()
            key, val = m.group(1), m.group(2)
            buf = [val] if val else []
        else:
            buf.append(line)
    flush()
    return data


def _read(md_path: Path, name_fallback: str, kind: str = "skill") -> dict | None:
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
        mtime = md_path.stat().st_mtime
    except OSError:
        return None  # file vanished mid-scan (repos are edited live) — skip it
    fm = _parse_frontmatter(text)
    return {
        "name": fm.get("name") or name_fallback,
        "description": fm.get("description", ""),
        "model": fm.get("model", ""),
        "kind": kind,
        "path": str(md_path),
        "mtime": mtime,
    }


def _claude_json(*args):
    """Run `claude <args> --json` and parse it. Returns None on any failure
    (binary missing, non-zero exit, timeout, bad JSON) so callers can fall back
    to reading internal files. `claude` is the supported, stable surface;
    the file scrapers below are the offline/older-version fallback."""
    claude = shutil.which("claude")
    if not claude:
        return None
    try:
        r = subprocess.run(
            [claude, *args, "--json"],
            capture_output=True,
            text=True,
            timeout=8,
            env=GIT_ENV,
        )
        if r.returncode == 0:
            return json.loads(r.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
        pass
    return None


def plugin_paths_from_cli(data) -> list[tuple[str, Path]] | None:
    """Parse `claude plugin list --json` into (label, installPath), keeping only
    ENABLED plugins. Returns None if the input isn't the expected shape."""
    if not isinstance(data, list):
        return None
    out: list[tuple[str, Path]] = []
    for p in data:
        if not isinstance(p, dict) or not p.get("enabled"):
            continue  # skip disabled plugins — their skills are not active
        ip, label = p.get("installPath"), str(p.get("id", "")).split("@", 1)[0]
        if ip and label and Path(ip).is_dir():
            out.append((label, Path(ip)))
    return out


def _plugin_paths_from_manifest() -> list[tuple[str, Path]]:
    """Fallback: read the internal manifest (no enabled state — may include
    disabled plugins). Used only when the `claude` CLI is unavailable."""
    out: list[tuple[str, Path]] = []
    try:
        data = json.loads((HOME / ".claude/plugins/installed_plugins.json").read_text())
    except (OSError, json.JSONDecodeError):
        return out
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return out
    for key, installs in plugins.items():
        if not isinstance(installs, list):
            continue
        label = str(key).split("@", 1)[0]
        for inst in installs:
            p = inst.get("installPath") if isinstance(inst, dict) else None
            if p and Path(p).is_dir():
                out.append((label, Path(p)))
    return out


_plugins_cache: dict = {"ts": 0.0, "data": None}


def _plugin_paths() -> list[tuple[str, Path]]:
    """Enabled plugins as (label, installPath). Prefers `claude plugin list
    --json` (supported, carries enabled state); falls back to the internal
    manifest. Cached 60s so the un-cached Skills view doesn't spawn `claude`
    on every 25s refresh."""
    if _plugins_cache["data"] is not None and time.time() - _plugins_cache["ts"] < 60:
        return _plugins_cache["data"]
    out = plugin_paths_from_cli(_claude_json("plugin", "list"))
    if out is None:
        out = _plugin_paths_from_manifest()
    _plugins_cache.update(ts=time.time(), data=out)
    return out


def collect() -> dict:
    groups: dict[str, list[dict]] = {}
    agents: dict[str, list[dict]] = {}
    seen_s: set[tuple[str, str]] = set()
    seen_a: set[tuple[str, str]] = set()

    def add(bucket, seen, source, rec):
        if not rec or not rec.get("name"):
            return
        k = (source, rec["name"])
        if k in seen:
            return
        seen.add(k)
        bucket.setdefault(source, []).append(rec)

    def scan_skills(source: str, root: Path, kind: str = "skill"):
        # A skill is exactly <root>/<name>/SKILL.md, one level deep. scandir
        # follows symlinks (personal skills are symlinked from their repos) and
        # never descends into worktrees/node_modules the way os.walk would.
        try:
            children = sorted(os.scandir(root), key=lambda e: e.name)
        except (OSError, NotADirectoryError):
            return
        for child in children:
            md = Path(child.path) / "SKILL.md"
            if md.exists():
                add(groups, seen_s, source, _read(md, Path(child.path).name, kind))

    def scan_flat(bucket, seen, source: str, root: Path, kind: str):
        # Agents (<root>/<name>.md) and commands (<root>/<name>.md); the name
        # falls back to the file stem, never the parent dir "agents"/"commands".
        try:
            children = sorted(os.scandir(root), key=lambda e: e.name)
        except (OSError, NotADirectoryError):
            return
        for child in children:
            if (
                child.name.endswith(".md")
                and child.name != "README.md"
                and child.is_file()
            ):
                add(
                    bucket,
                    seen,
                    source,
                    _read(Path(child.path), Path(child.name).stem, kind),
                )

    # Personal
    scan_skills("personal", HOME / ".claude" / "skills")
    scan_flat(agents, seen_a, "personal", HOME / ".claude" / "agents", "agent")

    # Projects — discovered dynamically (no hardcoded repo), canonical dirs only
    for root in project_roots():
        src = f"project:{root.name}"
        scan_skills(src, root / ".claude" / "skills")
        scan_flat(agents, seen_a, src, root / ".claude" / "agents", "agent")

    # Plugins — skills, commands, and agents at <base> or <base>/.claude
    for label, base in _plugin_paths():
        src = f"plugin:{label}"
        for sub in ("", ".claude"):
            scan_skills(src, base / sub / "skills")
            scan_flat(groups, seen_s, src, base / sub / "commands", "command")
            scan_flat(agents, seen_a, src, base / sub / "agents", "agent")

    for lst in list(groups.values()) + list(agents.values()):
        lst.sort(key=lambda r: r["name"].lower())

    return {
        "groups": groups,
        "agents": agents,
        "total_skills": sum(len(v) for v in groups.values()),
        "total_agents": sum(len(v) for v in agents.values()),
    }


# --------------------------------------------------------------------------- #
# Workboard collection
# --------------------------------------------------------------------------- #
BOARD_TTL = 45  # seconds; kept above the 25s client refresh so it serves cache
ACTION_TIMEOUT = 60  # seconds; hard cap on any single action's subprocess
_board_cache: dict = {
    "ts": 0.0,
    "data": None,
    "registry": None,
    "pages": None,
    "actions": None,
}
_board_lock = threading.Lock()
# GitHub repo visibility (public/private), fetched once via `gh` and cached long
# — this is the only part of the tool that touches the network.
_GH_TTL = 1800
_gh_cache: dict = {"ts": 0.0, "map": None}


def gh_visibility() -> dict:
    """{ 'owner/repo'(lower): 'public'|'private' } from one `gh repo list` call.
    Best-effort: returns the last-known map (possibly empty) if gh is missing,
    unauthenticated, or offline. Never raises."""
    fresh = _gh_cache["map"] is not None and time.time() - _gh_cache["ts"] < _GH_TTL
    if fresh:
        return _gh_cache["map"]
    gh = shutil.which("gh")
    if not gh:
        _gh_cache.update(ts=time.time(), map=_gh_cache["map"] or {})
        return _gh_cache["map"]
    m = dict(_gh_cache["map"] or {})
    try:
        r = subprocess.run(
            [
                gh,
                "repo",
                "list",
                "--json",
                "nameWithOwner,visibility",
                "--limit",
                "500",
            ],
            capture_output=True,
            text=True,
            timeout=12,
            env=GIT_ENV,
        )
        if r.returncode == 0:
            for e in json.loads(r.stdout):
                if isinstance(e, dict) and e.get("nameWithOwner"):
                    m[e["nameWithOwner"].lower()] = (e.get("visibility") or "").lower()
            _gh_cache.update(ts=time.time(), map=m)  # only advance TTL on success
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
        pass
    return m


def _git(repo: Path, *args, timeout=4) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            env=GIT_ENV,
            timeout=timeout,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def parse_repos() -> list[Path]:
    """Repo local paths from the REPOS.md table (`| ~/path | ... |`). Source
    file is `AGENT_CONSOLE_REPOS` or `~/REPOS.md`; nothing hardcoded."""
    repos: list[Path] = []
    try:
        lines = REPOS_MD.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        m = re.match(r"^\|\s*(~[^|]*?)\s*\|", line)
        if m:
            repos.append(Path(os.path.expanduser(m.group(1))))
    seen, out = set(), []
    for r in repos:
        if r not in seen and r.is_dir():
            seen.add(r)
            out.append(r)
    return out


PRIORITIES = ["P0", "P1", "P2", "P3"]  # highest → lowest; "" = unset


def _gh_slug(origin: str | None) -> str:
    """github.com owner/repo from a remote URL (https or ssh), else ""."""
    if not origin:
        return ""
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", origin.strip())
    return m.group(1) if m else ""


def _repo_extras(path: str, vis: dict) -> tuple[dict, dict]:
    """Best-effort data workboard.py's scan doesn't carry: the latest commit's
    hash/subject/ts and GitHub visibility, via a couple of extra `git` calls
    per repo (mirrors the pre-migration git_state())."""
    repo = Path(path)
    extra: dict = {}
    log = _git(repo, "log", "-1", "--format=%h%x00%cI%x00%s")
    if log and "\x00" in log:
        h, ci, subj = log.split("\x00", 2)
        extra.update(hash=h, commit_ts=_iso(ci), commit_subject=subj)
    slug = _gh_slug(_git(repo, "remote", "get-url", "origin"))
    gh = {
        "slug": slug,
        "visibility": vis.get(slug.lower(), "") if slug else "",
        "url": f"https://github.com/{slug}" if slug else "",
    }
    return extra, gh


def _iso(s) -> float:
    # PID records store epoch-milliseconds as ints; sessions-index stores ISO
    # strings. Accept both, returning epoch-seconds.
    if isinstance(s, (int, float)):
        return s / 1000.0 if s > 1e11 else float(s)
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return 0.0


def live_sessions_from_cli(data) -> list[dict] | None:
    """Parse `claude agents --json` into live-session dicts. Returns None if the
    input isn't the expected shape."""
    if not isinstance(data, list):
        return None
    out = []
    for e in data:
        if not isinstance(e, dict) or not e.get("sessionId"):
            continue
        out.append(
            {
                "sid": e["sessionId"],
                "cwd": e.get("cwd") or "",
                "name": (e.get("name") or "").strip(),
                "last": _iso(e.get("updatedAt"))
                or _iso(e.get("startedAt"))
                or time.time(),
            }
        )
    return out


def _live_sessions_from_pids() -> list[dict]:
    """Fallback: read the internal PID records and probe liveness with os.kill.
    Used only when the `claude` CLI is unavailable."""
    out = []
    try:
        files = list(PID_DIR.glob("*.json"))
    except OSError:
        return out
    for f in files:
        try:
            rec = json.loads(f.read_text())
            pid, sid = rec.get("pid"), rec.get("sessionId")
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
        if not (isinstance(pid, int) and sid):
            continue
        try:
            os.kill(pid, 0)
        except OSError:
            continue
        out.append(
            {
                "sid": sid,
                "cwd": rec.get("cwd") or "",
                "name": (rec.get("name") or "").strip(),
                "last": _iso(rec.get("updatedAt"))
                or _iso(rec.get("startedAt"))
                or time.time(),
            }
        )
    return out


def live_sessions() -> list[dict]:
    """Currently-running sessions. Prefers `claude agents --json` (supported,
    stable surface); falls back to scraping the internal PID records."""
    out = live_sessions_from_cli(_claude_json("agents"))
    if out is None:
        out = _live_sessions_from_pids()
    return out


_active_cache: dict = {"ts": 0.0, "data": None}


def active_repo_reals() -> set[str]:
    """realpath of tracked repos that currently have an active session working
    in them. Cached ~20s so the un-cached Skills view doesn't spawn `claude`
    on every refresh."""
    if _active_cache["data"] is not None and time.time() - _active_cache["ts"] < 20:
        return _active_cache["data"]
    reals = _tracked_repo_reals()
    out = set()
    for s in live_sessions():
        cwd = os.path.realpath(s.get("cwd") or "")
        best = ""
        for r in reals:
            if cwd == r or cwd.startswith(r + os.sep):
                best = r if len(r) > len(best) else best
        if best:
            out.add(best)
    _active_cache.update(ts=time.time(), data=out)
    return out


def agents_view():
    """(running, resumable) full agent records for the control UI. running →
    Stop targets; resumable → recent completed sessions to Resume."""

    def norm(e):
        return {
            "pid": e.get("pid"),
            "sid": e.get("sessionId", ""),
            "name": (e.get("name") or "").strip(),
            "cwd": e.get("cwd") or "",
            "status": (e.get("status") or e.get("state") or "").strip(),
            "kind": e.get("kind") or "",
            "started": _iso(e.get("startedAt")),
        }

    active = _claude_json("agents")
    allrec = _claude_json("agents", "--all")
    if not isinstance(active, list):
        return [], []
    running = [norm(e) for e in active if isinstance(e, dict) and e.get("sessionId")]
    running_sids = {r["sid"] for r in running}
    resumable = []
    if isinstance(allrec, list):
        for e in allrec:
            if (
                isinstance(e, dict)
                and e.get("sessionId")
                and e["sessionId"] not in running_sids
            ):
                resumable.append(norm(e))
        resumable.sort(key=lambda a: a["started"], reverse=True)
    return running, resumable[:12]


def _running_pid_for(sid: str):
    """Live pid for a running session id, or None. Best-effort — a failed
    `claude agents` probe never breaks the session page."""
    if not sid:
        return None
    try:
        running, _ = agents_view()
    except Exception:
        return None
    for a in running:
        if a.get("sid") == sid and a.get("pid"):
            return a["pid"]
    return None


_TASK_NUM_RE = re.compile(r"^(\d+)")


def _dag_tasks(spec_tasks: list[dict]) -> list[dict]:
    """spec['tasks'] (workboard's {file, abs, title, status, deps} shape) into
    viz.dag()'s {num, deps, status, title} schema. `num` is the task file's
    leading NN- prefix; a dep is kept only when it parses as a bare number —
    workboard's richer path/glob dep forms aren't resolved here, matching
    dag()'s own behavior of dropping an edge it can't place."""
    out = []
    for t in spec_tasks:
        m = _TASK_NUM_RE.match(Path(t["file"]).name)
        if not m:
            continue
        deps = []
        for raw in t.get("deps") or []:
            dm = re.search(r"\d+", raw)
            if dm:
                deps.append(int(dm.group(0)))
        entry = {
            "num": int(m.group(1)),
            "deps": deps,
            "status": t["status"],
            "title": t["title"],
        }
        # Blocker kind for viz.dag()'s badge: blocked/failed tasks are
        # human-bounded (no unblock step, or an ask-typed one) unless they
        # record an agent-runnable Unblock: run/agent recheck.
        if viz.canonical_status(t["status"]) in ("blocked", "failed"):
            ub = (t.get("unblock") or {}).get("type")
            entry["blocker"] = "agent" if ub in ("run", "agent") else "human"
        out.append(entry)
    return out


# Finer partitions of workboard's OPEN_TASK_STATUSES for the board's three
# open columns; membership in the open/closed sets themselves is checked
# against workboard's own constants, never re-listed here.
_KANBAN_IN_PROGRESS = {"in-progress", "in_progress", "claimed"}
_KANBAN_NEEDS_VERIFICATION = {"needs-verification", "needs_verification"}


def _kanban_column(status: str) -> str:
    """Canonicalize a raw task `Status:` value into one of the board's seven
    fixed columns (SPEC.md R2). Reuses workboard's OPEN/CLOSED status sets for
    the open-vs-closed-vs-other split; any status in neither set is the same
    catch-all workboard uses, rendered in the single Blocked column."""
    s = (status or "").strip().lower()
    if s in workboard.CLOSED_TASK_STATUSES:
        return s.capitalize()  # done→Done, deferred→Deferred, skipped→Skipped
    if s not in workboard.OPEN_TASK_STATUSES:
        return "Blocked"
    if s in _KANBAN_IN_PROGRESS:
        return "In Progress"
    if s in _KANBAN_NEEDS_VERIFICATION:
        return "Needs Verification"
    return "Pending"


def _adapt_board(assembled: dict, running_agents: list, resumable_agents: list) -> dict:
    """Map workboard.assemble()'s result (`{repos, sessions, inbox, ready,
    totals, ...}` — workboard.py is the single source of scan/inbox logic
    per R4) to the board dict render_workboard consumes. The only translation
    layer this migration adds; render_workboard itself is unchanged."""
    vis = gh_visibility()
    board_repos: list[dict] = []
    open_spec_list: list[dict] = []
    active_list: list[dict] = []
    open_specs = 0
    open_tasks = 0

    for r in assembled["repos"]:
        extra, gh = _repo_extras(r["path"], vis)
        git = {
            "branch": r["git"]["branch"],
            "dirty": r["git"]["dirty"],
            "ahead": r["git"]["ahead"],
            "behind": r["git"]["behind"],
            **extra,
        }
        specs = []
        for sp in r["specs"]:
            done, total = sp.get("tasks_done", 0), sp.get("tasks_total", 0)
            if total and done < total:
                open_specs += 1
                open_tasks += total - done
                open_spec_list.append(
                    {
                        "repo": r["name"],
                        "title": sp["title"],
                        "slug": sp["slug"],
                        "done": done,
                        "total": total,
                        "mtime": sp["last_touched"],
                    }
                )
            spec_path = sp.get("path", "")
            specs.append(
                {
                    "id": _entity_id("spec", _spec_dir(r["path"], spec_path))
                    if spec_path
                    else "",
                    "slug": sp["slug"],
                    "title": sp["title"],
                    "status": None,
                    "priority": sp.get("priority", ""),
                    "path": str(Path(r["path"]) / spec_path) if spec_path else "",
                    "done": done,
                    "total": total,
                    "tasks": _dag_tasks(sp.get("tasks", [])),
                    # Forward the scanner's waiting-spec header unblock and any
                    # blocked task files' unblock steps (each task carries an
                    # absolute path) so build_action_registry can generate the
                    # unblock/recheck dispatch kinds (unblock-next-steps R7).
                    "unblock": sp.get("unblock"),
                    "blocked_tasks": [
                        {
                            "path": t.get("abs") or "",
                            "title": t.get("title") or "",
                            "unblock": t.get("unblock"),
                        }
                        for t in sp.get("tasks", [])
                        if t.get("unblock")
                    ],
                    "mtime": sp["last_touched"],
                }
            )
        sessions = [
            {
                "state": s["state"],
                "prompt": s["prompt"],
                "branch": s["branch"],
                "last": s["last_ts"],
                "start_ts": s["start_ts"],
                "sid": s["id"],
            }
            for s in r.get("sessions", [])
        ]
        for s in sessions:
            if s["state"] == "active":
                active_list.append(
                    {
                        "repo": r["name"],
                        "prompt": s["prompt"],
                        "branch": s["branch"],
                        "last": s["last"],
                    }
                )
        board_repos.append(
            {
                "id": _entity_id("repo", r["path"]),
                "name": r["name"],
                "path": r["path"],  # the -C target for a push action's argv
                "git": git,
                "gh": gh,
                "specs": specs,
                "tasks": None,  # docs/TASKS.md tracking retired with scan_tasks
                "handoffs": [
                    {
                        "title": h["title"],
                        "path": h["path"],
                        "mtime": h["mtime"],
                        "id": _entity_id("file", _abs_under(r["path"], h["path"]))
                        if h.get("path")
                        else "",
                    }
                    for h in r["handoffs"]
                ],
                "sessions": sessions,
            }
        )

    inbox = [
        {
            "sev": i["severity"],
            "state": i["state"],
            "item": i["what"],
            "repo": i["repo"],
            "why": i["why"],
            "age": i.get("age_ts") or 0,
            "cmd": i.get("cmd", ""),
            # Forward task 01's unblock/deferred data when present; older scan
            # JSON omits both keys, so tolerate absence (R6, console side).
            "unblock": i.get("unblock"),
            "deferred_questions": i.get("deferred_questions") or [],
            # Structured missing-unblock flag from the scanner (task 06); older
            # scan JSON omits it, so default False.
            "unblock_missing": i.get("unblock_missing", False),
        }
        for i in assembled["inbox"]
    ]
    orphans = [
        {
            "state": s["state"],
            "prompt": s["prompt"],
            "repo": s["cwd"] or s["id"],
            "last": s["last_ts"],
        }
        for s in assembled["orphan_sessions"]
        if s["state"] in ("active", "recent")
    ]
    orphans.sort(key=lambda s: s["last"], reverse=True)
    open_spec_list.sort(key=lambda s: s["mtime"], reverse=True)

    # Source-health signal: liveness detection failing means active sessions
    # may misreport as idle — surface it rather than render a clean-empty
    # that reads as "no work" (agent-console/CLAUDE.md: fail loud on drift).
    health = []
    if assembled.get("liveness_unknown"):
        health.append(
            "session liveness could not be determined this scan — active "
            "sessions may show as idle"
        )

    return {
        "repos": board_repos,
        "inbox": inbox,
        "orphans": orphans,
        "open_specs": open_spec_list,
        "task_repos": [],  # docs/TASKS.md tracking retired with scan_tasks
        "actives": active_list,
        "agents": running_agents,
        "resumable": resumable_agents,
        "repo_names": [r["name"] for r in board_repos],
        "health": health,
        "n_repos": len(board_repos),
        "n_open_specs": open_specs,
        "n_open_tasks": open_tasks,
        "n_active": len(active_list),
    }


def get_board() -> dict:
    if _board_cache["data"] and time.time() - _board_cache["ts"] < BOARD_TTL:
        return _board_cache["data"]
    # Serialize rebuilds so concurrent requests (multiple tabs) don't each fan
    # out git/workboard scanning across every repo; the waiters get the
    # just-built cache.
    with _board_lock:
        if _board_cache["data"] and time.time() - _board_cache["ts"] < BOARD_TTL:
            return _board_cache["data"]
        assembled = workboard.assemble(
            workboard.default_roots(), max_depth=3, stale_days=STALE_DAYS, quiet=True
        )
        running_agents, resumable_agents = agents_view()
        data = _adapt_board(assembled, running_agents, resumable_agents)
        registry = build_entity_registry(assembled)
        pages = build_page_registry(assembled)
        actions = build_action_registry(data)
        _board_cache.update(
            ts=time.time(),
            data=data,
            registry=registry,
            pages=pages,
            actions=actions,
        )
        return data


# Detail-view id contract, shared with the workboard-actions queue: id =
# truncated hex sha256 of `kind + "\0" + canonical-target-path`, so it is
# stable across rescans of unchanged state and never derived from client input.
_ENTITY_ID_LEN = 16


def _entity_id(kind: str, target_path: str) -> str:
    canonical = os.path.realpath(target_path)
    digest = hashlib.sha256(f"{kind}\0{canonical}".encode("utf-8")).hexdigest()
    return digest[:_ENTITY_ID_LEN]


def build_entity_registry(assembled: dict) -> dict:
    """Map id -> {id, kind, path, title} for every file the board references:
    each repo CLAUDE.md, each SPEC.md, each task file, each handoff, plus a
    targeted listing of every spec's evidence/ dir. Built from assemble() data
    so it costs no extra scan; keyed by id, so one file yields exactly one id."""
    registry: dict = {}

    def add(kind: str, path: str, title: str = "") -> None:
        real = os.path.realpath(path)
        eid = _entity_id(kind, real)
        registry.setdefault(
            eid, {"id": eid, "kind": kind, "path": real, "title": title}
        )

    for repo in assembled.get("repos", []):
        root = repo.get("path") or ""
        if not root:
            continue
        add("file", os.path.join(root, "CLAUDE.md"), "CLAUDE.md")
        for spec in repo.get("specs", []):
            spath = spec.get("path") or ""
            spec_abs = spath if os.path.isabs(spath) else os.path.join(root, spath)
            if spec_abs.endswith(".md"):  # toolkit SPEC.md; Kiro specs are dirs
                add("file", spec_abs, spec.get("title", ""))
            for task in spec.get("tasks", []):
                tabs = task.get("abs")
                if not tabs and task.get("file"):
                    tabs = os.path.join(root, task["file"])
                if tabs:
                    add("file", tabs, task.get("title", ""))
            evidence_dir = os.path.join(os.path.dirname(spec_abs), "evidence")
            try:
                names = sorted(os.listdir(evidence_dir))
            except OSError:
                names = []
            for name in names:
                if name.endswith(".md"):
                    add("file", os.path.join(evidence_dir, name), name)
        for handoff in repo.get("handoffs", []):
            hpath = handoff.get("path") or ""
            if not hpath:
                continue
            habs = hpath if os.path.isabs(hpath) else os.path.join(root, hpath)
            add("file", habs, handoff.get("title", ""))
    return registry


def get_registry() -> dict:
    """The entity registry for the current board, doing the lazy first scan via
    get_board() (so a deep link before any scan resolves, not 404s) and serving
    the cache within the TTL window — never an extra workboard.assemble call."""
    get_board()
    return _board_cache.get("registry") or {}


def _abs_under(root: str, path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(root, path)


def _spec_dir(root: str, spec_path: str) -> str:
    """Directory holding a spec: the parent of its SPEC.md (toolkit specs) or
    the path itself (Kiro specs, which are directories)."""
    ab = _abs_under(root, spec_path)
    return os.path.dirname(ab) if ab.endswith(".md") else ab


def build_page_registry(assembled: dict) -> dict:
    """Map id -> entry for the repo/spec/task detail pages, keyed by the same
    content-derived id scheme as the file registry (kind + canonical path). Kept
    separate from build_entity_registry so a repo/spec entity and a file entity
    for the same path get distinct ids and distinct routes. Entries carry the
    assemble() source dict the renderer needs, so no rescan is required."""
    pages: dict = {}
    for repo in assembled.get("repos", []):
        root = repo.get("path") or ""
        if not root:
            continue
        rid = _entity_id("repo", root)
        pages.setdefault(
            rid,
            {
                "id": rid,
                "kind": "repo",
                "path": os.path.realpath(root),
                "title": repo.get("name") or root,
                "repo": repo,
            },
        )
        for spec in repo.get("specs", []):
            spath = spec.get("path") or ""
            if not spath:
                continue
            sdir = _spec_dir(root, spath)
            sid = _entity_id("spec", sdir)
            pages.setdefault(
                sid,
                {
                    "id": sid,
                    "kind": "spec",
                    "path": os.path.realpath(sdir),
                    "title": spec.get("title") or spec.get("slug") or "",
                    "spec": spec,
                    "root": root,
                },
            )
            for task in spec.get("tasks", []):
                tabs = task.get("abs") or (
                    _abs_under(root, task["file"]) if task.get("file") else ""
                )
                if not tabs:
                    continue
                tid = _entity_id("task", tabs)
                pages.setdefault(
                    tid,
                    {
                        "id": tid,
                        "kind": "task",
                        "path": os.path.realpath(tabs),
                        "title": task.get("title") or "",
                        "task": task,
                    },
                )
        for s in repo.get("sessions", []):
            ssid = s.get("id")
            if not ssid:
                continue
            seid = _entity_id("session", ssid)
            pages.setdefault(
                seid,
                {
                    "id": seid,
                    "kind": "session",
                    "title": (s.get("prompt") or "session")[:90],
                    "session": s,
                    "root": root,
                },
            )
    return pages


def get_pages() -> dict:
    """The repo/spec/task page registry for the current board (same lazy-scan
    and TTL-cache contract as get_registry)."""
    get_board()
    return _board_cache.get("pages") or {}


def _is_git_root(path: str) -> bool:
    """Whether `path` is a git-repo root — the same `.git`-child test the
    scanner's find_repos uses. Dispatches (drain/verify/resume) only generate
    for git roots (R5b): a spec under the non-git `~/specs` home has no repo
    cwd to run in, so it gets view actions only."""
    try:
        return (Path(path) / ".git").exists()
    except OSError:
        return False


def _prompt_from_cmd(cmd: str) -> str:
    """The prompt out of a scanner inbox `cmd` (`cd <repo> && claude <prompt>`).
    Reusing the scanner's own text keeps a single source for the verify/resume
    prompts (workboard.py owns them; this server never duplicates them)."""
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return ""
    if "claude" in parts:
        i = parts.index("claude")
        if i + 1 < len(parts):
            return parts[i + 1]
    return ""


def _scanner_dispatch_prompts(inbox: list) -> tuple[dict, dict]:
    """Index the verify/resume prompts workboard.attention_items already built,
    keyed by (repo-name, spec-slug) and (repo-name, handoff-title), so a
    dispatch action reuses the scanner's exact prompt rather than a local copy."""
    verify: dict = {}
    resume: dict = {}
    for i in inbox:
        prompt = _prompt_from_cmd(i.get("cmd") or "")
        if not prompt:
            continue
        repo, item = i.get("repo") or "", i.get("item") or ""
        if (
            i.get("state") == "needs-review"
            and item.startswith("Spec ")
            and ": all " in item
        ):
            verify[(repo, item[len("Spec ") : item.index(": all ")])] = prompt
        elif item.startswith("Handoff parked: "):
            resume[(repo, item[len("Handoff parked: ") :])] = prompt
    return verify, resume


def _unblock_prompt(unblock: dict) -> str:
    """The agent prompt for an `unblock` dispatch. `run:` text is untrusted
    file-derived data, so it is never exec'd: the agent is told to evaluate it
    and run it only under its own judgment (spec R7 / execution-safety). An
    `agent:` step is already a prompt and dispatches verbatim."""
    step = unblock.get("step") or ""
    if unblock.get("type") == "run":
        return f"Evaluate and, if safe and sensible, run: {step}; report the outcome."
    return step


def _recheck_prompt(file_path: str, unblock: dict) -> str:
    """The documented read-verify-flip-or-update prompt (spec R7), covering both
    a blocked task file (flip Status to pending + drop the Unblock line) and a
    waiting spec header (drop the Status/Unblock pair)."""
    line = f"Unblock: {unblock.get('type')}: {unblock.get('step') or ''}"
    return (
        f"Read {file_path}. It is blocked/waiting; its recorded unblock step is "
        f"`{line}`. Verify whether the blocking condition still holds. If it has "
        "cleared: for a task file, flip Status to pending and remove the Unblock "
        "line; for a spec header, remove the Status/Unblock pair; then commit with "
        "--no-verify. If it still holds, update the Unblock text with what is still "
        "missing and today's date, then commit."
    )


def _add_unblock_recheck(
    actions: dict, file_path: str, cwd: str, unblock: dict | None, label: str
) -> None:
    """Register the `unblock` + `recheck` dispatch kinds for one blocked task
    file or waiting spec header. `ask:` items get neither (no dispatch
    affordance — a human answers them); both are keyed by (kind, file) so a
    later POST validates against the current registry."""
    if not file_path or not unblock or unblock.get("type") == "ask":
        return
    uid = _entity_id("unblock", file_path)
    actions[uid] = {
        "id": uid,
        "kind": "unblock",
        "label": f"unblock: {label}",
        "repo": cwd,
        "cwd": cwd,
        "prompt": _unblock_prompt(unblock),
    }
    rid = _entity_id("recheck", file_path)
    actions[rid] = {
        "id": rid,
        "kind": "recheck",
        "label": f"recheck: {label}",
        "repo": cwd,
        "cwd": cwd,
        "prompt": _recheck_prompt(file_path, unblock),
    }


def build_action_registry(board: dict) -> dict:
    """Map action-id -> action dict for every executable action the current
    board affords. Kinds: a `push` per repo with unpushed commits
    (`git.ahead > 0`); and, for specs/handoffs in git-repo roots (R5b), the
    detached-`claude` dispatches — `dispatch-drain` (a spec with pending
    tasks), `dispatch-verify` (a spec whose tasks are all done), and
    `dispatch-resume-handoff` (a parked handoff). Every argv is built here from
    scanned facts — never client input — and each id is content-derived
    (_entity_id, kind + canonical path), so it is stable across rescans of
    unchanged state and validates a later POST against the TTL-window board."""
    actions: dict = {}
    verify_prompts, resume_prompts = _scanner_dispatch_prompts(board.get("inbox", []))

    def add_dispatch(kind: str, target: str, cwd: str, prompt: str, label: str) -> None:
        aid = _entity_id(kind, target)
        actions[aid] = {
            "id": aid,
            "kind": kind,
            "label": label,
            "repo": cwd,
            "cwd": cwd,
            "prompt": prompt,
        }

    for repo in board.get("repos", []):
        path = repo.get("path") or ""
        if not path:
            continue
        name = repo.get("name") or path
        ahead = (repo.get("git") or {}).get("ahead") or 0
        if ahead > 0:
            aid = _entity_id("push", path)
            actions[aid] = {
                "id": aid,
                "kind": "push",
                "label": f"push {name} (↑{ahead})",
                "repo": path,
                "argv": ["git", "-C", path, "push"],
            }
        if not _is_git_root(path):
            continue  # R5b: no repo cwd for a dispatch to run in
        for sp in repo.get("specs", []):
            slug, spec_path = sp.get("slug") or "", sp.get("path") or ""
            done, total = sp.get("done", 0) or 0, sp.get("total", 0) or 0
            if not spec_path or not total:
                continue
            if done < total:
                add_dispatch(
                    "dispatch-drain",
                    spec_path,
                    path,
                    f"Run /drain for specs/{slug}; work only that spec's tasks",
                    f"drain {slug} ({done}/{total})",
                )
            else:
                prompt = verify_prompts.get((name, slug))
                if prompt:
                    add_dispatch(
                        "dispatch-verify", spec_path, path, prompt, f"verify {slug}"
                    )
        for h in repo.get("handoffs", []):
            title, hpath = h.get("title") or "", h.get("path") or ""
            prompt = resume_prompts.get((name, title))
            if hpath and prompt:
                add_dispatch(
                    "dispatch-resume-handoff",
                    hpath,
                    path,
                    prompt,
                    f"resume handoff: {title}",
                )
        # unblock/recheck (unblock-next-steps R7): a waiting-spec header and each
        # blocked task file in this git root gets both agent-dispatch kinds
        # (ask: items excluded inside the helper). Kept separate from the
        # drain/verify loop above, which gates on task counts a waiting spec
        # (spec-header-only status, often no tasks/) would not satisfy.
        for sp in repo.get("specs", []):
            _add_unblock_recheck(
                actions,
                sp.get("path") or "",
                path,
                sp.get("unblock"),
                f"spec {sp.get('slug') or ''}".strip(),
            )
            for bt in sp.get("blocked_tasks") or []:
                tpath = bt.get("path") or ""
                _add_unblock_recheck(
                    actions,
                    tpath,
                    path,
                    bt.get("unblock"),
                    bt.get("title") or os.path.basename(tpath),
                )

    # stop-dispatch: one per live dispatch this server started (R1/R7). Keyed
    # on the record's log path so the id is stable across rescans of the same
    # running dispatch.
    for rec in _load_records():
        if not rec.get("running"):
            continue
        did = rec.get("id") or ""
        aid = _entity_id("stop-dispatch", rec.get("log") or did)
        actions[aid] = {
            "id": aid,
            "kind": "stop-dispatch",
            "label": f"stop {rec.get('kind', 'dispatch')}",
            "repo": rec.get("cwd") or "",
            "dispatch_id": did,
        }
    return actions


def get_actions() -> dict:
    """The action registry for the current board (same lazy-scan and TTL-cache
    contract as get_registry): a POST validates its id against exactly the
    registry built for the board the browser is looking at."""
    get_board()
    return _board_cache.get("actions") or {}


# --------------------------------------------------------------------------- #
# Rendering — one shared shell, two views
# --------------------------------------------------------------------------- #
def _ago(ts: float) -> str:
    if not ts or ts > 1e11:
        return "—"
    d = max(0, time.time() - ts)
    if d < 3600:
        return f"{int(d // 60)}m"
    if d < 86400:
        return f"{int(d // 3600)}h"
    return f"{int(d // 86400)}d"


def _dt(ts: float) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def esc(s) -> str:
    return html.escape(str(s))


def render_markdown(text: str) -> str:
    """Minimal, dependency-free markdown → HTML: headings, fenced code, and
    dash/star lists; everything else is an escaped paragraph. Every text run is
    HTML-escaped, so file contents can never inject markup."""
    out: list[str] = []
    in_code = False
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
            else:
                close_list()
                out.append("<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            out.append(esc(line))
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{esc(heading.group(2).strip())}</h{level}>")
            continue
        item = re.match(r"^\s*[-*]\s+(.*)$", line)
        if item:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{esc(item.group(1).strip())}</li>")
            continue
        close_list()
        if line.strip():
            out.append(f"<p>{esc(line)}</p>")
    if in_code:
        out.append("</code></pre>")
    close_list()
    return "\n".join(out)


def render_detail_page(title: str, body_html: str) -> str:
    """Chrome shared by every detail view: a back-to-board link, the last scan
    timestamp, and the rendered body."""
    scanned = _dt(_board_cache.get("ts") or 0)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Console — {esc(title)}</title><style>{CSS}</style></head><body>
<header><div class="masthead">
  <div class="wordmark">Agent<span class="dot">·</span>Console</div>
  <nav class="tabs"><a href="/workboard">&larr; Board</a></nav>
</div></header>
<main><div class="eyebrow"><span class="key" style="color:var(--text)">{esc(title)}</span>
<span class="rule"></span><span class="mono">scanned {esc(scanned)}</span></div>
<article class="card">{body_html}</article></main>
</body></html>"""


def _unblock_line(path: str) -> str:
    """A task file's `Unblock:` line, verbatim — plain-text passthrough; parsing
    its next-steps grammar is unblock-next-steps' scope, not ours."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.strip().startswith("Unblock:"):
                    return line.strip()
    except OSError:
        pass
    return ""


def render_repo_page(entry: dict) -> str:
    """A repo's path, state chips, unpushed commits (`git log @{u}..`), dirty
    files (`git status --porcelain`), and links to its specs, sessions, and
    CLAUDE.md. Git reads are fresh, read-only, and time-capped via _git."""
    repo = entry.get("repo") or {}
    root = entry["path"]
    name = entry.get("title") or os.path.basename(root)
    rp = Path(root)

    dirty = _git(rp, "status", "--porcelain")
    dirty_files = [ln for ln in (dirty or "").splitlines() if ln.strip()]
    unpushed = _git(rp, "log", "--oneline", "@{u}..")  # None => no upstream

    chips = []
    if dirty_files:
        chips.append('<span class="chip dirty">dirty</span>')
    if unpushed:
        chips.append('<span class="chip unpushed">unpushed</span>')
    if not dirty_files and not unpushed:
        chips.append('<span class="chip">clean</span>')

    parts = [f'<p class="mono">{esc(root)}</p>', "".join(chips)]

    if unpushed is None:
        parts.append('<div class="sub">Unpushed</div><p class="mono">no upstream</p>')
    elif unpushed:
        items = "".join(f"<li>{esc(ln)}</li>" for ln in unpushed.splitlines())
        parts.append(f'<div class="sub">Unpushed commits</div><ul>{items}</ul>')
    else:
        parts.append('<div class="sub">Unpushed commits</div><p class="mono">none</p>')

    if dirty_files:
        items = "".join(f"<li>{esc(ln)}</li>" for ln in dirty_files)
        parts.append(f'<div class="sub">Dirty files</div><ul>{items}</ul>')

    spec_rows = []
    for sp in repo.get("specs") or []:
        spath = sp.get("path") or ""
        if not spath:
            continue
        sid = _entity_id("spec", _spec_dir(root, spath))
        label = esc(sp.get("title") or sp.get("slug") or "spec")
        spec_rows.append(f'<li><a href="/spec/{esc(sid)}">{label}</a></li>')
    if spec_rows:
        parts.append(f'<div class="sub">Specs</div><ul>{"".join(spec_rows)}</ul>')

    sess_rows = []
    for s in repo.get("sessions") or []:
        label = esc((s.get("prompt") or "")[:90] or "session")
        state = esc(s.get("state") or "")
        sid = s.get("id") or ""
        if sid:
            link = _entity_id("session", sid)
            sess_rows.append(
                f'<li><a href="/session/{esc(link)}">{label}</a> '
                f'<span class="meta">{state}</span></li>'
            )
        else:
            sess_rows.append(f'<li>{label} <span class="meta">{state}</span></li>')
    if sess_rows:
        parts.append(f'<div class="sub">Sessions</div><ul>{"".join(sess_rows)}</ul>')

    claude_md = os.path.join(root, "CLAUDE.md")
    if os.path.exists(claude_md):
        cid = _entity_id("file", claude_md)
        parts.append(
            f'<div class="sub">Conventions</div>'
            f'<p><a href="/file/{esc(cid)}">CLAUDE.md</a></p>'
        )

    return render_detail_page(name, "".join(parts))


def _projects_root() -> Path:
    """Root of the per-project session transcript tree
    (`~/.claude/projects/*/<sessionId>.jsonl`); a function so tests can point
    it at a fixture dir."""
    return HOME / ".claude" / "projects"


def _transcript_path(sid: str, root: Path | None = None):
    """First `<root>/*/<sid>.jsonl` match, else None. `sid` is a resolved
    sessionId from the registry, never client input, but path separators are
    rejected defensively before globbing."""
    if not sid or "/" in sid or "\\" in sid or ".." in sid:
        return None
    base = root if root is not None else _projects_root()
    try:
        matches = sorted(Path(base).glob(f"*/{sid}.jsonl"))
    except OSError:
        return None
    return matches[0] if matches else None


def tail_events(path, n: int = 50, window: int = 65_536):
    """Last ~n parsed JSONL events read tail-first from a bounded byte window
    (never the whole file). Returns (events, approx_total): approx_total is the
    exact count when the window spans the file, else a byte-ratio estimate
    (events_in_window * file_size / bytes_read)."""
    path = str(path)
    try:
        size = os.path.getsize(path)
    except OSError:
        return [], 0
    start = max(0, size - window)
    try:
        with open(path, "rb") as f:
            f.seek(start)
            chunk = f.read()
    except OSError:
        return [], 0
    lines = chunk.decode("utf-8", errors="replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]  # drop the partial leading line the window cut into
    events = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            events.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    in_window = len(events)
    read_bytes = len(chunk)
    if start == 0 or read_bytes >= size or not read_bytes:
        approx_total = in_window
    else:
        approx_total = round(in_window * size / read_bytes)
    return events[-n:], approx_total


def _render_events(events) -> str:
    """A transcript tail as role-tagged lines. Tool payloads are elided: a
    tool_use shows only `[tool: NAME]`; a tool_result resolves its NAME from a
    matching tool_use in the tail (else `[tool result]`). No tool input/output
    payload text is ever emitted."""
    names: dict = {}
    for ev in events:
        msg = ev.get("message") if isinstance(ev, dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        if isinstance(content, list):
            for blk in content:
                if (
                    isinstance(blk, dict)
                    and blk.get("type") == "tool_use"
                    and blk.get("id")
                ):
                    names[blk["id"]] = blk.get("name") or "tool"

    rows = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
        role = msg.get("role") or ev.get("type") or "event"
        content = msg.get("content")
        pieces = []
        if isinstance(content, str):
            if content.strip():
                pieces.append(esc(content.strip()))
        elif isinstance(content, list):
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                bt = blk.get("type")
                if bt == "text":
                    text = (blk.get("text") or "").strip()
                    if text:
                        pieces.append(esc(text))
                elif bt == "tool_use":
                    pieces.append(
                        f'<span class="tool">[tool: {esc(blk.get("name") or "tool")}]</span>'
                    )
                elif bt == "tool_result":
                    nm = names.get(blk.get("tool_use_id"))
                    label = f"[tool: {esc(nm)} result]" if nm else "[tool result]"
                    pieces.append(f'<span class="tool">{label}</span>')
        if not pieces:
            continue
        rows.append(
            f'<div class="evt"><span class="role">{esc(role)}</span> '
            f"{' '.join(pieces)}</div>"
        )
    return "".join(rows)


def render_session_page(entry: dict) -> str:
    """A session's metadata (cwd, sessionId, state, started/last-active, pid when
    live) plus a tail of the last ~50 transcript events (roles + text + tool
    names; payloads elided). Resume/stop reuse the existing agent-control POSTs
    via the shared data-act handlers."""
    session = entry.get("session") or {}
    sid = session.get("id") or ""
    state = session.get("state") or ""
    cwd = session.get("cwd") or ""
    started = _dt(session.get("start_ts") or 0)
    last = _dt(session.get("last_ts") or session.get("end_ts") or 0)
    pid = _running_pid_for(sid) if state == "active" else None

    meta = [
        f'<p class="mono">{esc(cwd or "—")}</p>',
        '<div class="sub">Session</div>',
        '<table class="meta">'
        f'<tr><td>sessionId</td><td class="mono">{esc(sid)}</td></tr>'
        f"<tr><td>state</td><td>{esc(state)}</td></tr>"
        f"<tr><td>started</td><td>{esc(started)}</td></tr>"
        f"<tr><td>last active</td><td>{esc(last)}</td></tr>"
        + (f'<tr><td>pid</td><td class="mono">{esc(pid)}</td></tr>' if pid else "")
        + "</table>",
    ]

    btns = []
    if pid:
        btns.append(
            f'<button class="btn stop" data-act="stop" data-pid="{esc(pid)}" '
            f'data-name="{esc(sid[:8])}">stop</button>'
        )
    if sid:
        btns.append(
            f'<button class="btn" data-act="resume" data-sid="{esc(sid)}" '
            f'data-name="{esc(sid[:8])}">resume</button>'
        )
    if btns:
        meta.append(f'<div class="controls">{"".join(btns)}</div>')

    tpath = _transcript_path(sid)
    if tpath is None:
        meta.append(
            '<div class="sub">Transcript</div><p class="mono">no transcript found</p>'
        )
    else:
        events, total = tail_events(tpath)
        shown = len(events)
        banner = f"last {shown} of ~{total}" if total > shown else f"{shown} events"
        body = _render_events(events) or '<p class="mono">no events</p>'
        meta.append(
            f'<div class="sub">Transcript</div><p class="meta">{esc(banner)}</p>'
            f'<div class="transcript">{body}</div>'
        )

    title = (session.get("prompt") or "session")[:90]
    page = render_detail_page(title, "".join(meta))
    # inject the shared CSRF token + client JS so the resume/stop data-act
    # buttons work from this page too (render_detail_page ships neither).
    inject = f"<script>window.CSRF={json.dumps(CSRF_TOKEN)};</script>{PAGE_JS}"
    return page.replace("</body></html>", inject + "</body></html>")


def render_spec_page(entry: dict) -> str:
    """A spec's rendered SPEC.md, its task table (name, status, verbatim Unblock
    line, link to the task page), evidence-file links, and — in git-repo roots —
    the last 10 commits touching the spec dir."""
    spec = entry.get("spec") or {}
    spec_dir = entry["path"]
    root = entry.get("root") or spec_dir
    title = entry.get("title") or os.path.basename(spec_dir)

    parts = [f'<p class="mono">{esc(spec_dir)}</p>']

    spath = spec.get("path") or ""
    spec_abs = _abs_under(root, spath) if spath else ""
    if spec_abs.endswith(".md"):
        try:
            with open(spec_abs, encoding="utf-8", errors="replace") as fh:
                parts.append(render_markdown(fh.read()))
        except OSError:
            pass

    task_rows = []
    for t in spec.get("tasks") or []:
        tabs = t.get("abs") or (_abs_under(root, t["file"]) if t.get("file") else "")
        label = esc(t.get("title") or (os.path.basename(tabs) if tabs else "task"))
        status = esc(t.get("status") or "")
        unblock = esc(_unblock_line(tabs)) if tabs else ""
        if tabs:
            tid = _entity_id("task", tabs)
            cell = f'<a href="/task/{esc(tid)}">{label}</a>'
        else:
            cell = label
        task_rows.append(f"<tr><td>{cell}</td><td>{status}</td><td>{unblock}</td></tr>")
    if task_rows:
        parts.append(
            '<div class="sub">Tasks</div>'
            "<table><thead><tr><th>Task</th><th>Status</th><th>Unblock</th>"
            f"</tr></thead><tbody>{''.join(task_rows)}</tbody></table>"
        )

    ev_dir = os.path.join(spec_dir, "evidence")
    try:
        ev_names = sorted(n for n in os.listdir(ev_dir) if n.endswith(".md"))
    except OSError:
        ev_names = []
    if ev_names:
        rows = "".join(
            f'<li><a href="/file/{esc(_entity_id("file", os.path.join(ev_dir, n)))}">'
            f"{esc(n)}</a></li>"
            for n in ev_names
        )
        parts.append(f'<div class="sub">Evidence</div><ul>{rows}</ul>')

    log = _git(Path(root), "log", "--oneline", "-10", "--", spec_dir)
    if log:
        items = "".join(f"<li>{esc(ln)}</li>" for ln in log.splitlines())
        parts.append(f'<div class="sub">Recent commits</div><ul>{items}</ul>')

    return render_detail_page(title, "".join(parts))


def _prio_select(path: str, current: str) -> str:
    """A priority <select> for a spec; posts to /api/priority on change."""
    opts = f'<option value=""{" selected" if not current else ""}>—</option>'
    opts += "".join(
        f'<option value="{p}"{" selected" if p == current else ""}>{p}</option>'
        for p in PRIORITIES
    )
    cls = f"prio prio-{current}" if current else "prio"
    return (
        f'<select class="{cls}" data-prio-path="{esc(path)}" '
        f'aria-label="priority">{opts}</select>'
    )


CSS = """
:root{
  --ground:#0e1016; --panel:#161922; --raise:#1c212c; --rule:#252b38;
  --text:#e6e9f0; --dim:#8b93a4; --faint:#5a6274;
  --signal:#d98a63; --signal-bg:#241a14; --cool:#6ea3c0;
  --disp:'Futura','Avenir Next',ui-sans-serif,system-ui;
  --body:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  --mono:'SF Mono',ui-monospace,Menlo,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--text);font-family:var(--body);
  font-size:14px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.mono{font-family:var(--mono)}
header{position:sticky;top:0;z-index:20;background:rgba(14,16,22,.88);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--rule)}
.masthead{display:flex;align-items:baseline;justify-content:space-between;
  gap:16px;padding:16px 26px 0;flex-wrap:wrap}
.wordmark{font-family:var(--disp);font-weight:600;font-size:15px;
  letter-spacing:.34em;text-transform:uppercase}
.wordmark .dot{color:var(--signal)}
.readout{font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.02em}
.readout b{color:var(--text);font-weight:600}
.tabs{display:flex;gap:2px;padding:12px 26px 0}
.tab{font-family:var(--disp);text-transform:uppercase;letter-spacing:.18em;
  font-size:11.5px;padding:9px 16px;color:var(--dim);border-bottom:2px solid transparent}
.tab:hover{color:var(--text)}
.tab.on{color:var(--text);border-bottom-color:var(--signal)}
.filterbar{padding:12px 26px 14px}
#q{width:100%;padding:9px 13px;border-radius:7px;border:1px solid var(--rule);
  background:var(--panel);color:var(--text);font-size:13.5px;font-family:var(--mono)}
#q:focus{outline:none;border-color:var(--cool)}
main{padding:22px 26px 80px;max-width:1320px;margin:0 auto}
.eyebrow{display:flex;align-items:center;gap:10px;margin:30px 0 12px}
.eyebrow .key{font-family:var(--disp);text-transform:uppercase;letter-spacing:.2em;
  font-size:11.5px;color:var(--dim)}
.eyebrow .rule{flex:1;height:1px;background:var(--rule)}
.eyebrow .n{font-family:var(--mono);font-size:11px;color:var(--faint)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:11px}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:9px;
  padding:12px 14px;transition:border-color .12s,transform .12s}
.card:hover{border-color:#37404f;transform:translateY(-1px)}
.card .top{display:flex;align-items:center;gap:8px;margin-bottom:5px}
.card .nm{font-weight:600;font-size:13.5px}
.tag{font-family:var(--mono);font-size:9.5px;letter-spacing:.04em;padding:1px 6px;
  border-radius:5px;background:var(--raise);color:var(--dim);text-transform:uppercase}
.tag.cmd{color:var(--cool)} .tag.agent{color:var(--cool)}
.card .desc{margin:0 0 8px;color:var(--dim);font-size:12px;
  display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.card .path{font-family:var(--mono);font-size:10px;color:var(--faint);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hidden{display:none!important}
/* workboard */
.health{border:1px solid #5c3a28;border-left:2px solid var(--signal);
  background:var(--signal-bg);color:var(--signal);border-radius:8px;
  padding:9px 14px;margin-bottom:16px;font-family:var(--mono);font-size:11.5px}
/* priority select on spec rows */
.specrow{display:flex;align-items:baseline;gap:8px}
.specrow>.spec,.specrow>.line{flex:1;min-width:0}
select.prio{appearance:none;-webkit-appearance:none;background:var(--raise);color:var(--faint);
  border:1px solid var(--rule);border-radius:5px;font-family:var(--disp);font-size:9.5px;
  letter-spacing:.06em;padding:2px 6px;cursor:pointer;flex:none;align-self:center}
select.prio:focus{outline:none;border-color:var(--cool)}
select.prio.prio-P0,select.prio.prio-P1{color:var(--signal);border-color:#5c3a28}
select.prio.prio-P2{color:var(--cool);border-color:#2f4a58}
select.prio.prio-P3{color:var(--dim)}
/* agents control */
.agents{border:1px solid var(--rule);border-radius:9px;background:var(--panel);
  padding:6px 14px 12px;margin-bottom:26px}
.kickoff{display:flex;gap:8px;margin:8px 0 4px;flex-wrap:wrap}
.kickoff input[name=prompt]{flex:1;min-width:220px;padding:8px 11px;border-radius:7px;
  border:1px solid var(--rule);background:var(--ground);color:var(--text);
  font-size:13px;font-family:var(--body)}
.kickoff input:focus,.kickoff select:focus{outline:none;border-color:var(--cool)}
.kickoff select{padding:8px 10px;border-radius:7px;border:1px solid var(--rule);
  background:var(--ground);color:var(--text);font-family:var(--mono);font-size:12px}
.btn{font-family:var(--disp);text-transform:uppercase;letter-spacing:.1em;font-size:10px;
  padding:4px 12px;border-radius:6px;border:1px solid var(--rule);background:var(--raise);
  color:var(--dim);cursor:pointer;align-self:center;flex:none}
.btn:hover{border-color:#37404f;color:var(--text)}
.btn.go{color:var(--cool);border-color:#2f4a58}
.btn.stop{color:var(--signal);border-color:#5c3a28}
.acwd{font-family:var(--mono);font-size:10.5px;color:var(--faint)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
  gap:11px;margin-bottom:24px}
.tile{background:var(--panel);border:1px solid var(--rule);border-radius:9px;padding:13px 15px;
  text-align:left;font:inherit;color:inherit;cursor:pointer;transition:border-color .12s,transform .12s}
.tile:hover{border-color:#37404f;transform:translateY(-1px)}
.tile:focus-visible{outline:2px solid var(--cool);outline-offset:2px}
.tile.on{border-color:var(--cool)}
.tile .v{font-family:var(--mono);font-size:26px;font-weight:600;line-height:1}
.tile .l{font-family:var(--disp);text-transform:uppercase;letter-spacing:.13em;
  font-size:10px;color:var(--dim);margin-top:7px}
.tile.alert .v{color:var(--signal)}
.panel{display:none;border:1px solid var(--rule);border-radius:9px;background:var(--panel);
  padding:8px 14px 12px;margin:-14px 0 24px}
.panel.show{display:block}
.spec{border:none;background:none}
.spec>summary{list-style:none;cursor:pointer;position:relative;padding-left:16px}
.spec>summary::-webkit-details-marker{display:none}
.spec>summary::before{content:'▸';position:absolute;left:0;top:6px;
  color:var(--faint);font-size:9px}
.spec[open]>summary::before{content:'▾'}
.spec>summary:hover .trunc{color:var(--cool)}
.line.plain{padding-left:16px}
.viz-graphwrap{overflow-x:auto;padding:10px 0 6px 20px}
.viz-graphwrap svg{max-width:none}
.inbox{border:1px solid var(--rule);border-left:2px solid var(--signal);
  background:linear-gradient(90deg,var(--signal-bg),var(--panel) 55%);
  border-radius:9px;overflow:hidden;margin-bottom:26px}
.inbox .row{display:grid;grid-template-columns:96px 1fr 150px 60px;gap:12px;
  align-items:baseline;padding:10px 15px;border-top:1px solid var(--rule)}
.inbox .row:first-child{border-top:none}
.inbox .what{font-weight:600;font-size:13px}
.inbox .why{color:var(--dim);font-size:12px}
.inbox .why code{font-family:var(--mono);font-size:11px;color:var(--cool);
  background:var(--raise);padding:1px 5px;border-radius:4px}
.inbox .repo{font-family:var(--mono);font-size:11px;color:var(--dim);
  text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.inbox .age{font-family:var(--mono);font-size:11px;color:var(--faint);text-align:right}
.inbox.needs-answer{border-left:3px solid var(--cool);
  background:linear-gradient(90deg,var(--raise),var(--panel) 55%);margin-bottom:14px}
.inbox .ihead{font-family:var(--disp);text-transform:uppercase;letter-spacing:.13em;
  font-size:9.5px;color:var(--cool);padding:9px 15px 3px}
.chip.needs-answer{color:var(--cool);border-color:#2f4a58}
.chip.warn{color:var(--signal);border-color:#5c3a28}
.chip{font-family:var(--disp);text-transform:uppercase;letter-spacing:.09em;
  font-size:9.5px;padding:2px 8px;border-radius:5px;border:1px solid var(--rule);
  color:var(--dim);white-space:nowrap;align-self:center}
.chip.blocked{color:var(--signal);border-color:#5c3a28}
.chip.verify{color:var(--cool);border-color:#2f4a58}
.chip.stale,.chip.dirty,.chip.unpushed,.chip.idle{color:var(--dim)}
.chip.active{color:var(--signal);border-color:#5c3a28}
.chip.recent{color:var(--cool)}
.zero{color:var(--dim);padding:16px 4px;font-size:13px}
.repo{border:1px solid var(--rule);border-radius:9px;margin-bottom:12px;background:var(--panel)}
.repo>summary{list-style:none;cursor:pointer;padding:13px 16px;display:flex;
  align-items:baseline;gap:12px;flex-wrap:wrap}
.repo>summary::-webkit-details-marker{display:none}
.repo .rn{font-family:var(--mono);font-size:13px;font-weight:600}
.gchip{font-family:var(--mono);font-size:10.5px;color:var(--dim);
  border:1px solid var(--rule);border-radius:5px;padding:1px 7px}
.gchip.warn{color:var(--signal);border-color:#5c3a28}
button.gchip.act{background:none;cursor:pointer}
button.gchip.act:hover{color:var(--text);border-color:#8a4a30}
.ghb{font-family:var(--disp);text-transform:uppercase;letter-spacing:.08em;
  font-size:9px;padding:2px 7px;border-radius:5px;border:1px solid var(--rule);color:var(--dim)}
.ghb.public{color:var(--cool);border-color:#2f4a58}
.ghb.private{color:var(--signal);border-color:#5c3a28}
.ghb.local{color:var(--faint)}
a.ghb:hover{border-color:var(--text)}
.commit{flex-basis:100%;display:flex;align-items:baseline;gap:9px;min-width:0;
  margin-top:6px;font-size:11.5px;color:var(--dim)}
.commit .chash{font-family:var(--mono);font-size:10.5px;color:var(--cool);flex:none}
.commit .csub{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.commit .cwhen{font-family:var(--mono);font-size:10.5px;color:var(--faint);
  margin-left:auto;white-space:nowrap;flex:none}
.rbody{padding:2px 16px 15px;border-top:1px solid var(--rule)}
.sub{font-family:var(--disp);text-transform:uppercase;letter-spacing:.15em;
  font-size:9.5px;color:var(--faint);margin:14px 0 7px}
.line{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:12px;align-items:baseline;
  padding:5px 0;border-top:1px solid var(--rule);font-size:12.5px}
.line.evt{grid-template-columns:auto minmax(0,1fr) auto}
.line:first-of-type{border-top:none}
.line>.chip{justify-self:start}
.line .meta{font-family:var(--mono);font-size:11px;color:var(--faint)}
.prog{display:inline-flex;align-items:center;gap:8px;justify-self:end}
.bar{height:4px;border-radius:2px;background:var(--raise);width:120px;overflow:hidden;align-self:center}
.bar>i{display:block;height:100%;background:var(--cool)}
.trunc{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
footer{color:var(--faint);font-family:var(--mono);font-size:10.5px;
  text-align:center;padding:26px}
@media (max-width:640px){.inbox .row{grid-template-columns:80px 1fr;}
  .inbox .repo,.inbox .age{display:none}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
.kanban-board{display:flex;gap:11px;align-items:flex-start;overflow-x:auto;padding-bottom:8px}
.kanban-column{flex:1 1 0;min-width:210px;background:var(--panel);border:1px solid var(--rule);
  border-radius:9px;padding:11px 12px}
.kanban-column details>summary{list-style:none;cursor:pointer}
.kanban-column details>summary::-webkit-details-marker{display:none}
.col-header,.kanban-column summary{display:flex;align-items:center;gap:8px;margin-bottom:9px}
.col-head{font-family:var(--disp);text-transform:uppercase;letter-spacing:.13em;
  font-size:10.5px;color:var(--dim)}
.kanban-column .count{font-family:var(--mono);font-size:11px;color:var(--faint)}
.col-cards{display:flex;flex-direction:column;gap:8px}
.kanban-card{background:var(--raise);border:1px solid var(--rule);border-radius:7px;
  padding:9px 11px;transition:border-color .12s}
.kanban-card:hover{border-color:#37404f}
.kanban-card .card-title{font-size:12.5px;font-weight:600;margin-bottom:5px}
.kanban-card .card-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.kanban-card .badge{font-family:var(--mono);font-size:10px;color:var(--faint)}
.kanban-card .prio{font-family:var(--disp);text-transform:uppercase;letter-spacing:.1em;
  font-size:9.5px;color:var(--signal);background:var(--signal-bg);padding:1px 6px;border-radius:4px}
.kanban-column .zero{color:var(--faint);font-size:11.5px}
"""


# Client script: delegated handlers (survive DOM swaps) + in-place auto-refresh
# that re-fetches the current view every REFRESH ms and swaps <main> while
# preserving scroll, expanded <details>, the open drill-down panel, and the
# skills filter. Delegation means handlers keep working after each swap.
PAGE_JS = """<script>(function(){
var $=function(s){return document.querySelector(s)},$$=function(s){return document.querySelectorAll(s)};
document.addEventListener('input',function(e){
  if(e.target.id!=='q')return;var t=e.target.value.trim().toLowerCase();
  $$('[data-text]').forEach(function(c){c.classList.toggle('hidden',t&&c.dataset.text.indexOf(t)<0)});
  $$('[data-group]').forEach(function(g){var any=[].slice.call(g.querySelectorAll('.card')).some(function(c){return !c.classList.contains('hidden')});g.classList.toggle('hidden',!any)});
});
document.addEventListener('click',function(e){
  var t=e.target.closest('.tile');if(!t)return;
  if(t.dataset.panel){var id='panel-'+t.dataset.panel,p=document.getElementById(id);
    $$('.panel').forEach(function(x){if(x.id!==id)x.classList.remove('show')});
    var on=p.classList.toggle('show');
    $$('.tile[data-panel]').forEach(function(x){x.classList.remove('on')});
    if(on){t.classList.add('on');p.scrollIntoView({behavior:'smooth',block:'nearest'})}
  }else if(t.dataset.scroll){var d=$(t.dataset.scroll);if(d)d.scrollIntoView({behavior:'smooth',block:'start'})}
});
// --- writes / agent control (CSRF-guarded POSTs) ---
function acPost(url,body,confirmMsg){
  if(confirmMsg&&!window.confirm(confirmMsg))return Promise.resolve(false);
  return fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF':window.CSRF||''},body:JSON.stringify(body)})
    .then(function(r){return r.json().catch(function(){return{ok:r.ok}}).then(function(j){
      if(!j.ok){window.alert('Failed: '+(j.message||r.status))}return j.ok})})
    .catch(function(e){window.alert('Request failed: '+e);return false});
}
// change a spec's priority
document.addEventListener('change',function(e){
  var sel=e.target.closest('select[data-prio-path]');if(!sel)return;
  acPost('/api/priority',{path:sel.dataset.prioPath,value:sel.value}).then(function(ok){if(ok)refresh()});
});
// stop / resume / start-agent buttons
document.addEventListener('click',function(e){
  var b=e.target.closest('[data-act]');if(!b)return;
  e.preventDefault();
  if(b.dataset.act==='stop'){
    acPost('/api/agent/stop',{pid:parseInt(b.dataset.pid,10),confirm:true},'Stop agent "'+(b.dataset.name||b.dataset.pid)+'" (SIGTERM, then SIGKILL after 10s)? Resumable via claude --resume.').then(function(ok){if(ok)setTimeout(refresh,600)});
  }else if(b.dataset.act==='stop-dispatch'){
    acPost('/action/'+encodeURIComponent(b.dataset.id),{confirm:true},b.dataset.confirm||'Stop this dispatch (SIGTERM, then SIGKILL after 10s)?').then(function(ok){if(ok)setTimeout(refresh,800)});
  }else if(b.dataset.act==='resume'){
    var p=window.prompt('Resume "'+(b.dataset.name||b.dataset.sid)+'" as a background agent. Prompt (blank = "continue"):','');
    if(p===null)return;
    acPost('/api/agent/resume',{sid:b.dataset.sid,prompt:p}).then(function(ok){if(ok)setTimeout(refresh,800)});
  }else if(b.dataset.act==='start'){
    var form=b.closest('.kickoff'),prompt=form.querySelector('[name=prompt]').value,cwd=form.querySelector('[name=cwd]').value;
    if(!prompt.trim()){window.alert('Enter a prompt.');return}
    acPost('/api/agent/start',{cwd:cwd,prompt:prompt},'Kick off a background agent in '+cwd+'? This runs Claude and costs tokens.').then(function(ok){if(ok){form.querySelector('[name=prompt]').value='';setTimeout(refresh,900)}});
  }else if(b.dataset.act==='push'){
    acPost('/action/'+encodeURIComponent(b.dataset.id),{},'Push "'+(b.dataset.name||'repo')+'"? Runs: git push').then(function(ok){if(ok)setTimeout(refresh,800)});
  }else if(b.dataset.act==='dispatch'){
    acPost('/action/'+encodeURIComponent(b.dataset.id),{},b.dataset.confirm||'Launch this Claude dispatch in the repo? It runs an agent with write access and costs tokens.').then(function(ok){if(ok)setTimeout(refresh,800)});
  }else if(b.dataset.act==='refresh-profile'){
    acPost('/api/profile/refresh',{}).then(function(ok){if(ok)setTimeout(refresh,600)});
  }
});
var REFRESH=25000;
function stamp(){var el=document.getElementById('live');if(el)el.textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'})}
function snap(){return{open:[].slice.call($$('details[data-k]')).filter(function(d){return d.open}).map(function(d){return d.dataset.k}),panel:($('.panel.show')||{}).id||'',y:window.scrollY,q:($('#q')||{}).value||''}}
function rest(s){
  s.open.forEach(function(k){var d=document.querySelector('details[data-k="'+CSS.escape(k)+'"]');if(d)d.open=true});
  if(s.panel){var p=document.getElementById(s.panel);if(p)p.classList.add('show');var t=document.querySelector('.tile[data-panel="'+s.panel.replace('panel-','')+'"]');if(t)t.classList.add('on')}
  var q=$('#q');if(q&&s.q){q.value=s.q;q.dispatchEvent(new Event('input'))}
  window.scrollTo(0,s.y);
}
function refresh(){
  if(document.hidden)return;var a=document.activeElement;
  if(a&&(a.tagName==='INPUT'||a.tagName==='SELECT'||a.tagName==='TEXTAREA'||a.tagName==='SUMMARY'))return;
  fetch(location.href,{cache:'no-store'}).then(function(r){return r.text()}).then(function(html){
    var doc=new DOMParser().parseFromString(html,'text/html'),nm=doc.querySelector('main');if(!nm)return;
    var s=snap();$('main').replaceWith(nm);
    var nr=doc.querySelector('.readout');if(nr)$('.readout').innerHTML=nr.innerHTML;
    rest(s);stamp();
  }).catch(function(){});
}
setInterval(refresh,REFRESH);
document.addEventListener('visibilitychange',function(){if(!document.hidden)refresh()});
stamp();
})();</script>"""


def page(active: str, readout: str, body: str, with_filter: bool) -> str:
    def tab(href, label, key):
        return (
            f'<a class="tab {"on" if key == active else ""}" href="{href}">{label}</a>'
        )

    filt = (
        (
            '<div class="filterbar"><input id="q" type="search" '
            'placeholder="filter by name or description" autofocus></div>'
        )
        if with_filter
        else ""
    )
    # Profile link — pprof web UI over the rolling agentprof profile. Plain
    # anchor, no health gating: renders even when the pprof server is down.
    profile_link = (
        '<a class="tab" href="http://127.0.0.1:8901/" target="_blank" '
        'rel="noopener">Profile</a>'
        if active == "workboard"
        else ""
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Console — {esc(active).title()}</title><style>{viz.VIZ_CSS}{CSS}</style></head><body>
<header>
  <div class="masthead">
    <div class="wordmark">Agent<span class="dot">·</span>Console</div>
    <div class="readout">{readout}</div>
  </div>
  <nav class="tabs">{tab("/", "Skills", "skills")}{tab("/workboard", "Workboard", "workboard")}{tab("/workboard-kanban", "Board", "board")}{profile_link}</nav>
  {filt}
</header>
<main>{body}</main>
<footer>live · updated <span id="live" class="mono"></span> · auto-refresh 25s</footer>
<script>window.CSRF={json.dumps(CSRF_TOKEN)};</script>
{PAGE_JS}
</body></html>"""


def _source_order(s: str):
    return (
        0
        if s == "personal"
        else 1
        if s.startswith("project:")
        else 2
        if s.startswith("plugin:")
        else 3,
        s,
    )


def render_skills(model: dict) -> str:
    def card(rec):
        tag = ""
        if rec["kind"] == "command":
            tag = '<span class="tag cmd">cmd</span>'
        elif rec["kind"] == "built-in":
            tag = '<span class="tag">built-in</span>'
        elif rec["kind"] == "agent":
            tag = '<span class="tag agent">agent</span>'
        elif rec.get("model"):
            tag = f'<span class="tag">{esc(rec["model"])}</span>'
        return (
            f'<div class="card" data-text="{esc(rec["name"].lower())} {esc(rec["description"].lower())}">'
            f'<div class="top"><span class="nm">{esc(rec["name"])}</span>{tag}</div>'
            f'<p class="desc">{esc(rec["description"] or "—")}</p>'
            f'<div class="path" title="{esc(rec["path"])}">{esc(rec["path"])}</div></div>'
        )

    def block(title, buckets):
        parts = []
        for src in sorted(buckets, key=_source_order):
            recs = buckets[src]
            parts.append(
                f'<div data-group><div class="eyebrow"><span class="key">{esc(src)}</span>'
                f'<span class="rule"></span><span class="n">{len(recs):02d}</span></div>'
                f'<div class="grid">{"".join(card(r) for r in recs)}</div></div>'
            )
        return (
            f'<div class="eyebrow"><span class="key" style="color:var(--text)">{title}</span>'
            f'<span class="rule"></span></div>' + "".join(parts)
        )

    readout = (
        f"<b>{model['total_skills']}</b> skills&nbsp;&nbsp;"
        f"<b>{model['total_agents']}</b> subagents"
    )
    body = block("Skills", model["groups"])
    if model["agents"]:
        body += block("Subagents", model["agents"])
    return page("skills", readout, body, with_filter=True)


def _dispatch_btn(kind: str, target: str, label: str, confirm: str) -> str:
    """A two-step-confirm dispatch button (R8). The id is content-derived from
    kind + target exactly as build_action_registry keys it, so the POST it
    fires validates against the current registry; the client sends only that
    opaque id (R9)."""
    aid = _entity_id(kind, target)
    return (
        f'<button class="btn act" data-act="dispatch" data-id="{esc(aid)}" '
        f'data-confirm="{esc(confirm)}" title="{esc(confirm)}">{esc(label)}</button>'
    )


def _unblock_recheck_btns(path: str, unblock: dict | None, label: str, git_root: bool) -> str:
    """Both dispatch buttons for a waiting-spec header or a blocked task file
    (unblock-next-steps R7). Gated identically to _add_unblock_recheck() in the
    action registry — git-repo root, truthy path, truthy unblock, non-`ask` —
    so every button POSTs a `data-id` the registry actually generated. Empty
    string when any gate fails."""
    if not git_root or not path or not unblock or unblock.get("type") == "ask":
        return ""
    ub = _dispatch_btn("unblock", path, f"unblock: {label}",
        f"Unblock {label}? Launches a Claude agent to act on the unblock step "
        "(agent with write access, costs tokens).")
    rc = _dispatch_btn("recheck", path, f"recheck: {label}",
        f"Recheck {label}? Launches a Claude agent to re-verify whether the "
        "blocker cleared (costs tokens).")
    return ub + rc


def _is_answer_item(i: dict) -> bool:
    """A needs-your-answer inbox item: an ask-typed unblock or a deferred
    question the human must resolve. The scanner marks these `needs-answer`;
    the structured unblock/deferred fields are honored too, for forward-compat."""
    return (
        i.get("state") == "needs-answer"
        or (i.get("unblock") or {}).get("type") == "ask"
        or bool(i.get("deferred_questions"))
    )


def _unblock_missing(i: dict) -> bool:
    """A blocked item with no recorded Unblock: step — flag it so the user
    knows to add one. Driven by the scanner's structured `unblock_missing`
    flag (task 06); older scan JSON without the key defaults to unflagged."""
    return bool(i.get("unblock_missing"))


# Session-refresh budget arms (spec session-refresh-automation): a live session
# is flagged over EITHER arm. Pinned from the 30-day profile — 3 is the re-prime
# median (the behavior being changed) and 250k sits in the heavy context tail.
REPRIME_BUDGET = 3
CTX_BUDGET = 250_000


def _reprime_flags(
    b: dict, summary: dict | None, summary_mtime: float | None
) -> list[dict]:
    """Needs-attention inbox items for live sessions over a session-refresh
    budget arm (R4): `reprime_count` >= REPRIME_BUDGET OR `p90_ctx` >= CTX_BUDGET.

    The join is the live-session scan's ids against the summary's `sessions`
    keys, exactly — a live session absent from the summary is not flagged. Each
    flag names the session, which arm tripped, the re-prime count + cost, and
    the summary file's mtime (the freshness bound). Older summary JSON without
    `reprime_count` treats that arm as 0; the p90_ctx arm still evaluates."""
    sessions = (summary or {}).get("sessions") or {}
    if not sessions:
        return []
    stamp = _dt(summary_mtime) if summary_mtime else "unknown"
    flags = []
    for r in b.get("repos", []):
        for s in r.get("sessions", []):
            if s.get("state") != "active":
                continue
            sess = sessions.get(s.get("sid"))
            if not sess:  # not tracked in the summary -> never flagged
                continue
            count = sess.get("reprime_count", 0) or 0
            ctx = sess.get("p90_ctx", 0) or 0
            arms = []
            if count >= REPRIME_BUDGET:
                arms.append("re-prime")
            if ctx >= CTX_BUDGET:
                arms.append("context")
            if not arms:
                continue
            dollars = (sess.get("reprime_cost_microusd", 0) or 0) / 1_000_000
            flags.append(
                {
                    "sev": "warning",
                    "state": "over-budget",
                    "item": f"session {s['sid']} over budget",
                    "repo": r["name"],
                    "why": (
                        f"{' + '.join(arms)} budget tripped — {count} re-primes, "
                        f"${dollars:,.2f}; summary {stamp}"
                    ),
                    "age": summary_mtime or 0,
                    "cmd": "",
                    "unblock": None,
                    "deferred_questions": [],
                }
            )
    return flags


def render_workboard(
    b: dict, cost: dict | None = None, summary_mtime: float | None = None
) -> str:
    inbox_items = list(b["inbox"]) + _reprime_flags(b, cost, summary_mtime)

    def chip(state):
        return f'<span class="chip {esc(state)}">{esc(state)}</span>'

    def tile(v, label, attr, cls=""):
        return (
            f'<button class="tile {cls}" {attr}>'
            f'<div class="v">{v}</div><div class="l">{esc(label)}</div></button>'
        )

    # Cost (7d): the summary dict is read+passed by the HTTP handler (R6);
    # this function stays pure. A missing summary (cost is None) renders an
    # explicit pending state, never an error (R7).
    def _usd(microusd):
        try:
            return f"${(microusd or 0) / 1_000_000:,.2f}"
        except (TypeError, ValueError):
            return "$0.00"

    def _cost_rows(dim):
        top = sorted(
            (dim or {}).items(),
            key=lambda kv: (kv[1] or {}).get("cost_microusd", 0),
            reverse=True,
        )[:5]
        return (
            "".join(
                f'<div class="line"><span class="trunc">{esc(name)}</span>'
                f'<span class="meta">{_usd((v or {}).get("cost_microusd", 0))}</span></div>'
                for name, v in top
            )
            or '<div class="zero">None.</div>'
        )

    if cost is None:
        cost_value = "—"
        cost_body = (
            '<div class="zero">Cost data pending — run a refresh to populate '
            "the 7-day window.</div>"
        )
    else:
        cost_value = _usd((cost.get("totals") or {}).get("cost_microusd", 0))
        cost_body = (
            '<div class="sub">By model</div>'
            + _cost_rows(cost.get("by_model"))
            + '<div class="sub">By skill</div>'
            + _cost_rows(cost.get("by_skill"))
            + '<div class="sub">By project</div>'
            + _cost_rows(cost.get("by_project"))
        )
        # One re-prime line: count + cost for the window (spec R4). Sourced from
        # the `reprime` section of the summary JSON. Older caches carry no
        # `reprime` section — the line is simply omitted (no error, no
        # placeholder), so the panel renders exactly as before.
        reprime = cost.get("reprime")
        if reprime:
            n = reprime.get("count", 0)
            cost_body += (
                '<div class="sub">Re-prime (7d)</div>'
                f'<div class="line"><span class="trunc">{esc(str(n))} re-primes</span>'
                f'<span class="meta">{_usd(reprime.get("cost_microusd", 0))}</span></div>'
            )
        # One untyped-fanout guard line: calls (+ deepest nesting) and cost of
        # dispatch through untyped catch-all agent frames (spec R4). Absent from
        # older caches with no `untyped_fanout` section — the line is simply
        # omitted, so the panel renders exactly as before.
        fanout = cost.get("untyped_fanout")
        if fanout:
            calls = fanout.get("calls", 0)
            depth = fanout.get("max_depth", 0)
            cost_body += (
                '<div class="sub">Untyped fan-out (7d)</div>'
                f'<div class="line"><span class="trunc">{esc(str(calls))} calls · '
                f"depth {esc(str(depth))}</span>"
                f'<span class="meta">{_usd(fanout.get("cost_microusd", 0))}</span></div>'
            )
    cost_panel = (
        f'<div class="panel" id="panel-cost"><div class="sub">Cost (7d) · '
        f"{cost_value}</div>{cost_body}</div>"
    )

    tiles = "".join(
        [
            tile(b["n_repos"], "repos", 'data-scroll="#repos"'),
            tile(b["n_open_specs"], "open specs", 'data-panel="specs"'),
            tile(b["n_open_tasks"], "open tasks", 'data-panel="tasks"'),
            tile(b["n_active"], "active sessions", 'data-panel="active"'),
            tile(cost_value, "cost (7d)", 'data-panel="cost"'),
            tile(
                len(inbox_items),
                "needs attention",
                'data-scroll="#inbox"',
                "alert" if inbox_items else "",
            ),
        ]
    )

    # Drill-down panels (revealed by clicking a tile) — built from live board data
    def panel_rows(items, fmt):
        return "".join(fmt(x) for x in items) or '<div class="zero">None.</div>'

    specs_panel = panel_rows(
        b["open_specs"],
        lambda s: (
            f'<div class="line"><span class="trunc">{esc(s["title"])}</span>'
            f'<span class="meta">{s["done"]}/{s["total"]}</span>'
            f'<span class="meta">{esc(s["repo"])} · {_ago(s["mtime"])}</span></div>'
        ),
    )
    tasks_panel = panel_rows(
        b["task_repos"],
        lambda t: (
            f'<div class="line"><span class="trunc">{esc(t["next"] or "—")}</span>'
            f'<span class="meta">{t["open"]}/{t["total"]}</span>'
            f'<span class="meta">{esc(t["repo"])}</span></div>'
        ),
    )
    active_panel = panel_rows(
        b["actives"],
        lambda a: (
            f'<div class="line"><span class="trunc">{esc(a["prompt"][:90] or "—")}</span>'
            f'<span class="meta">{esc(a["branch"])}</span>'
            f'<span class="meta">{esc(a["repo"])} · {_ago(a["last"])}</span></div>'
        ),
    )
    panels = (
        f'<div class="panel" id="panel-specs"><div class="sub">Open specs · {len(b["open_specs"])}</div>{specs_panel}</div>'
        f'<div class="panel" id="panel-tasks"><div class="sub">Repos with open tasks · {len(b["task_repos"])}</div>{tasks_panel}</div>'
        f'<div class="panel" id="panel-active"><div class="sub">Active sessions · {len(b["actives"])}</div>{active_panel}</div>'
        f"{cost_panel}"
    )

    def inbox_row(i, *, answerable):
        # Answer rows are human-decision-only: never a dispatch command. Blocked
        # rows lacking a recorded unblock get a warning chip nudging an Unblock: line.
        badge = chip(i["state"])
        if not answerable and _unblock_missing(i):
            badge += '<span class="chip warn">no unblock</span>'
        cmd = f" <code>{esc(i['cmd'])}</code>" if i["cmd"] and not answerable else ""
        return (
            f'<div class="row" data-text="{esc((i["item"] + " " + i["why"] + " " + i["repo"]).lower())}">{badge}'
            f'<div><div class="what">{esc(i["item"])}</div>'
            f'<div class="why">{esc(i["why"])}{cmd}</div></div>'
            f'<div class="repo">{esc(i["repo"])}</div>'
            f'<div class="age">{_ago(i["age"])}</div></div>'
        )

    if not inbox_items:
        inbox = '<div class="inbox"><div class="zero">Nothing needs you.</div></div>'
    else:
        answer_items = [i for i in inbox_items if _is_answer_item(i)]
        rest_items = [i for i in inbox_items if not _is_answer_item(i)]
        inbox = ""
        if answer_items:  # grouped first, visually distinct, no dispatch (R6)
            arows = "".join(inbox_row(i, answerable=True) for i in answer_items)
            inbox += (
                '<div class="inbox needs-answer">'
                '<div class="ihead">Needs your answer</div>'
                f"{arows}</div>"
            )
        if rest_items:
            rrows = "".join(inbox_row(i, answerable=False) for i in rest_items)
            inbox += f'<div class="inbox">{rrows}</div>'

    repo_blocks = []
    for r in sorted(b["repos"], key=lambda r: (not _repo_has_work(r), r["name"])):
        g = r["git"]
        git_root = _is_git_root(r.get("path") or "")  # R5b: dispatches only here
        chips = []
        if g.get("branch"):
            chips.append(f'<span class="gchip">{esc(g["branch"])}</span>')
        if g.get("dirty"):
            chips.append(f'<span class="gchip warn">{g["dirty"]}&#916;</span>')
        if g.get("ahead"):
            if r.get("path"):  # a one-click push for the unpushed commits
                pid = _entity_id("push", r["path"])
                chips.append(
                    f'<button class="gchip warn act" data-act="push" '
                    f'data-id="{esc(pid)}" data-name="{esc(r["name"])}" '
                    f'title="git push">push &#8593;{g["ahead"]}</button>'
                )
            else:
                chips.append(f'<span class="gchip warn">&#8593;{g["ahead"]}</span>')
        if g.get("behind"):
            chips.append(f'<span class="gchip">&#8595;{g["behind"]}</span>')
        inner = []
        if r["specs"]:
            lines = []
            for sp in r["specs"]:
                pct = int(100 * sp["done"] / sp["total"]) if sp["total"] else 0
                prog = (
                    f'<span class="prog"><span class="meta">{sp["done"]}/{sp["total"]}</span>'
                    f'<span class="bar"><i style="width:{pct}%"></i></span></span>'
                    if sp["total"]
                    else f'<span class="meta">{esc(sp["status"] or "—")}</span>'
                )
                graph = viz.dag(sp.get("tasks", []))
                title_el = (
                    f'<a class="trunc" href="/spec/{esc(sp["id"])}">{esc(sp["title"])}</a>'
                    if sp.get("id")
                    else f'<span class="trunc">{esc(sp["title"])}</span>'
                )
                disp = ""
                if git_root and sp.get("path") and sp["total"]:
                    if sp["done"] < sp["total"]:
                        disp = _dispatch_btn(
                            "dispatch-drain",
                            sp["path"],
                            f"drain {sp['slug']}",
                            f"Drain specs/{sp['slug']} in {r['name']}? Launches a "
                            "Claude /drain session (agent with write access, costs tokens).",
                        )
                    else:
                        disp = _dispatch_btn(
                            "dispatch-verify",
                            sp["path"],
                            f"verify {sp['slug']}",
                            f"Verify specs/{sp['slug']} in {r['name']}? Launches the "
                            "verifier agent (costs tokens).",
                        )
                # unblock/recheck (R7): the waiting-spec header keys on the
                # spec path; each non-ask blocked task keys on its own file
                # path. Not gated on sp["total"] — a waiting spec often has 0.
                ub = _unblock_recheck_btns(
                    sp.get("path", ""), sp.get("unblock"), f"spec {sp['slug']}", git_root
                )
                bt_lines = []
                for bt in sp.get("blocked_tasks") or []:
                    tpath = bt.get("path") or ""
                    tlabel = bt.get("title") or (os.path.basename(tpath) if tpath else "")
                    btns = _unblock_recheck_btns(tpath, bt.get("unblock"), tlabel, git_root)
                    if btns:
                        bt_lines.append(
                            f'<div class="line evt"><span class="trunc">{esc(tlabel)}</span>{btns}</div>'
                        )
                bt_block = "".join(bt_lines)
                row = (
                    f"{title_el}"
                    f'{prog}<span class="meta">{_ago(sp["mtime"])}</span>{disp}{ub}'
                )
                prio = _prio_select(sp.get("path", ""), sp.get("priority", ""))
                if graph:  # expandable to the dependency graph
                    # Human-blocked nodes auto-expand: the human's blockers
                    # are visible per repo without hunting; agent-bounded
                    # ones stay collapsed and proceed.
                    is_open = any(
                        t.get("blocker") == "human" for t in sp.get("tasks", [])
                    )
                    item = (
                        f'<details class="spec" data-k="s:{esc(r["name"])}/{esc(sp["slug"])}"'
                        f"{' open' if is_open else ''}>"
                        f'<summary><div class="line">{row}</div>'
                        f"</summary>{graph}{bt_block}</details>"
                    )
                else:
                    item = f'<div class="line plain">{row}</div>{bt_block}'
                lines.append(f'<div class="specrow">{prio}{item}</div>')
            inner.append(f'<div class="sub">Specs</div>{"".join(lines)}')
        if r["tasks"] and r["tasks"]["total"]:
            t = r["tasks"]
            nxt = (
                f'<span class="trunc">{esc(t["next"])}</span>'
                if t["next"]
                else '<span class="trunc" style="color:var(--faint)">all done</span>'
            )
            inner.append(
                f'<div class="sub">Tasks · {t["open"]} open / {t["total"]}</div>'
                f'<div class="line">{nxt}<span></span>'
                f'<span class="meta">{_ago(t["mtime"])}</span></div>'
            )
        vis = [s for s in r["sessions"] if s["state"] in ("active", "recent")]
        if vis:
            rows = [
                {
                    "label": s["prompt"][:90] or "—",
                    "status": s["state"],
                    "start_ts": s["start_ts"],
                    "end_ts": s["last"],
                    "tooltip": f"{s['branch']} · {_ago(s['last'])}"
                    if s["branch"]
                    else _ago(s["last"]),
                    "href": f"http://127.0.0.1:8901/ui/flamegraph?tf=session={quote(s['sid'], safe='')}",
                }
                for s in vis[:6]
            ]
            more = len(vis) - 6
            extra = (
                f'<div class="line"><span class="meta">+{more} more</span></div>'
                if more > 0
                else ""
            )
            inner.append(f'<div class="sub">Sessions</div>{viz.timeline(rows)}{extra}')
        if r["handoffs"]:
            lines = "".join(
                f'<div class="line evt">{chip("blocked")}'
                + (
                    f'<a class="trunc" href="/file/{esc(h["id"])}">{esc(h["title"])}</a>'
                    if h.get("id")
                    else f'<span class="trunc">{esc(h["title"])}</span>'
                )
                + f'<span class="meta">{_ago(h["mtime"])}</span>'
                + (
                    _dispatch_btn(
                        "dispatch-resume-handoff",
                        h["path"],
                        "resume",
                        f'Resume the handoff "{h["title"]}" in {r["name"]}? Launches a '
                        "Claude session to finish it (costs tokens).",
                    )
                    if git_root and h.get("path")
                    else ""
                )
                + "</div>"
                for h in r["handoffs"]
            )
            inner.append(f'<div class="sub">Handoffs</div>{lines}')

        gh = r.get("gh", {})
        if gh.get("slug"):
            v = gh.get("visibility") or "gh"
            ghbadge = (
                f'<a class="ghb {esc(v)}" href="{esc(gh["url"])}" target="_blank" '
                f'rel="noopener" title="{esc(gh["slug"])}">{esc(v)}</a>'
            )
        else:
            ghbadge = '<span class="ghb local">local</span>'
        commit = ""
        if g.get("hash"):
            commit = (
                f'<span class="commit"><span class="chash">{esc(g["hash"])}</span>'
                f'<span class="csub">{esc(g.get("commit_subject", ""))}</span>'
                f'<span class="cwhen">{_dt(g.get("commit_ts", 0))} · {_ago(g.get("commit_ts", 0))}</span></span>'
            )

        rn = (
            f'<a class="rn" href="/repo/{esc(r["id"])}">{esc(r["name"])}</a>'
            if r.get("id")
            else f'<span class="rn">{esc(r["name"])}</span>'
        )
        open_attr = " open" if _repo_has_work(r) else ""
        body = (
            f'<div class="rbody">{"".join(inner)}</div>'
            if inner
            else '<div class="rbody"><div class="zero" style="padding:8px 0">No open work.</div></div>'
        )
        # Filter text: repo name + spec titles/slugs + handoff titles, so
        # typing a name or slug fragment narrows the board (client-side #q).
        text_bits = [r["name"]]
        for sp in r["specs"]:
            text_bits += [sp["title"], sp.get("slug", "")]
        text_bits += [h["title"] for h in r["handoffs"]]
        data_text = esc(" ".join(t for t in text_bits if t).lower())
        repo_blocks.append(
            f'<details class="repo"{open_attr} data-k="r:{esc(r["name"])}" '
            f'data-text="{data_text}"><summary>'
            f"{rn}{ghbadge}{''.join(chips)}"
            f"{commit}</summary>{body}</details>"
        )

    orphan = ""
    if b["orphans"]:
        lines = "".join(
            f'<div class="line evt">{chip(s["state"])}'
            f'<span class="trunc">{esc(s["prompt"][:90] or "—")}</span>'
            f'<span class="meta">{esc(s["repo"])} · {_ago(s["last"])}</span></div>'
            for s in b["orphans"][:12]
        )
        orphan = (
            f'<div class="eyebrow"><span class="key">sessions outside tracked repos</span>'
            f'<span class="rule"></span></div><div class="repo"><div class="rbody">{lines}</div></div>'
        )

    readout = (
        f"<b>{b['n_repos']}</b> repos&nbsp;&nbsp;<b>{b['n_open_tasks']}</b> open&nbsp;&nbsp;"
        f"<b>{len(inbox_items)}</b> need you"
    )
    health = "".join(
        f'<div class="health">source check · {esc(h)}</div>'
        for h in b.get("health", [])
    )

    # Agents control panel: kick off, stop running, resume recent.
    kick_opts = "".join(
        f'<option value="{esc(n)}">{esc(n)}</option>' for n in b.get("repo_names", [])
    )
    kickoff = (
        '<form class="kickoff" onsubmit="return false">'
        '<input name="prompt" type="text" autocomplete="off" '
        'placeholder="prompt for a new background agent…">'
        f'<select name="cwd" aria-label="repo">{kick_opts}</select>'
        '<button class="btn go" data-act="start">Start</button></form>'
    )
    running_html = (
        "".join(
            f'<div class="line evt"><span class="chip active">{esc(a["status"] or "running")}</span>'
            f'<span class="trunc">{esc(a["name"] or a["sid"][:8])} '
            f'<span class="acwd">{esc(a["cwd"])}</span></span>'
            f'<button class="btn stop" data-act="stop" data-pid="{a["pid"]}" '
            f'data-name="{esc(a["name"])}">stop</button></div>'
            for a in b.get("agents", [])
            if a.get("pid")
        )
        or '<div class="zero" style="padding:6px 0">No running agents.</div>'
    )
    resumable = b.get("resumable", [])
    resume_html = (
        '<div class="sub">Recent — resume</div>'
        + "".join(
            f'<div class="line evt"><span class="chip idle">ended</span>'
            f'<span class="trunc">{esc(a["name"] or a["sid"][:8])} '
            f'<span class="acwd">{esc(a["cwd"])}</span></span>'
            f'<button class="btn" data-act="resume" data-sid="{esc(a["sid"])}" '
            f'data-name="{esc(a["name"])}">resume</button></div>'
            for a in resumable
        )
        if resumable
        else ""
    )
    agents_html = (
        f'<div class="eyebrow" id="agents"><span class="key" style="color:var(--text)">Agents</span>'
        f'<span class="rule"></span><span class="n">{len([a for a in b.get("agents", []) if a.get("pid")])} running</span></div>'
        f'<div class="agents">{kickoff}<div class="sub">Running</div>{running_html}{resume_html}</div>'
    )
    profile_html = (
        '<div class="eyebrow"><span class="key" style="color:var(--text)">Profile</span>'
        '<span class="rule"></span></div>'
        '<div class="agents"><button class="btn" data-act="refresh-profile">'
        "Refresh profile</button></div>"
    )

    body = (
        f"{health}"
        f'<div class="tiles">{tiles}</div>{panels}'
        f'<div class="eyebrow" id="inbox"><span class="key" style="color:var(--text)">Needs attention</span>'
        f'<span class="rule"></span></div>{inbox}'
        f"{agents_html}"
        f"{profile_html}"
        f'<div class="eyebrow" id="repos"><span class="key" style="color:var(--text)">Repos</span>'
        f'<span class="rule"></span></div>{"".join(repo_blocks)}{orphan}'
    )
    return page("workboard", readout, body, with_filter=True)


# Board (kanban) view: same board scan render_workboard consumes, regrouped
# into seven fixed status columns instead of a per-repo list (SPEC.md R1-R9).
# Read-only — no POST/write route, no drag handlers.
_KANBAN_COLUMNS = (
    "Pending",
    "In Progress",
    "Needs Verification",
    "Blocked",
    "Done",
    "Deferred",
    "Skipped",
)
_KANBAN_COLLAPSED = {"Done", "Deferred", "Skipped"}


def render_workboard_kanban(b: dict) -> str:
    buckets: dict[str, list[str]] = {c: [] for c in _KANBAN_COLUMNS}
    for r in b["repos"]:
        repo = r["name"]
        for sp in r["specs"]:
            slug = sp["slug"]
            spec_id = sp.get("id", "")
            priority = sp.get("priority", "")
            for t in sp.get("tasks", []):
                title = t["title"]
                col = _kanban_column(t["status"])
                data_text = esc(f"{repo} {slug} {title}".lower())
                link = (
                    f'<a href="/spec/{esc(spec_id)}">{esc(title)}</a>'
                    if spec_id
                    else esc(title)
                )
                prio = f'<span class="prio">{esc(priority)}</span>' if priority else ""
                buckets[col].append(
                    f'<div class="kanban-card" data-text="{data_text}">'
                    f'<div class="card-title">{link}</div>'
                    f'<div class="card-meta">'
                    f'<span class="badge">{esc(repo)}:{esc(slug)}</span>{prio}'
                    f"</div></div>"
                )

    columns = []
    for c in _KANBAN_COLUMNS:
        cards = buckets[c]
        head = (
            f'<span class="col-head">{esc(c)}</span>'
            f'<span class="count">{len(cards)}</span>'
        )
        inner = "".join(cards) or '<div class="zero">None.</div>'
        if c in _KANBAN_COLLAPSED:
            col = (
                '<div class="kanban-column"><details>'
                f"<summary>{head}</summary>"
                f'<div class="col-cards">{inner}</div></details></div>'
            )
        else:
            col = (
                '<div class="kanban-column">'
                f'<div class="col-header">{head}</div>'
                f'<div class="col-cards">{inner}</div></div>'
            )
        columns.append(col)

    # One column per line so each closed column's <details> is line-isolated
    # (the board's HTML is otherwise a single run).
    body = '<div class="kanban-board">\n' + "\n".join(columns) + "\n</div>"
    readout = (
        f'<div class="line"><span class="trunc">{b["n_open_specs"]} open specs · '
        f"{b['n_open_tasks']} open tasks · {b['n_repos']} repos</span></div>"
    )
    return page("board", readout, body, with_filter=True)


def _repo_has_work(r: dict) -> bool:
    g = r["git"]
    return bool(
        g.get("dirty")
        or g.get("ahead")
        or r["handoffs"]
        or any(s["state"] in ("active", "recent") for s in r["sessions"])
        or any(sp["total"] and sp["done"] < sp["total"] for sp in r["specs"])
        or (r["tasks"] and r["tasks"]["open"])
    )


# --------------------------------------------------------------------------- #
# Mutations & control (the only write/exec surface) — POST-only, CSRF-guarded
# --------------------------------------------------------------------------- #
# Per-process token: a same-origin page carries it; cross-origin/other-process
# POSTs (CSRF, DNS-rebind) can't read it, so they're rejected. Not auth — a
# same-machine barrier appropriate for a single-user localhost service.
CSRF_TOKEN = secrets.token_urlsafe(24)


def _tracked_repo_reals() -> set[str]:
    """Repos a gated mutation will accept: the union of REPOS.md
    (`parse_repos()`) and the Workboard's own repo-discovery walk
    (`workboard.find_repos(default_roots())`). The two sources can diverge, so
    unioning them keeps a repo visible on the board from being rejected by a
    priority edit or agent kickoff (or vice versa). Fail soft: a failed walk
    still yields the REPOS.md set."""
    reals = {os.path.realpath(str(r)) for r in parse_repos()}
    try:
        reals |= {
            os.path.realpath(str(r))
            for r in workboard.find_repos(workboard.default_roots(), max_depth=3)
        }
    except Exception:
        pass
    return reals


def _claude_run_bg(args: list[str], cwd: str):
    """Spawn a detached background `claude` process; don't wait on it."""
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("claude not found on PATH")
    subprocess.Popen(
        [claude, *args],
        cwd=cwd,
        env=GIT_ENV,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _invalidate_board() -> None:
    """Force the next get_board() to rescan: an executed action likely changed
    the state the board reflects (a push clears the repo's `ahead` chip)."""
    with _board_lock:
        _board_cache["ts"] = 0.0


def execute_push(action: dict) -> dict:
    """Run a `push` action's argv (git push, no shell), capturing combined
    stdout+stderr and the exit code. A non-zero exit is reported, never retried;
    a success invalidates the board cache so the next render drops the stale
    `ahead` chip. Returns {code, body} for the POST handler to serialize."""
    try:
        proc = subprocess.run(
            action["argv"],
            capture_output=True,
            text=True,
            timeout=ACTION_TIMEOUT,
            env=GIT_ENV,
        )
    except subprocess.TimeoutExpired:
        return {
            "code": 200,
            "body": {
                "ok": False,
                "kind": "push",
                "exit": None,
                "output": "",
                "message": f"git push timed out after {ACTION_TIMEOUT}s",
            },
        }
    output = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0
    if ok:
        _invalidate_board()
    return {
        "code": 200,
        "body": {
            "ok": ok,
            "kind": "push",
            "exit": proc.returncode,
            "output": output,
            "message": "pushed" if ok else f"git push exited {proc.returncode}",
        },
    }


# Every dispatch runs an agentic `claude` session with write access to the
# target repo — that is the point of a dispatch button (R5). The elevation is
# recorded here, deliberate, and kept local-only by the Host check + CSRF token
# (R2/R2a): the flag set is the headless one the drain/build reference docs
# document — a non-interactive permission mode (`dontAsk` aborts rather than
# hangs on an unapproved tool), a tool allowlist broad enough to orchestrate a
# drain / run the verifier / resume a handoff, and a hard `--max-turns` cap.
_DISPATCH_PERMISSION_MODE = "dontAsk"
_DISPATCH_ALLOWED_TOOLS = "Read,Edit,Write,Glob,Grep,Task,Bash"
_DISPATCH_MAX_TURNS = "80"
_DISPATCH_ARGS = [
    "--allowedTools",
    _DISPATCH_ALLOWED_TOOLS,
    "--permission-mode",
    _DISPATCH_PERMISSION_MODE,
    "--max-turns",
    _DISPATCH_MAX_TURNS,
]


def execute_dispatch(action: dict) -> dict:
    """Run a `dispatch-*` action: launch `claude -p <prompt>` detached in the
    target repo via the shared runtime, with the recorded permission flags. The
    prompt and cwd come wholly from the server-built registry (spec R9); a
    second dispatch for the same cwd is refused (409) by the per-cwd lock."""
    return start_dispatch(
        action["kind"], action["cwd"], action["prompt"], extra_args=_DISPATCH_ARGS
    )


def execute_stop_dispatch(action: dict) -> dict:
    """Registry executor for `stop-dispatch`: terminate the recorded dispatch's
    process group (R7). The dispatch id comes wholly from the server-built
    registry — the client supplies only the action id + confirm flag."""
    ok, msg = stop_dispatch(action.get("dispatch_id") or "")
    return {"code": 200 if ok else 409, "body": {"ok": ok, "message": msg}}


_ACTION_EXECUTORS = {
    "push": execute_push,
    "dispatch-drain": execute_dispatch,
    "dispatch-verify": execute_dispatch,
    "dispatch-resume-handoff": execute_dispatch,
    "unblock": execute_dispatch,
    "recheck": execute_dispatch,
    "stop-dispatch": execute_stop_dispatch,
}

# Destructive actions additionally require an explicit confirm flag in the POST
# body (R8's two-step confirm, mirrored server-side; R9 lists the confirm flag
# as a permitted client value). The token + Host check still gate every POST.
_CONFIRM_REQUIRED = {"stop-dispatch"}


def run_action(action_id: str, confirm: bool = False) -> dict:
    """Validate an opaque action id against the current (TTL-window) registry
    and execute it. The only client-supplied values are the id and the confirm
    flag — the argv comes wholly from the server-built registry (spec R9). An id
    not in the registry (unknown, or valid before the last rescan) -> 409 and
    nothing runs; a confirm-required action without the flag -> 400."""
    action = get_actions().get(action_id)
    if not action:
        return {
            "code": 409,
            "body": {
                "ok": False,
                "message": "unknown action id — the board state may have changed; "
                "rescan the board and try again",
            },
        }
    if action["kind"] in _CONFIRM_REQUIRED and not confirm:
        return {
            "code": 400,
            "body": {
                "ok": False,
                "message": "this action requires an explicit confirm",
            },
        }
    executor = _ACTION_EXECUTORS.get(action["kind"])
    if not executor:
        return {
            "code": 400,
            "body": {
                "ok": False,
                "message": f"unsupported action kind: {action['kind']}",
            },
        }
    return executor(action)


# --------------------------------------------------------------------------- #
# Dispatch runtime — detached `claude` runs, one log + one JSON record each
# --------------------------------------------------------------------------- #
# The generic engine (action kinds are wired in a later task): resolve the
# claude binary at dispatch time, launch it detached in its own process group,
# and persist a record so a server restart can still see it (liveness = pgid
# alive AND process start-time unchanged, so a recycled pgid never reads live).


_dispatch_procs: list = []  # live detached Popen handles (see start_dispatch)


def _resolve_claude_bin() -> str:
    """The claude binary to dispatch, resolved fresh on every call (the launchd
    service starts before a CLI upgrade may repoint the symlink): the
    `AGENT_CONSOLE_CLAUDE_BIN` override, else `claude` on PATH, else
    `~/.local/bin/claude` (launchd's PATH omits it)."""
    env = os.environ.get("AGENT_CONSOLE_CLAUDE_BIN")
    if env:
        return os.path.expanduser(env)
    return shutil.which("claude") or str(HOME / ".local" / "bin" / "claude")


def _dispatch_dir() -> Path:
    """Where dispatch logs + records live; env-overridable so tests use a
    tempdir instead of the real `~/Library/Logs/agent-console/dispatch`."""
    env = os.environ.get("AGENT_CONSOLE_DISPATCH_DIR")
    if env:
        return Path(os.path.expanduser(env))
    return HOME / "Library" / "Logs" / "agent-console" / "dispatch"


def _slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", str(s)).strip("-").lower() or "x"


def _proc_start_time(pid: int) -> str:
    """The kernel's start time for `pid` as `ps` reports it — a stable string
    that differs once the pid/pgid is recycled to another process. Empty when
    the process is gone."""
    try:
        out = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip()


def _pgid_alive(pgid: int) -> bool:
    """Signal 0 to the group: it exists (ours, or someone else's → Permission)
    unless there is no such group at all."""
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _pid_alive(pid: int) -> bool:
    """Signal 0 to a single pid — alive unless there is no such process."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _proc_command(pid: int) -> str:
    """The command line of `pid` as `ps` reports it; empty when gone. Used to
    confirm a pid we're about to signal is really a `claude` invocation (R7) —
    a recycled pid running something else won't match."""
    try:
        out = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip()


def _stop_grace() -> float:
    """Seconds to wait after SIGTERM before escalating to SIGKILL (R7's 10s
    grace). Env-overridable so tests can shrink it."""
    try:
        return float(os.environ.get("AGENT_CONSOLE_STOP_GRACE", "10"))
    except ValueError:
        return 10.0


_escalation_timers: list = []  # daemon Timers pending a SIGKILL escalation


def _signal_with_grace(term_fn, kill_fn, alive_fn, grace, on_dead=None):
    """R7 SIGTERM→SIGKILL, non-blocking: send the term signal now, then on a
    background timer escalate to the kill signal after `grace` seconds — but
    only if `alive_fn()` still reports the target alive — and run `on_dead()`
    once done. Returns the Timer so callers/tests can join it. The handler
    thread never blocks for the grace (task: never block the request for 10s)."""
    term_fn()

    def _finish():
        try:
            if alive_fn():
                kill_fn()
        except OSError:
            pass
        finally:
            if on_dead:
                on_dead()

    t = threading.Timer(grace, _finish)
    t.daemon = True
    t.start()
    _escalation_timers[:] = [x for x in _escalation_timers if x.is_alive()]
    _escalation_timers.append(t)
    return t


def _record_live(rec: dict) -> bool:
    """A record is running only if its process group is still alive AND that
    group's start time matches what we recorded — the two-part check that a
    recycled pgid cannot pass."""
    pgid = rec.get("pgid")
    start_time = rec.get("start_time") or ""
    if not isinstance(pgid, int) or not start_time:
        return False
    return _pgid_alive(pgid) and _proc_start_time(pgid) == start_time


def _load_records() -> list[dict]:
    """Every persisted dispatch record, each tagged with a live `running` flag
    from the liveness check. Read from disk on every call, so a freshly booted
    server (no memory of what it launched) reports the same truth (R5a)."""
    d = _dispatch_dir()
    out = []
    if not d.exists():
        return out
    for jf in sorted(d.glob("*.json")):
        try:
            rec = json.loads(jf.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(rec, dict):
            continue
        rec["running"] = _record_live(rec)
        out.append(rec)
    out.sort(key=lambda r: r.get("started_at") or 0, reverse=True)
    return out


def _running_dispatch_for_cwd(cwd: str) -> dict | None:
    """The live dispatch (if any) for a cwd — the per-cwd lock (R6) reads from
    the persisted records, so a restart neither drops nor duplicates the lock."""
    real = os.path.realpath(os.path.expanduser(cwd or ""))
    for rec in _load_records():
        if rec.get("running") and os.path.realpath(rec.get("cwd", "")) == real:
            return rec
    return None


def start_dispatch(kind: str, cwd: str, prompt: str, extra_args=()) -> dict:
    """Launch `claude -p <prompt> [extra_args]` detached in `cwd`, in its own
    process group (survives a server restart), streaming to one log file with a
    sibling JSON record. Refuses (409) when a dispatch is already live for the
    same cwd. The argv is built here from server-held values — the caller
    supplies kind/cwd/prompt, never a raw command line (spec R9)."""
    real = os.path.realpath(os.path.expanduser(cwd or ""))
    running = _running_dispatch_for_cwd(real)
    if running:
        return {
            "code": 409,
            "body": {
                "ok": False,
                "id": running["id"],
                "message": f"a dispatch is already running for {real} "
                f"(id {running['id']}); stop it or wait for it to finish",
            },
        }
    claude = _resolve_claude_bin()
    d = _dispatch_dir()
    d.mkdir(parents=True, exist_ok=True)
    did = (
        f"{time.strftime('%Y%m%dT%H%M%S')}-{_slug(kind)}"
        f"-{_slug(os.path.basename(real) or kind)}-{secrets.token_hex(3)}"
    )
    log_path = d / f"{did}.log"
    argv = [claude, "-p", prompt, *extra_args]
    logf = open(log_path, "ab")
    try:
        proc = subprocess.Popen(
            argv,
            cwd=real,
            env=GIT_ENV,
            stdin=subprocess.DEVNULL,
            stdout=logf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        logf.close()
    # Hold the handle so it isn't finalized while the detached child still runs
    # (a GC'd running Popen warns); prune exited ones so the list stays small.
    _dispatch_procs[:] = [p for p in _dispatch_procs if p.poll() is None]
    _dispatch_procs.append(proc)
    pgid = proc.pid  # start_new_session makes the child its group/session leader
    rec = {
        "id": did,
        "kind": kind,
        "cwd": real,
        "pgid": pgid,
        "start_time": _proc_start_time(pgid),
        "started_at": time.time(),
        "log": str(log_path),
        "state": "running",
        "exit_code": None,
    }
    (d / f"{did}.json").write_text(json.dumps(rec), encoding="utf-8")
    # Rebuild the board next scan so the new dispatch's `stop-dispatch` action
    # enters the registry immediately (R8: no manual rescan to stop it).
    _invalidate_board()
    return {
        "code": 200,
        "body": {
            "ok": True,
            "id": did,
            "log": str(log_path),
            "message": f"dispatched {kind} in {real}",
        },
    }


def _find_record(dispatch_id: str) -> tuple[dict | None, Path | None]:
    """Load a single dispatch record + its json path by id, or (None, None)."""
    if not dispatch_id:
        return None, None
    jf = _dispatch_dir() / f"{dispatch_id}.json"
    try:
        rec = json.loads(jf.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    return (rec, jf) if isinstance(rec, dict) else (None, None)


def _record_stopped(jf: Path) -> None:
    """Persist a stopped dispatch's terminal state (task: record exit state).
    exit_code comes from a retained Popen handle when we still hold one (the
    dispatch started in this process); otherwise it is left as recorded."""
    try:
        rec = json.loads(jf.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    proc = next((p for p in _dispatch_procs if p.pid == rec.get("pgid")), None)
    rec["state"] = "stopped"
    if proc is not None:
        rec["exit_code"] = proc.poll()
    try:
        jf.write_text(json.dumps(rec), encoding="utf-8")
    except OSError:
        pass


def stop_dispatch(dispatch_id: str) -> tuple[bool, str]:
    """R7: terminate a dispatch this server started — SIGTERM to its process
    group, SIGKILL after the grace only if it ignores the term. Signals only
    when the recorded pgid is still alive AND its start time matches
    (`_record_live`), so a recycled pgid is never signaled."""
    rec, jf = _find_record(dispatch_id)
    if not rec:
        return False, "unknown dispatch id"
    if not _record_live(rec):
        return False, "dispatch is not running (already exited)"
    pgid = rec["pgid"]
    _signal_with_grace(
        term_fn=lambda: os.killpg(pgid, signal.SIGTERM),
        kill_fn=lambda: os.killpg(pgid, signal.SIGKILL),
        alive_fn=lambda: _record_live(rec),
        grace=_stop_grace(),
        on_dead=lambda: _record_stopped(jf),
    )
    _invalidate_board()
    return True, "stopping dispatch (SIGTERM; SIGKILL after grace)"


def render_dispatches(records: list[dict]) -> str:
    """The `/dispatches` page: one row per persisted dispatch (state, start,
    exit code, log link, cwd)."""
    rows = []
    for r in records:
        state = "running" if r.get("running") else "exited"
        exit_code = r.get("exit_code")
        exit_txt = "—" if exit_code is None else str(exit_code)
        did = r.get("id", "")
        # A running dispatch gets a two-step-confirm stop button (R8); the id
        # matches the registry's stop-dispatch action so the POST validates.
        if r.get("running"):
            aid = _entity_id("stop-dispatch", r.get("log") or did)
            confirm = f"Stop this {r.get('kind', 'dispatch')} dispatch (SIGTERM)?"
            act = (
                f'<button class="btn stop act" data-act="stop-dispatch" '
                f'data-id="{esc(aid)}" data-confirm="{esc(confirm)}">stop</button>'
            )
        else:
            act = "—"
        rows.append(
            f"<tr><td>{esc(r.get('kind', ''))}</td><td>{esc(state)}</td>"
            f"<td>{esc(_ago(r.get('started_at') or 0))}</td>"
            f"<td>{esc(exit_txt)}</td>"
            f'<td><a href="/dispatch/{esc(did)}/log">log</a></td>'
            f"<td>{esc(r.get('cwd', ''))}</td><td>{act}</td></tr>"
        )
    if rows:
        body = (
            "<table><thead><tr><th>kind</th><th>state</th><th>started</th>"
            "<th>exit</th><th>log</th><th>cwd</th><th></th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    else:
        body = "<p>No dispatches yet.</p>"
    return render_detail_page("Dispatches", body)


def apply_priority(text: str, value: str) -> str:
    """Pure: return `text` with its `Priority:` line set to `value` (or removed
    when value == ""). Inserts under Status:, else after the H1 title."""
    has_line = bool(re.search(r"^Priority:.*$", text, re.M))
    if value:
        repl = f"Priority: {value}"
        if has_line:
            return re.sub(r"^Priority:.*$", repl, text, count=1, flags=re.M)
        if re.search(r"^Status:.*$", text, re.M):
            return re.sub(r"^(Status:.*)$", r"\1\n" + repl, text, count=1, flags=re.M)
        return re.sub(r"^(#\s+.+)$", r"\1\n\n" + repl, text, count=1, flags=re.M)
    if not has_line:
        return text
    return re.sub(r"^Priority:.*\n?", "", text, count=1, flags=re.M)


def set_priority(spec_path: str, value: str) -> tuple[bool, str]:
    """Rewrite a SPEC.md's `Priority:` line and auto-commit. Validates the path
    is a SPEC.md inside a tracked repo's specs/ tree."""
    if value not in PRIORITIES and value != "":
        return False, "bad priority"
    real = os.path.realpath(spec_path)
    if os.path.basename(real) != "SPEC.md" or f"{os.sep}specs{os.sep}" not in real:
        return False, "not a spec file"
    repo = next((r for r in _tracked_repo_reals() if real.startswith(r + os.sep)), None)
    if not repo:
        return False, "outside tracked repos"
    p = Path(real)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        return False, str(e)
    new = apply_priority(text, value)
    if new == text:
        return True, "no change"
    try:
        p.write_text(new, encoding="utf-8")
    except OSError as e:
        return False, str(e)
    _git(Path(repo), "add", real)
    _git(
        Path(repo),
        "-c",
        "user.name=agent-console",
        "-c",
        "user.email=agent-console@localhost",
        "commit",
        "-m",
        f"chore(priority): {os.path.relpath(real, repo)} -> {value or 'unset'}",
        "--",
        real,
    )
    _plugins_cache["ts"] = 0  # (no-op for board, but force next board rebuild)
    _board_cache["ts"] = 0
    return True, "ok"


def start_agent(cwd: str, prompt: str) -> tuple[bool, str]:
    prompt = (prompt or "").strip()
    if not prompt:
        return False, "empty prompt"
    real = os.path.realpath(os.path.expanduser(cwd or ""))
    if real not in _tracked_repo_reals():
        return False, "cwd is not a tracked repo"
    try:
        _claude_run_bg(["--bg", "-p", prompt], real)
    except (OSError, RuntimeError) as e:
        return False, str(e)
    _board_cache["ts"] = 0
    return True, "started"


def _verify_session_pid(pid: int) -> tuple[bool, str]:
    """R7 stop-session verification: the pid must have a session record, the
    live process must be a `claude` invocation, and its kernel start time must
    match the record's `procStart` — a pid reassigned to another process fails
    this and is never signaled (recycled-pid guard)."""
    try:
        rec = json.loads((PID_DIR / f"{pid}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "no session record for pid"
    if not _pid_alive(pid):
        return False, "session process is not alive"
    if "claude" not in _proc_command(pid).lower():
        return False, "pid is not a claude process"
    proc_start = rec.get("procStart") or ""
    if not proc_start or _proc_start_time(pid) != proc_start:
        return False, "process start-time mismatch (recycled pid)"
    return True, "ok"


def stop_agent(pid: int, confirm: bool = False) -> tuple[bool, str]:
    # Only signal PIDs the CLI currently reports as agent sessions — never an
    # arbitrary pid supplied by the caller.
    data = _claude_json("agents", "--all") or _claude_json("agents") or []
    live_pids = {e.get("pid") for e in data if isinstance(e, dict)}
    if pid not in live_pids:
        return False, "not a known agent pid"
    if not confirm:
        return False, "confirm required"
    ok, why = _verify_session_pid(pid)
    if not ok:
        return False, why
    _signal_with_grace(
        term_fn=lambda: os.kill(pid, signal.SIGTERM),
        kill_fn=lambda: os.kill(pid, signal.SIGKILL),
        alive_fn=lambda: _pid_alive(pid),
        grace=_stop_grace(),
    )
    _board_cache["ts"] = 0
    return True, "stopping (SIGTERM; SIGKILL after grace)"


def resume_agent(sid: str, prompt: str) -> tuple[bool, str]:
    data = _claude_json("agents", "--all") or []
    sids = {e.get("sessionId") for e in data if isinstance(e, dict)}
    if sid not in sids:
        return False, "not a known session"
    repo = next((e.get("cwd") for e in data if e.get("sessionId") == sid), None) or str(
        HOME
    )
    real = os.path.realpath(repo)
    try:
        _claude_run_bg(
            ["--bg", "--resume", sid, "-p", (prompt or "continue").strip()], real
        )
    except (OSError, RuntimeError) as e:
        return False, str(e)
    _board_cache["ts"] = 0
    return True, "resumed"


def _cost_summary_path() -> Path:
    """The rolling 7-day cost summary agentprof's hourly refresh maintains.
    Overridable for tests/deployment via `AGENT_CONSOLE_COST_SUMMARY`."""
    override = os.environ.get("AGENT_CONSOLE_COST_SUMMARY")
    if override:
        return Path(override)
    return Path.home() / ".local" / "state" / "agentprof" / "weekly-7d-summary.json"


def _read_cost_summary() -> dict | None:
    """Read the pre-aggregated cost summary JSON (a tiny file — cheap on every
    request; no subprocess, no transcript reparse). Returns None when the file
    is absent (fresh install, R7) or unreadable/malformed — the caller renders
    an explicit pending state, never a 500."""
    try:
        with open(_cost_summary_path(), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _cost_summary_mtime() -> float | None:
    """The summary file's last-modified time — the freshness bound the workboard
    re-prime flag surfaces. None when the file is absent/unstatable (R7)."""
    try:
        return _cost_summary_path().stat().st_mtime
    except OSError:
        return None


def _agentprof_refresh_script() -> Path:
    """`agentprof/scripts/refresh-profile.sh` for this checkout, derived from
    this file's own location — same pattern as `_skills_root()`."""
    return (
        Path(__file__).resolve().parent.parent
        / "agentprof"
        / "scripts"
        / "refresh-profile.sh"
    )


def refresh_profile() -> tuple[bool, str]:
    """Regenerate the agentprof profile via the repo-checked refresh script,
    then kickstart the pprof service so it serves the new file. A kickstart
    failure (e.g. the launchd service isn't installed) doesn't fail the
    call — regeneration succeeding is enough for ok=True, with the kickstart
    result folded into the message."""
    script = _agentprof_refresh_script()
    try:
        regen = subprocess.run(
            ["bash", str(script)], capture_output=True, text=True, timeout=120
        )
    except OSError as e:
        return False, str(e)
    if regen.returncode != 0:
        return False, (regen.stderr or regen.stdout or "refresh failed").strip()
    try:
        kick = subprocess.run(
            [
                "launchctl",
                "kickstart",
                "-k",
                f"gui/{os.getuid()}/com.sjaconette.agentprof-pprof",
            ],
            capture_output=True,
            text=True,
        )
        kick_msg = (
            "pprof kickstarted"
            if kick.returncode == 0
            else f"kickstart failed: {(kick.stderr or kick.stdout).strip()}"
        )
    except OSError as e:
        kick_msg = f"kickstart failed: {e}"
    return True, f"profile refreshed; {kick_msg}"


def refresh_cost() -> tuple[bool, str, int]:
    """Run the same incremental refresh step as the hourly launchd job (task
    04 wires `weekly-7d.jsonl`/`weekly-7d-summary.json` maintenance into
    `refresh-profile.sh`), synchronously, for the manual "refresh now" button
    (R5). `sessions_added` is read back out of the just-written summary JSON —
    agentprof computes it (per SPEC R3); the console never derives it."""
    script = _agentprof_refresh_script()
    try:
        regen = subprocess.run(
            ["bash", str(script)], capture_output=True, text=True, timeout=120
        )
    except OSError as e:
        return False, str(e), 0
    if regen.returncode != 0:
        return False, (regen.stderr or regen.stdout or "refresh failed").strip(), 0
    summary = _read_cost_summary()
    if summary is None:
        return False, "refresh ran but no cost summary was written", 0
    added = summary.get("sessions_added", 0)
    if not isinstance(added, int):
        added = 0
    return True, "cost refreshed", added


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, ctype="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _host_allowed(self) -> bool:
        """The Host header names a loopback origin (127.0.0.1, localhost, ::1).
        Guards every route against DNS-rebinding; shared by GET and POST."""
        raw = (self.headers.get("Host") or "").strip()
        if raw.startswith("["):  # bracketed IPv6, e.g. [::1]:8899
            host = raw[1 : raw.index("]")] if "]" in raw else raw[1:]
        elif raw.count(":") == 1:  # host:port
            host = raw.rsplit(":", 1)[0]
        else:
            host = raw
        return host in ("127.0.0.1", "localhost", "::1")

    def do_GET(self):
        if not self._host_allowed():
            self._send(b"bad host", "text/plain", 400)
            return
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/", "/index.html"):
                self._send(render_skills(collect()).encode("utf-8"))
            elif path == "/workboard":
                self._send(
                    render_workboard(
                        get_board(), _read_cost_summary(), _cost_summary_mtime()
                    ).encode("utf-8")
                )
            elif path == "/workboard-kanban":
                self._send(render_workboard_kanban(get_board()).encode("utf-8"))
            elif path == "/dispatches":
                self._send(render_dispatches(_load_records()).encode("utf-8"))
            elif path.startswith("/dispatch/") and path.endswith("/log"):
                self._serve_dispatch_log(path[len("/dispatch/") : -len("/log")])
            elif path.startswith("/file/"):
                self._serve_file(path[len("/file/") :])
            elif path.startswith("/repo/"):
                self._serve_repo(path[len("/repo/") :])
            elif path.startswith("/spec/"):
                self._serve_spec(path[len("/spec/") :])
            elif path.startswith("/task/"):
                self._serve_task(path[len("/task/") :])
            elif path.startswith("/session/"):
                self._serve_session(path[len("/session/") :])
            elif path == "/healthz":
                self._send(b"ok", "text/plain")
            else:
                self._send(b"not found", "text/plain", 404)
        except Exception as exc:  # never drop the connection on a scan hiccup
            self._send(
                f"<pre>dashboard error: {esc(exc)}</pre>".encode("utf-8"), code=500
            )

    def _serve_file(self, entity_id: str) -> None:
        """Read-only view of a registry file. The path comes only from the
        registry (keyed by id), so a client can never steer it — an unknown id
        or `../` segment is just a missing key and 404s."""
        entry = get_registry().get(entity_id)
        if not entry:
            self._send(b"not found", "text/plain", 404)
            return
        try:
            with open(entry["path"], encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            self._send(b"not found", "text/plain", 404)
            return
        title = entry.get("title") or os.path.basename(entry["path"])
        if entry["path"].endswith(".md"):
            body = render_markdown(content)
        else:
            body = f"<pre>{esc(content)}</pre>"
        self._send(render_detail_page(title, body).encode("utf-8"))

    def _serve_dispatch_log(self, did: str) -> None:
        """Serve the last ~200 lines of a dispatch's log. The id keys the
        persisted records, so an unknown id 404s — the client never names a
        path."""
        rec = next((r for r in _load_records() if r.get("id") == did), None)
        if not rec:
            self._send(b"not found", "text/plain", 404)
            return
        try:
            with open(rec["log"], encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            self._send(b"not found", "text/plain", 404)
            return
        tail = "".join(lines[-200:])
        body = render_detail_page(
            f"dispatch log — {esc(rec.get('kind', ''))}", f"<pre>{esc(tail)}</pre>"
        )
        self._send(body.encode("utf-8"))

    def _serve_repo(self, entity_id: str) -> None:
        entry = get_pages().get(entity_id)
        if not entry or entry.get("kind") != "repo":
            self._send(b"not found", "text/plain", 404)
            return
        self._send(render_repo_page(entry).encode("utf-8"))

    def _serve_spec(self, entity_id: str) -> None:
        entry = get_pages().get(entity_id)
        if not entry or entry.get("kind") != "spec":
            self._send(b"not found", "text/plain", 404)
            return
        self._send(render_spec_page(entry).encode("utf-8"))

    def _serve_session(self, entity_id: str) -> None:
        entry = get_pages().get(entity_id)
        if not entry or entry.get("kind") != "session":
            self._send(b"not found", "text/plain", 404)
            return
        self._send(render_session_page(entry).encode("utf-8"))

    def _serve_task(self, entity_id: str) -> None:
        entry = get_pages().get(entity_id)
        if not entry or entry.get("kind") != "task":
            self._send(b"not found", "text/plain", 404)
            return
        try:
            with open(entry["path"], encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            self._send(b"not found", "text/plain", 404)
            return
        title = entry.get("title") or os.path.basename(entry["path"])
        self._send(render_detail_page(title, render_markdown(content)).encode("utf-8"))

    # --- writes / control ---------------------------------------------------
    def _reject_cross_origin(self) -> bool:
        """True (and sends 403) if the request isn't a same-origin localhost
        POST carrying the CSRF token. Blocks CSRF and DNS-rebinding."""
        if not self._host_allowed():
            self._send(b"bad host", "text/plain", 403)
            return True
        origin = self.headers.get("Origin")
        if origin and origin not in (
            f"http://127.0.0.1:{PORT}",
            f"http://localhost:{PORT}",
        ):
            self._send(b"bad origin", "text/plain", 403)
            return True
        if self.headers.get("X-CSRF") != CSRF_TOKEN:
            self._send(b"bad token", "text/plain", 403)
            return True
        return False

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if self._reject_cross_origin():
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or "{}") if n else {}
            if not isinstance(body, dict):
                raise ValueError("body")
        except (ValueError, OSError):
            self._send(b'{"ok":false,"error":"bad body"}', "application/json", 400)
            return
        # Action registry: the only client input is the opaque id in the path;
        # the body (parsed above only to reject malformed JSON) is ignored, so
        # no client-supplied field can steer the executed argv (spec R9).
        if path.startswith("/action/"):
            result = run_action(
                path[len("/action/") :], confirm=bool(body.get("confirm"))
            )
            self._send(
                json.dumps(result["body"]).encode("utf-8"),
                "application/json",
                result["code"],
            )
            return
        # Cost refresh returns a richer body ({"ok", "sessions_added"}) than
        # the generic (ok, message) handlers below, so it's handled here (R5).
        if path == "/api/cost/refresh":
            ok, msg, added = refresh_cost()
            payload = (
                {"ok": ok, "sessions_added": added}
                if ok
                else {
                    "ok": ok,
                    "message": msg,
                }
            )
            self._send(
                json.dumps(payload).encode("utf-8"),
                "application/json",
                200 if ok else 400,
            )
            return
        handlers = {
            "/api/priority": lambda: set_priority(
                body.get("path", ""), body.get("value", "")
            ),
            "/api/agent/start": lambda: start_agent(
                body.get("cwd", ""), body.get("prompt", "")
            ),
            "/api/agent/stop": lambda: stop_agent(
                body.get("pid") if isinstance(body.get("pid"), int) else -1,
                confirm=bool(body.get("confirm")),
            ),
            "/api/agent/resume": lambda: resume_agent(
                body.get("sid", ""), body.get("prompt", "")
            ),
            "/api/profile/refresh": refresh_profile,
        }
        fn = handlers.get(path)
        if not fn:
            self._send(b'{"ok":false,"error":"not found"}', "application/json", 404)
            return
        try:
            ok, msg = fn()
        except Exception as exc:  # never crash the server on a bad request
            ok, msg = False, str(exc)
        payload = json.dumps({"ok": ok, "message": msg}).encode("utf-8")
        self._send(payload, "application/json", 200 if ok else 400)

    def log_message(self, *args):
        pass


def main():
    try:
        srv = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        # Port already held (e.g. another instance). Exit cleanly so launchd
        # KeepAlive(SuccessfulExit=false) does NOT hot-loop restarting us.
        print(f"[agent-console] cannot bind {HOST}:{PORT}: {exc}; exiting", flush=True)
        return
    print(
        f"[agent-console] serving http://{HOST}:{PORT}  (pid {os.getpid()})", flush=True
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
