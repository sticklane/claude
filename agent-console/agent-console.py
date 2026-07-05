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

import html
import importlib.util
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

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
_board_cache: dict = {"ts": 0.0, "data": None}
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
        out.append(
            {
                "num": int(m.group(1)),
                "deps": deps,
                "status": t["status"],
                "title": t["title"],
            }
        )
    return out


def _adapt_board(
    assembled: dict, running_agents: list, resumable_agents: list
) -> dict:
    """Map workboard.assemble()'s result (`{repos, sessions, inbox, ready,
    totals, ...}` — workboard.py is the single source of scan/inbox logic
    per R4) to the board dict render_workboard consumes. The only translation
    layer this migration adds; render_workboard itself is unchanged."""
    vis = gh_visibility()
    board_repos: list[dict] = []
    open_spec_list: list[dict] = []
    active_list: list[dict] = []
    open_specs = 0

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
                    "slug": sp["slug"],
                    "title": sp["title"],
                    "status": None,
                    "priority": "",  # not tracked by workboard.py's scan
                    "path": str(Path(r["path"]) / spec_path) if spec_path else "",
                    "done": done,
                    "total": total,
                    "tasks": _dag_tasks(sp.get("tasks", [])),
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
                "name": r["name"],
                "git": git,
                "gh": gh,
                "specs": specs,
                "tasks": None,  # docs/TASKS.md tracking retired with scan_tasks
                "handoffs": [
                    {"title": h["title"], "path": h["path"], "mtime": h["mtime"]}
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
        "n_open_tasks": 0,
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
        _board_cache.update(ts=time.time(), data=data)
        return data


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
"""


# Client script: delegated handlers (survive DOM swaps) + in-place auto-refresh
# that re-fetches the current view every REFRESH ms and swaps <main> while
# preserving scroll, expanded <details>, the open drill-down panel, and the
# skills filter. Delegation means handlers keep working after each swap.
PAGE_JS = """<script>(function(){
var $=function(s){return document.querySelector(s)},$$=function(s){return document.querySelectorAll(s)};
document.addEventListener('input',function(e){
  if(e.target.id!=='q')return;var t=e.target.value.trim().toLowerCase();
  $$('.card').forEach(function(c){c.classList.toggle('hidden',t&&c.dataset.text.indexOf(t)<0)});
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
    acPost('/api/agent/stop',{pid:parseInt(b.dataset.pid,10)},'Stop agent "'+(b.dataset.name||b.dataset.pid)+'" (SIGTERM)? Resumable via claude --resume.').then(function(ok){if(ok)setTimeout(refresh,600)});
  }else if(b.dataset.act==='resume'){
    var p=window.prompt('Resume "'+(b.dataset.name||b.dataset.sid)+'" as a background agent. Prompt (blank = "continue"):','');
    if(p===null)return;
    acPost('/api/agent/resume',{sid:b.dataset.sid,prompt:p}).then(function(ok){if(ok)setTimeout(refresh,800)});
  }else if(b.dataset.act==='start'){
    var form=b.closest('.kickoff'),prompt=form.querySelector('[name=prompt]').value,cwd=form.querySelector('[name=cwd]').value;
    if(!prompt.trim()){window.alert('Enter a prompt.');return}
    acPost('/api/agent/start',{cwd:cwd,prompt:prompt},'Kick off a background agent in '+cwd+'? This runs Claude and costs tokens.').then(function(ok){if(ok){form.querySelector('[name=prompt]').value='';setTimeout(refresh,900)}});
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
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Console — {esc(active).title()}</title><style>{viz.VIZ_CSS}{CSS}</style></head><body>
<header>
  <div class="masthead">
    <div class="wordmark">Agent<span class="dot">·</span>Console</div>
    <div class="readout">{readout}</div>
  </div>
  <nav class="tabs">{tab("/", "Skills", "skills")}{tab("/workboard", "Workboard", "workboard")}</nav>
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


def render_workboard(b: dict) -> str:
    def chip(state):
        return f'<span class="chip {esc(state)}">{esc(state)}</span>'

    def tile(v, label, attr, cls=""):
        return (
            f'<button class="tile {cls}" {attr}>'
            f'<div class="v">{v}</div><div class="l">{esc(label)}</div></button>'
        )

    tiles = "".join(
        [
            tile(b["n_repos"], "repos", 'data-scroll="#repos"'),
            tile(b["n_open_specs"], "open specs", 'data-panel="specs"'),
            tile(b["n_open_tasks"], "open tasks", 'data-panel="tasks"'),
            tile(b["n_active"], "active sessions", 'data-panel="active"'),
            tile(
                len(b["inbox"]),
                "needs attention",
                'data-scroll="#inbox"',
                "alert" if b["inbox"] else "",
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
    )

    if b["inbox"]:
        rows = "".join(
            f'<div class="row">{chip(i["state"])}'
            f'<div><div class="what">{esc(i["item"])}</div>'
            f'<div class="why">{esc(i["why"])}'
            f"{' <code>' + esc(i['cmd']) + '</code>' if i['cmd'] else ''}</div></div>"
            f'<div class="repo">{esc(i["repo"])}</div>'
            f'<div class="age">{_ago(i["age"])}</div></div>'
            for i in b["inbox"]
        )
        inbox = f'<div class="inbox">{rows}</div>'
    else:
        inbox = '<div class="inbox"><div class="zero">Nothing needs you.</div></div>'

    repo_blocks = []
    for r in sorted(b["repos"], key=lambda r: (not _repo_has_work(r), r["name"])):
        g = r["git"]
        chips = []
        if g.get("branch"):
            chips.append(f'<span class="gchip">{esc(g["branch"])}</span>')
        if g.get("dirty"):
            chips.append(f'<span class="gchip warn">{g["dirty"]}&#916;</span>')
        if g.get("ahead"):
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
                row = (
                    f'<span class="trunc">{esc(sp["title"])}</span>'
                    f'{prog}<span class="meta">{_ago(sp["mtime"])}</span>'
                )
                prio = _prio_select(sp.get("path", ""), sp.get("priority", ""))
                if graph:  # expandable to the dependency graph
                    item = (
                        f'<details class="spec" data-k="s:{esc(r["name"])}/{esc(sp["slug"])}">'
                        f'<summary><div class="line">{row}</div>'
                        f"</summary>{graph}</details>"
                    )
                else:
                    item = f'<div class="line plain">{row}</div>'
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
                    "tooltip": f'{s["branch"]} · {_ago(s["last"])}'
                    if s["branch"]
                    else _ago(s["last"]),
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
                f'<span class="trunc">{esc(h["title"])}</span>'
                f'<span class="meta">{_ago(h["mtime"])}</span></div>'
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

        open_attr = " open" if _repo_has_work(r) else ""
        body = (
            f'<div class="rbody">{"".join(inner)}</div>'
            if inner
            else '<div class="rbody"><div class="zero" style="padding:8px 0">No open work.</div></div>'
        )
        repo_blocks.append(
            f'<details class="repo"{open_attr} data-k="r:{esc(r["name"])}"><summary>'
            f'<span class="rn">{esc(r["name"])}</span>{ghbadge}{"".join(chips)}'
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
        f"<b>{len(b['inbox'])}</b> need you"
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

    body = (
        f"{health}"
        f'<div class="tiles">{tiles}</div>{panels}'
        f'<div class="eyebrow" id="inbox"><span class="key" style="color:var(--text)">Needs attention</span>'
        f'<span class="rule"></span></div>{inbox}'
        f"{agents_html}"
        f'<div class="eyebrow" id="repos"><span class="key" style="color:var(--text)">Repos</span>'
        f'<span class="rule"></span></div>{"".join(repo_blocks)}{orphan}'
    )
    return page("workboard", readout, body, with_filter=False)


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
    return {os.path.realpath(str(r)) for r in parse_repos()}


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


def stop_agent(pid: int) -> tuple[bool, str]:
    # Only kill PIDs the CLI currently reports as agent sessions — never an
    # arbitrary pid supplied by the caller.
    data = _claude_json("agents", "--all") or _claude_json("agents") or []
    live_pids = {e.get("pid") for e in data if isinstance(e, dict)}
    if pid not in live_pids:
        return False, "not a known agent pid"
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as e:
        return False, str(e)
    _board_cache["ts"] = 0
    return True, "stopped"


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

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/", "/index.html"):
                self._send(render_skills(collect()).encode("utf-8"))
            elif path == "/workboard":
                self._send(render_workboard(get_board()).encode("utf-8"))
            elif path == "/healthz":
                self._send(b"ok", "text/plain")
            else:
                self._send(b"not found", "text/plain", 404)
        except Exception as exc:  # never drop the connection on a scan hiccup
            self._send(
                f"<pre>dashboard error: {esc(exc)}</pre>".encode("utf-8"), code=500
            )

    # --- writes / control ---------------------------------------------------
    def _reject_cross_origin(self) -> bool:
        """True (and sends 403) if the request isn't a same-origin localhost
        POST carrying the CSRF token. Blocks CSRF and DNS-rebinding."""
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
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
        handlers = {
            "/api/priority": lambda: set_priority(
                body.get("path", ""), body.get("value", "")
            ),
            "/api/agent/start": lambda: start_agent(
                body.get("cwd", ""), body.get("prompt", "")
            ),
            "/api/agent/stop": lambda: stop_agent(
                body.get("pid") if isinstance(body.get("pid"), int) else -1
            ),
            "/api/agent/resume": lambda: resume_agent(
                body.get("sid", ""), body.get("prompt", "")
            ),
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
