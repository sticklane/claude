#!/usr/bin/env python3
"""workboard — a cross-repo dashboard of specs, tasks, sessions, and agent state.

Scans local git repos and Claude Code state on this machine and renders a
single self-contained HTML snapshot of all open work:

  - toolkit specs   specs/<slug>/SPEC.md + specs/<slug>/tasks/NN-*.md (Status: lines)
  - Kiro specs      .kiro/specs/<name>/tasks.md checkbox state ([ ] [-] [x])
  - Antigravity     ~/.gemini/antigravity*/brain/<id>/ artifacts (task.md + metadata)
  - handoffs        HANDOFF.md files (blocked-on-human, resumable)
  - batons          specs/*/DRAIN-BATON.md (a parked drain generation to relaunch)
  - sessions        ~/.claude/projects/<escaped>/<sessionId>.jsonl transcripts
                    (repo, branch, first prompt, last activity, live PID)
  - git             branch, dirty files, unpushed commits, worktrees

Stdlib only. Read-only: it never mutates any of the state it reports on.

Usage:
  workboard.py [ROOTS ...] [--out workboard.html] [--json] [--stale-days 7]
               [--max-depth 3] [--quiet]

With no ROOTS it scans common code directories (~/code ~/src ~/projects
~/dev ~/repos ~/work, plus the cwd) and every repo any Claude Code session
has touched (derived from session records' cwd field).
"""

import argparse
import html
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve()
STALE_DAYS_DEFAULT = 7
RECENT_HOURS = 48
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".tox",
    "dist", "build", "target", ".next", ".cache", "vendor",
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
            capture_output=True, text=True, timeout=10,
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
            if (Path(dirpath) / ".git").exists():
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

STATUS_RE = re.compile(r"^Status:\s*\[?([A-Za-z_-]+)\]?", re.MULTILINE)
DEPENDS_RE = re.compile(r"^Depends on:\s*(.*)$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
OPEN_TASK_STATUSES = {"pending", "open", "todo", "ready",
                      "in-progress", "in_progress", "claimed"}
CLOSED_TASK_STATUSES = {"done", "deferred", "skipped"}


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
        tasks = []
        tasks_dir = spec_dir / "tasks"
        mtimes = [spec_md.stat().st_mtime]
        if tasks_dir.is_dir():
            for tf in sorted(tasks_dir.glob("*.md")):
                t_text = read_text(tf, 10_000)
                sm = STATUS_RE.search(t_text)
                status = sm.group(1).lower() if sm else "pending"
                tm = TITLE_RE.search(t_text)
                tasks.append({
                    "file": str(tf.relative_to(repo)),
                    "abs": str(tf),
                    "title": tm.group(1).strip() if tm else tf.stem,
                    "status": status,
                    "deps": parse_deps(t_text),
                })
                mtimes.append(tf.stat().st_mtime)
        done = sum(1 for t in tasks if t["status"] in CLOSED_TASK_STATUSES)
        doing = sum(1 for t in tasks
                    if t["status"] in ("in-progress", "in_progress", "claimed"))
        blocked = [t for t in tasks
                   if t["status"] not in CLOSED_TASK_STATUSES
                   and t["status"] not in OPEN_TASK_STATUSES]
        specs.append({
            "kind": "toolkit",
            "slug": spec_dir.name,
            "title": (m.group(1).strip() if m else spec_dir.name),
            "path": str(spec_md.relative_to(repo)),
            "tasks_total": len(tasks),
            "tasks_done": done,
            "tasks_doing": doing,
            "tasks_blocked": [t["file"] for t in blocked],
            "tasks": tasks,
            "last_touched": max(mtimes),
        })
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
                    blocked.append({
                        "repo": r["name"], "slug": s["slug"],
                        "task": t["file"], "dep": unresolved,
                    })
                elif satisfied:
                    spec_ready.append(t)
            if len(spec_ready) >= 2:
                cmd = (f'cd {shlex.quote(repo_path)} && '
                       f'claude "/drain specs/{s["slug"]}"')
                items.append({
                    "repo": r["name"], "slug": s["slug"],
                    "task": f"{len(spec_ready)} ready tasks",
                    "cmd": cmd, "kind": "drain",
                })
            elif spec_ready:
                t = spec_ready[0]
                cmd = (f'cd {shlex.quote(repo_path)} && '
                       f'claude "/build {t["file"]}"')
                items.append({
                    "repo": r["name"], "slug": s["slug"],
                    "task": t["title"], "cmd": cmd, "kind": "build",
                })
    return {"items": items, "blocked_unresolved": blocked}


CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ x-])\]", re.MULTILINE)


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
        phase = [f for f in ("requirements.md", "design.md", "tasks.md")
                 if (spec_dir / f).is_file()]
        mtime = max((f.stat().st_mtime for f in spec_dir.glob("*.md")),
                    default=spec_dir.stat().st_mtime)
        specs.append({
            "kind": "kiro",
            "slug": spec_dir.name,
            "title": spec_dir.name,
            "path": str(spec_dir.relative_to(repo)),
            "tasks_total": total,
            "tasks_done": done,
            "tasks_doing": doing,
            "phase": phase,
            "last_touched": mtime,
        })
    return specs


def scan_handoffs(repo):
    """HANDOFF.md anywhere shallow in the repo = work parked for a human/next session."""
    handoffs = []
    for pattern in ("HANDOFF.md", "*/HANDOFF.md", "*/*/HANDOFF.md",
                    ".claude/HANDOFF.md", "specs/*/HANDOFF.md"):
        for f in repo.glob(pattern):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            text = read_text(f, 4_000)
            m = TITLE_RE.search(text)
            handoffs.append({
                "path": str(f.relative_to(repo)),
                "title": m.group(1).strip() if m else "Handoff",
                "mtime": f.stat().st_mtime,
            })
    # de-dup (patterns can overlap)
    seen, out = set(), []
    for h in handoffs:
        if h["path"] not in seen:
            seen.add(h["path"])
            out.append(h)
    return out


BATON_GEN_RE = re.compile(r"generation[:\s]+(\d+)", re.IGNORECASE)
BATON_CMD_RE = re.compile(r'claude\s+-p\s+"[^"]*"')


def _section_body(text, *heading_patterns):
    """Body of the first markdown section whose heading matches, '' if none."""
    for pat in heading_patterns:
        m = re.search(rf"^#+\s*{pat}[^\n]*\n(.*?)(?=\n#+\s|\Z)",
                      text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def scan_batons(repo):
    """DRAIN-BATON.md = a parked drain generation to relaunch (self-managed,
    not a human handoff — the final generation deletes it)."""
    batons = []
    for pattern in ("DRAIN-BATON.md", "specs/*/DRAIN-BATON.md"):
        for f in repo.glob(pattern):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            text = read_text(f, 8_000)
            gm = BATON_GEN_RE.search(text)
            cm = BATON_CMD_RE.search(text)
            batons.append({
                "path": str(f.relative_to(repo)),
                "generation": int(gm.group(1)) if gm else None,
                "command": cm.group(0) if cm else "",
                "needs_attention": _section_body(text, "needs.?attention",
                                                 "deferred"),
                "mtime": f.stat().st_mtime,
            })
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
                        texts = [c.get("text", "") for c in content
                                 if isinstance(c, dict) and c.get("type") == "text"]
                        prompt = " ".join(texts).strip() or None
                if prompt and cwd and branch:
                    break
    except OSError:
        pass
    if prompt:
        prompt = re.sub(r"<[^>]+>", " ", prompt)  # strip system-reminder tags
        prompt = re.sub(r"\s+", " ", prompt).strip()[:200]
    return prompt, cwd, branch


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


def live_session_ids(claude_home):
    """sessionIds with a live Claude Code process, from ~/.claude/sessions/*.json."""
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


def scan_sessions(claude_home, stale_days):
    sessions = []
    projects = claude_home / "projects"
    if not projects.is_dir():
        return sessions
    live = live_session_ids(claude_home)
    for proj_dir in projects.iterdir():
        if not proj_dir.is_dir():
            continue
        for jl in proj_dir.glob("*.jsonl"):
            sid = jl.stem
            prompt, cwd, branch = _first_prompt_and_meta(jl)
            last_ts, last_branch = _last_record_ts(jl)
            last_ts = last_ts or jl.stat().st_mtime
            age_days = (now_ts() - last_ts) / 86400
            if sid in live:
                state = "active"
            elif age_days * 24 < RECENT_HOURS:
                state = "recent"
            elif age_days > stale_days:
                state = "stale"
            else:
                state = "idle"
            sessions.append({
                "id": sid,
                "cwd": cwd,
                "branch": last_branch or branch,
                "prompt": prompt or "(no prompt found)",
                "last_ts": last_ts,
                "bytes": jl.stat().st_size,
                "state": state,
            })
    sessions.sort(key=lambda s: s["last_ts"], reverse=True)
    return sessions


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
        open_items = [t for t in todos if isinstance(t, dict)
                      and t.get("status") in ("pending", "in_progress")]
        if open_items:
            items.append({
                "session": f.stem.split("-agent-")[0],
                "open": len(open_items),
                "total": len(todos),
                "next": open_items[0].get("content", "")[:120],
                "mtime": f.stat().st_mtime,
            })
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
                encoding="utf-8")
            marked.append(conv.name)
            wanted.discard(conv.name)
    return marked, sorted(wanted)


def abandon_stale(stale_days):
    """Mark every stale conversation (open items, idle past threshold)."""
    stale = [c["id"] for c in scan_antigravity()
             if c["open"] > 0 and (now_ts() - c["last_ts"]) > stale_days * 86400]
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
        convs.append({
            "id": conv.name,
            "store": store,
            "summary": (summary or conv.name)[:160],
            "tasks_total": len(boxes),
            "tasks_done": done,
            "open": len(boxes) - done,
            "last_ts": mtime,
        })
    convs.sort(key=lambda c: c["last_ts"], reverse=True)
    return convs

# ---------------------------------------------------------------- assembly

def attention_items(repos, sessions, antigravity, stale_days):
    """The inbox: everything that needs a human decision, most severe first.

    severity: critical > serious > warning  (rendered with icon + word, never
    color alone)."""
    items = []
    active_cwds = {s["cwd"] for s in sessions if s["state"] == "active" and s["cwd"]}

    for r in repos:
        rp = r["path"]
        covered_by_active = any(c and (c == rp or c.startswith(rp + os.sep))
                                for c in active_cwds)
        for h in r["handoffs"]:
            resume_prompt = (f"Resume the parked handoff in {h['path']}; "
                             "delete the file once fully resumed")
            items.append({
                "severity": "serious", "state": "blocked",
                "repo": r["name"], "what": f"Handoff parked: {h['title']}",
                "why": f"{h['path']} — resume it in a fresh session, then delete the file (/handoff wrote it):",
                "cmd": f"cd {shlex.quote(rp)} && claude {shlex.quote(resume_prompt)}",
                "age_ts": h["mtime"],
            })
        for s in r["specs"]:
            open_tasks = s["tasks_total"] - s["tasks_done"]
            if s.get("tasks_blocked"):
                items.append({
                    "severity": "serious", "state": "blocked",
                    "repo": r["name"],
                    "what": f"Spec {s['slug']}: task(s) blocked",
                    "why": ", ".join(s["tasks_blocked"][:3])
                           + " — answer its open question, flip its Status: line, re-dispatch via /build or /drain",
                    "age_ts": s["last_touched"],
                })
            elif s["tasks_total"] > 0 and open_tasks == 0:
                verify_prompt = (f"Use the verifier agent to verify specs/{s['slug']} "
                                 "against its acceptance criteria; if it passes, "
                                 "archive the spec dir")
                items.append({
                    "severity": "warning", "state": "needs-review",
                    "repo": r["name"],
                    "what": f"Spec {s['slug']}: all {s['tasks_total']} task(s) done",
                    "why": "run the verifier agent against the spec, then archive the spec dir:",
                    "cmd": f"cd {shlex.quote(rp)} && claude {shlex.quote(verify_prompt)}",
                    "age_ts": s["last_touched"],
                })
            elif open_tasks > 0 and (now_ts() - s["last_touched"]) > stale_days * 86400:
                items.append({
                    "severity": "warning", "state": "stale",
                    "repo": r["name"],
                    "what": f"Spec {s['slug']}: {open_tasks} open task(s), idle {age_str(s['last_touched'])}",
                    "why": "resume it, defer it (Status: deferred), or delete it — open work decays; deciding is the point",
                    "age_ts": s["last_touched"],
                })
        if r["git"]["dirty"] and not covered_by_active:
            items.append({
                "severity": "warning", "state": "needs-review",
                "repo": r["name"],
                "what": f"{r['git']['dirty']} uncommitted change(s), no live session",
                "why": f"on branch {r['git']['branch']} — commit (then push) or stash; small focused commits",
                "age_ts": r["git"]["last_commit_ts"],
            })
        if r["git"]["ahead"]:
            items.append({
                "severity": "warning", "state": "needs-review",
                "repo": r["name"],
                "what": f"{r['git']['ahead']} unpushed commit(s) on {r['git']['branch']}",
                "why": "push or open a PR — local-only work is invisible work:",
                "cmd": f"git -C {shlex.quote(rp)} push",
                "age_ts": r["git"]["last_commit_ts"],
            })

    for c in antigravity:
        if c["open"] > 0 and (now_ts() - c["last_ts"]) > stale_days * 86400:
            items.append({
                "severity": "warning", "state": "stale",
                "repo": f"antigravity:{c['store']}",
                "what": f"{c['open']} open checklist item(s): {c['summary'][:60]}",
                "why": "stale Antigravity conversation — resume it, or abandon:",
                "cmd": f"python3 {shlex.quote(str(SCRIPT))} --abandon {shlex.quote(c['id'])}",
                "age_ts": c["last_ts"],
            })

    sev_rank = {"critical": 0, "serious": 1, "warning": 2}
    items.sort(key=lambda i: (sev_rank.get(i["severity"], 3), -(i["age_ts"] or 0)))
    return items


def assemble(roots, max_depth, stale_days, quiet):
    claude_home = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    sessions = scan_sessions(claude_home, stale_days)

    # every repo a session touched joins the scan set
    session_dirs = []
    for s in sessions:
        if s["cwd"] and Path(s["cwd"]).is_dir():
            top = run_git(s["cwd"], "rev-parse", "--show-toplevel")
            if top:
                session_dirs.append(Path(top))

    repo_paths = sorted({str(p) for p in
                         list(find_repos(roots, max_depth)) + session_dirs})
    repos = []
    for rp in repo_paths:
        p = Path(rp)
        if not quiet:
            print(f"  scanning {rp}", file=sys.stderr)
        repos.append({
            "path": rp,
            "name": p.name,
            "git": git_info(p),
            "specs": scan_toolkit_specs(p) + scan_kiro_specs(p),
            "handoffs": scan_handoffs(p),
            "batons": scan_batons(p),
        })

    # attach sessions to repos
    for r in repos:
        r["sessions"] = [s for s in sessions if s["cwd"]
                         and (s["cwd"] == r["path"]
                              or s["cwd"].startswith(r["path"] + os.sep))]
    matched = {s["id"] for r in repos for s in r["sessions"]}
    orphan_sessions = [s for s in sessions if s["id"] not in matched]

    antigravity = scan_antigravity()
    todos = scan_todos(claude_home)
    inbox = attention_items(repos, sessions, antigravity, stale_days)
    ready = ready_items(repos)

    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "stale_days": stale_days,
        "repos": repos,
        "sessions": sessions,
        "orphan_sessions": orphan_sessions,
        "antigravity": antigravity,
        "todos": todos,
        "inbox": inbox,
        "ready": ready,
        "totals": {
            "repos": len(repos),
            "specs_open": sum(1 for r in repos for s in r["specs"]
                              if s["tasks_total"] == 0
                              or s["tasks_done"] < s["tasks_total"]),
            "tasks_open": sum(s["tasks_total"] - s["tasks_done"]
                              for r in repos for s in r["specs"]),
            "sessions_active": sum(1 for s in sessions if s["state"] == "active"),
            "attention": len(inbox),
        },
    }

# ---------------------------------------------------------------- rendering

def esc(x):
    return html.escape(str(x if x is not None else ""))


def cmd_html(command):
    """A copyable shell command: <code class="cmd"> plus an adjacent,
    always-visible copy button. The click handler (see TEMPLATE) copies from
    either element and always ends in visible feedback."""
    return (
        f'<span class="cmd-wrap"><code class="cmd">{esc(command)}</code>'
        f'<button type="button" class="copy-btn" aria-label="Copy command">'
        f'<span class="copy-glyph" aria-hidden="true">⧉</span> copy</button></span>'
    )


def handoff_pickup_cmd(repo_path, rel_handoff):
    """Runnable pickup command for a repo-card handoff: cd into the repo and
    hand the absolute handoff path to a fresh `claude`."""
    abs_handoff = str(Path(repo_path) / rel_handoff)
    prompt = f"Read {shlex.quote(abs_handoff)} and continue the work it describes"
    return f'cd {shlex.quote(repo_path)} && claude "{prompt}"'


STATE_BADGE = {
    # state → (glyph, css class); color never carries meaning alone
    "active": ("●", "good"),
    "recent": ("◐", "info"),
    "idle": ("○", "muted"),
    "stale": ("⏸", "warning"),
    "blocked": ("⚑", "serious"),
    "needs-review": ("▲", "warning"),
    "done": ("✓", "good"),
}


def badge(state):
    glyph, cls = STATE_BADGE.get(state, ("○", "muted"))
    return f'<span class="badge {cls}">{glyph} {esc(state)}</span>'


def progress_bar(done, total, doing=0):
    if total == 0:
        return '<span class="muted-text">no tasks yet</span>'
    pct = round(100 * done / total)
    doing_pct = round(100 * doing / total)
    return (
        f'<span class="bar" role="img" aria-label="{done} of {total} tasks done">'
        f'<span class="bar-fill" style="width:{pct}%"></span>'
        f'<span class="bar-doing" style="left:{pct}%;width:{doing_pct}%"></span></span>'
        f'<span class="bar-label">{done}/{total}</span>'
    )


def render_batons(batons):
    """Baton cards: a parked drain generation to relaunch. Deliberately NOT
    the handoff card's resume-then-delete prompt — drain self-manages the
    file, and the final generation deletes it on its own."""
    out = []
    for b in batons:
        gen = b["generation"] if b["generation"] is not None else "?"
        attn = (f'<span class="baton-attn"> · needs attention: '
                f'{esc(b["needs_attention"])}</span>'
                if b.get("needs_attention") else "")
        cmd = f' <code>{esc(b["command"])}</code>' if b.get("command") else ""
        out.append(
            f'<p class="baton">🪧 drain baton · generation {esc(gen)} parked in '
            f'<code>{esc(b["path"])}</code> — relaunch to continue the queue '
            f'(drain self-manages; the final generation deletes it):{cmd}{attn}</p>'
        )
    return "".join(out)


def render_ready(ready):
    """The 'Ready to start' section: opportunity, distinct from the inbox."""
    items = ready["items"]
    if items:
        rows = "".join(
            f"<tr><td>{esc(i['repo'])}</td>"
            f"<td class='strong'>{esc(i['slug'])}</td>"
            f"<td>{esc(i['task'])}</td>"
            f"<td>{cmd_html(i['cmd'])}</td></tr>"
            for i in items
        )
        body = (
            "<table><thead><tr><th>repo</th><th>spec</th><th>task</th>"
            "<th>launch</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )
    else:
        body = ('<p class="empty">Nothing ready to start — every pending task '
                'is waiting on an unfinished dependency.</p>')

    blocked = ready["blocked_unresolved"]
    blocked_html = ""
    if blocked:
        lines = "".join(
            f"<li>{esc(b['repo'])} · <code>{esc(b['task'])}</code> — "
            f"unresolved dependency <code>{esc(b['dep'])}</code></li>"
            for b in blocked
        )
        blocked_html = (
            '<p class="legend">Blocked by an unresolved <code>Depends on:</code> '
            f'id — fix the reference:</p><ul class="blocked-deps">{lines}</ul>'
        )

    return (
        '<section class="ready" data-category="ready"><h2>Ready to start '
        f'<span class="count">{len(items)}</span></h2>'
        '<p class="legend">Pending tasks whose dependencies are all done — '
        'dispatchable now. Click a <code>command</code> or its copy button to copy it.</p>'
        f"{body}{blocked_html}</section>"
    )


def build_actions_script(data):
    """The companion actions script: only safe, mechanical batch fixes — repo
    pushes and verifier invocations — in labeled, independently-runnable
    sections. Never archive moves, force pushes, rm, or /build//drain launches."""
    pushes, verifies = [], []
    for r in data["repos"]:
        rp = r["path"]
        if r["git"]["ahead"]:
            pushes.append(f"git -C {shlex.quote(rp)} push")
        for s in r["specs"]:
            if (s.get("kind") == "toolkit" and s["tasks_total"] > 0
                    and s["tasks_done"] >= s["tasks_total"]):
                verifies.append(
                    f"cd {shlex.quote(rp)}\n"
                    f'claude "Use the verifier agent to verify specs/{s["slug"]} '
                    'against its acceptance criteria"')
    lines = [
        "#!/usr/bin/env bash",
        "set -u",
        'echo "Review this script before running: pushes run immediately; '
        'verify lines launch review sessions." >&2',
        "",
    ]
    if pushes:
        lines.append("# === Pushes ===")
        lines.extend(pushes)
        lines.append("")
    if verifies:
        lines.append("# === Verify done specs ===")
        lines.extend(verifies)
        lines.append("")
    if not pushes and not verifies:
        lines.append("# no batch actions available")
    return "\n".join(lines).rstrip("\n") + "\n"


def render_actions(data):
    """Near-top HTML surface linking the companion actions script: its path plus
    the exact `bash <path>` invocation inside a <td><code> so the existing
    click-to-copy handler (closest('td code')) applies."""
    path = data.get("actions_path")
    if not path:
        return ""
    inv = f"bash {shlex.quote(path)}"
    return (
        '<section class="actions"><h2>Batch actions</h2>'
        '<p class="legend">A companion script of safe, mechanical fixes was '
        f'written to <code>{esc(path)}</code>. Pushes run immediately; verify '
        'lines launch review sessions — review it before running.</p>'
        '<table><tbody><tr><td><code class="cmd">'
        f'{esc(inv)}</code></td></tr></tbody></table></section>'
    )


# The attention inbox categories, in fixed severity order (R6). `ready` (R7)
# is opportunity, not attention, so it leads the filter tiles but is not an
# inbox group.
INBOX_CATEGORIES = ("blocked", "needs-review", "stale")
FILTER_CATEGORIES = ("ready", *INBOX_CATEGORIES)


def render_inbox(inbox):
    """The attention inbox, grouped under per-category headers in the fixed
    severity order blocked → needs-review → stale, newest-first within a group.
    Item content and cmd strings are unchanged from the flat render (R6)."""
    if not inbox:
        return '<p class="empty">Inbox zero — nothing is blocked, stale, or waiting on review. 🎉</p>'
    groups = []
    for cat in INBOX_CATEGORIES:
        rows = sorted((i for i in inbox if i["state"] == cat),
                      key=lambda i: -(i["age_ts"] or 0))
        if not rows:
            continue
        body = "".join(
            f'<tr data-category="{cat}"><td>{badge(i["state"])}</td>'
            f"<td class='strong'>{esc(i['what'])}</td>"
            f"<td>{esc(i['repo'])}</td>"
            f"<td>{esc(i['why'])}"
            + (f" {cmd_html(i['cmd'])}" if i.get("cmd") else "")
            + f"</td><td class='num'>{esc(age_str(i['age_ts']))}</td></tr>"
            for i in rows
        )
        groups.append(
            f'<h3 class="group-head" data-category="{cat}">{badge(cat)} '
            f'<span class="count">{len(rows)}</span></h3>'
            f'<table data-category="{cat}"><thead><tr><th>state</th><th>item</th>'
            '<th>repo</th><th>suggested action</th><th>age</th></tr></thead>'
            f"<tbody>{body}</tbody></table>"
        )
    return "".join(groups)


def render_filter_tiles(data):
    """Clickable filter tiles: one per present category among ready, blocked,
    needs-review, stale (R7). Each carries data-filter="<category>"; the embedded
    handler in TEMPLATE toggles which categorized surfaces are shown."""
    counts = {c: 0 for c in FILTER_CATEGORIES}
    counts["ready"] = len(data["ready"]["items"])
    for i in data["inbox"]:
        if i["state"] in counts:
            counts[i["state"]] += 1
    tiles = "".join(
        f'<button type="button" class="ftile" data-filter="{cat}">'
        f'<span class="ftile-value">{counts[cat]}</span>'
        f'<span class="ftile-label">{cat}</span></button>'
        for cat in FILTER_CATEGORIES if counts[cat]
    )
    if not tiles:
        return ""
    return (f'<div class="filter-tiles" role="group" aria-label="Filter by category">'
            f'{tiles}</div>')


def render_html(data):
    t = data["totals"]

    tiles = "".join(
        f'<div class="tile"><div class="tile-value">{esc(v)}</div>'
        f'<div class="tile-label">{esc(label)}</div></div>'
        for label, v in [
            ("repos scanned", t["repos"]),
            ("open specs", t["specs_open"]),
            ("open tasks", t["tasks_open"]),
            ("active sessions", t["sessions_active"]),
            ("needs attention", t["attention"]),
        ]
    )

    inbox_html = render_inbox(data["inbox"])

    repo_cards = []
    for r in sorted(data["repos"],
                    key=lambda r: r["git"]["last_commit_ts"] or 0, reverse=True):
        g = r["git"]
        chips = [f'<span class="chip">⎇ {esc(g["branch"])}</span>']
        if g["dirty"]:
            chips.append(f'<span class="chip warning">± {g["dirty"]} dirty</span>')
        if g["ahead"]:
            chips.append(f'<span class="chip warning">↑ {g["ahead"]} unpushed</span>')
        if g["behind"]:
            chips.append(f'<span class="chip">↓ {g["behind"]} behind</span>')
        for wt in g["worktrees"]:
            chips.append(f'<span class="chip">⌂ {esc(wt.get("branch", "worktree"))}</span>')

        spec_rows = "".join(
            f"<tr><td class='strong'>{esc(s['slug'])}"
            f"<span class='muted-text'> · {esc(s['kind'])}</span></td>"
            f"<td>{progress_bar(s['tasks_done'], s['tasks_total'], s.get('tasks_doing', 0))}</td>"
            f"<td class='num'>{esc(age_str(s['last_touched']))}</td></tr>"
            for s in r["specs"]
        ) or "<tr><td colspan='3' class='muted-text'>no specs</td></tr>"

        sess_rows = "".join(
            f"<tr><td>{badge(s['state'])}</td>"
            f"<td class='prompt'>{esc(s['prompt'])}</td>"
            f"<td>{esc(s['branch'] or '?')}</td>"
            f"<td class='num'>{esc(age_str(s['last_ts']))}</td></tr>"
            for s in r["sessions"][:8]
        )
        sess_html = (
            "<table><thead><tr><th>state</th><th>first prompt</th>"
            f"<th>branch</th><th>last active</th></tr></thead><tbody>{sess_rows}</tbody></table>"
            if sess_rows else '<p class="muted-text">no sessions recorded</p>'
        )
        handoff_html = "".join(
            f'<p class="handoff">⚑ handoff: {esc(h["title"])} — '
            f'{cmd_html(handoff_pickup_cmd(r["path"], h["path"]))}</p>'
            for h in r["handoffs"]
        )
        baton_html = render_batons(r.get("batons", []))
        repo_cards.append(
            f'<details class="repo" open><summary><span class="repo-name">{esc(r["name"])}</span>'
            f'<span class="repo-path">{esc(r["path"])}</span>{"".join(chips)}</summary>'
            f'{baton_html}{handoff_html}'
            f'<div class="repo-grid"><div><h3>Specs</h3>'
            f"<table><thead><tr><th>spec</th><th>tasks</th><th>touched</th></tr></thead>"
            f"<tbody>{spec_rows}</tbody></table></div>"
            f"<div><h3>Sessions</h3>{sess_html}</div></div></details>"
        )

    ag_html = ""
    if data["antigravity"]:
        ag_rows = "".join(
            f"<tr><td>{badge('stale' if c['open'] and (now_ts() - c['last_ts']) > data['stale_days'] * 86400 else ('done' if c['tasks_total'] and not c['open'] else 'idle'))}</td>"
            f"<td class='prompt'>{esc(c['summary'])}</td>"
            f"<td>{progress_bar(c['tasks_done'], c['tasks_total'])}</td>"
            f"<td class='num'>{esc(age_str(c['last_ts']))}</td></tr>"
            for c in data["antigravity"][:20]
        )
        any_stale = any(c["open"] and (now_ts() - c["last_ts"]) > data["stale_days"] * 86400
                        for c in data["antigravity"])
        abandon_hint = (
            f'<p class="muted-text">abandon everything stale at once: '
            f'{cmd_html(f"python3 {shlex.quote(str(SCRIPT))} --abandon-stale")} '
            f'(writes a skip-marker per conversation; Antigravity state itself is untouched)</p>'
            if any_stale else ""
        )
        ag_html = (
            "<section><h2>Antigravity conversations</h2>"
            f"{abandon_hint}"
            "<table><thead><tr><th>state</th><th>summary</th><th>checklist</th>"
            f"<th>updated</th></tr></thead><tbody>{ag_rows}</tbody></table></section>"
        )

    todo_html = ""
    if data["todos"]:
        todo_rows = "".join(
            f"<tr><td class='num'>{t['open']}/{t['total']}</td>"
            f"<td class='prompt'>{esc(t['next'])}</td>"
            f"<td class='num'>{esc(age_str(t['mtime']))}</td></tr>"
            for t in sorted(data["todos"], key=lambda t: t["mtime"], reverse=True)[:15]
        )
        todo_html = (
            "<section><h2>Open in-session todo lists</h2>"
            "<table><thead><tr><th>open</th><th>next item</th><th>updated</th>"
            f"</tr></thead><tbody>{todo_rows}</tbody></table></section>"
        )

    orphan_html = ""
    if data["orphan_sessions"]:
        rows = "".join(
            f"<tr><td>{badge(s['state'])}</td><td class='prompt'>{esc(s['prompt'])}</td>"
            f"<td>{esc(s['cwd'] or '?')}</td><td class='num'>{esc(age_str(s['last_ts']))}</td></tr>"
            for s in data["orphan_sessions"][:20]
        )
        orphan_html = (
            "<section><h2>Sessions outside scanned repos</h2>"
            "<table><thead><tr><th>state</th><th>first prompt</th><th>cwd</th>"
            f"<th>last active</th></tr></thead><tbody>{rows}</tbody></table></section>"
        )

    return TEMPLATE.format(
        generated_at=esc(data["generated_at"]),
        stale_days=data["stale_days"],
        tiles=tiles,
        filter_tiles=render_filter_tiles(data),
        actions=render_actions(data),
        ready=render_ready(data["ready"]),
        inbox=inbox_html,
        repos="".join(repo_cards) or '<p class="empty">No git repos found in the scanned roots.</p>',
        antigravity=ag_html,
        todos=todo_html,
        orphans=orphan_html,
    )


# Palette: the toolkit's pre-validated reference set (light+dark selected, not
# flipped). Status colors ship with a glyph + word — never color alone.
TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Workboard</title>
<style>
:root {{
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e;
  --muted:#898781; --grid:#e1e0d9; --border:rgba(11,11,11,.10);
  --blue:#2a78d6; --blue-soft:#9ec5f4;
  --good:#0ca30c; --warning:#a86e00; --serious:#c05a2e; --critical:#d03b3b;
}}
@media (prefers-color-scheme: dark) {{ :root {{
  --page:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7;
  --muted:#898781; --grid:#2c2c2a; --border:rgba(255,255,255,.10);
  --blue:#3987e5; --blue-soft:#1c5cab;
  --good:#0ca30c; --warning:#fab219; --serious:#ec835a; --critical:#d03b3b;
}} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:24px; background:var(--page); color:var(--ink);
  font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }}
h1 {{ font-size:20px; margin:0 0 2px; }}
h2 {{ font-size:15px; margin:0 0 10px; }}
h3 {{ font-size:13px; margin:0 0 6px; color:var(--ink-2); }}
.sub {{ color:var(--muted); font-size:12px; margin-bottom:20px; }}
section {{ background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:16px; margin-bottom:16px; }}
.tiles {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }}
.tile {{ background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:12px 18px; min-width:120px; }}
.tile-value {{ font-size:26px; font-weight:650; }}
.tile-label {{ font-size:12px; color:var(--ink-2); }}
.filter-tiles {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }}
.ftile {{ display:inline-flex; align-items:baseline; gap:6px; cursor:pointer;
  background:var(--surface); border:1px solid var(--border); border-radius:999px;
  padding:5px 14px; color:var(--ink); font:inherit; }}
.ftile:hover, .ftile:focus {{ border-color:var(--blue); }}
.ftile.active {{ border-color:var(--blue); background:var(--blue-soft); }}
.ftile-value {{ font-weight:650; font-variant-numeric:tabular-nums; }}
.ftile-label {{ font-size:12px; color:var(--ink-2); }}
.group-head {{ margin:14px 0 4px; display:flex; align-items:center; gap:8px; }}
.group-head:first-child {{ margin-top:0; }}
.group-head .count {{ font-size:11px; color:var(--muted);
  font-variant-numeric:tabular-nums; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; color:var(--muted); font-weight:500; font-size:11px;
  text-transform:uppercase; letter-spacing:.04em; padding:4px 10px 6px 0; }}
td {{ padding:6px 10px 6px 0; border-top:1px solid var(--grid);
  vertical-align:top; }}
.num {{ font-variant-numeric:tabular-nums; white-space:nowrap; }}
.strong {{ font-weight:600; }}
.prompt {{ color:var(--ink-2); max-width:560px; overflow-wrap:anywhere; }}
.badge {{ white-space:nowrap; font-size:12px; font-weight:600; }}
.badge.good {{ color:var(--good); }} .badge.warning {{ color:var(--warning); }}
.badge.serious {{ color:var(--serious); }} .badge.critical {{ color:var(--critical); }}
.badge.info {{ color:var(--blue); }} .badge.muted {{ color:var(--muted); }}
.chip {{ display:inline-block; font-size:11px; padding:1px 8px; margin-left:6px;
  border:1px solid var(--border); border-radius:999px; color:var(--ink-2); }}
.chip.warning {{ color:var(--warning); border-color:var(--warning); }}
.repo {{ background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:12px 16px; margin-bottom:12px; }}
.repo summary {{ cursor:pointer; list-style:none; display:flex; align-items:center;
  flex-wrap:wrap; gap:2px; }}
.repo summary::before {{ content:"▸"; color:var(--muted); margin-right:8px; }}
.repo[open] summary::before {{ content:"▾"; }}
.repo-name {{ font-weight:650; font-size:15px; }}
.repo-path {{ color:var(--muted); font-size:12px; margin-left:10px; }}
.repo-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px;
  margin-top:12px; }}
@media (max-width:800px) {{ .repo-grid {{ grid-template-columns:1fr; }} }}
.bar {{ display:inline-block; position:relative; width:120px; height:8px;
  background:var(--grid); border-radius:4px; overflow:hidden;
  vertical-align:middle; }}
.bar-fill {{ position:absolute; left:0; top:0; bottom:0;
  background:var(--blue); border-radius:4px; }}
.bar-doing {{ position:absolute; top:0; bottom:0; background:var(--blue-soft); }}
.bar-label {{ font-size:12px; color:var(--ink-2); margin-left:8px;
  font-variant-numeric:tabular-nums; }}
.muted-text {{ color:var(--muted); }}
.empty {{ color:var(--ink-2); }}
section.ready {{ border-left:4px solid var(--good); }}
section.ready h2 .count {{ display:inline-block; margin-left:6px;
  background:var(--good); color:#fff; border-radius:999px;
  padding:0 9px; font-size:12px; font-weight:600;
  font-variant-numeric:tabular-nums; vertical-align:middle; }}
.blocked-deps {{ margin:6px 0 0; padding-left:20px; color:var(--ink-2);
  font-size:12px; }}
.handoff {{ color:var(--serious); font-size:13px; margin:8px 0 0; }}
.handoff code {{ font-size:12px; }}
.baton {{ color:var(--ink-2); font-size:13px; margin:8px 0 0; }}
.baton code {{ font-size:12px; }}
.baton-attn {{ color:var(--serious); }}
#filter {{ width:280px; padding:6px 10px; margin-bottom:14px;
  border:1px solid var(--border); border-radius:8px; background:var(--surface);
  color:var(--ink); font:inherit; }}
footer {{ color:var(--muted); font-size:11px; margin-top:20px; }}
.legend {{ color:var(--muted); font-size:12px; margin:-4px 0 10px; }}
td code, .legend code {{ font-size:12px; background:var(--grid);
  padding:1px 6px; border-radius:5px; overflow-wrap:anywhere; }}
td code {{ cursor:copy; }}
td code.copied {{ outline:1px solid var(--good); }}
.cmd-wrap {{ display:inline-flex; align-items:center; gap:6px;
  vertical-align:baseline; max-width:100%; }}
code.cmd {{ cursor:pointer; overflow-wrap:anywhere; }}
code.cmd:hover, code.cmd:focus {{ outline:1px solid var(--blue);
  background:var(--surface); }}
.copy-btn {{ flex:0 0 auto; cursor:pointer; font:inherit; font-size:11px;
  line-height:1.4; padding:2px 8px; border:1px solid var(--border);
  border-radius:6px; background:var(--surface); color:var(--ink-2);
  display:inline-flex; align-items:center; gap:4px; white-space:nowrap; }}
.copy-btn:hover, .copy-btn:focus {{ border-color:var(--blue);
  color:var(--ink); }}
.copy-btn.is-copied {{ border-color:var(--good); color:var(--good); }}
.copy-btn.is-manual {{ border-color:var(--serious); color:var(--serious);
  font-weight:600; }}
.copy-glyph {{ font-size:12px; }}
</style></head><body>
<h1>Workboard</h1>
<div class="sub">All open work across local repos, specs, and Claude Code
sessions · snapshot {generated_at} · stale after {stale_days}d · re-run
<code>workboard.py</code> to refresh</div>
<div class="tiles">{tiles}</div>
{filter_tiles}
<input id="filter" type="search" placeholder="filter rows…"
 oninput="var q=this.value.toLowerCase();document.querySelectorAll('tbody tr, details.repo').forEach(function(el){{el.style.display=el.textContent.toLowerCase().includes(q)?'':'none'}})">
{actions}
{ready}
<section><h2>Needs attention</h2>
<p class="legend">⚑ blocked = waiting on a human decision · ▲ needs-review =
verify or close finished/dirty work · ⏸ stale = open work idle past {stale_days}d.
Most severe first. Click any <code>command</code> or its copy button to copy it.</p>
{inbox}</section>
<section><h2>Repos</h2>{repos}</section>
{antigravity}
{todos}
{orphans}
<footer>Sources: specs/*/SPEC.md + tasks (Status: lines) · .kiro/specs/*/tasks.md
checkboxes · HANDOFF.md + DRAIN-BATON.md files · ~/.claude/projects transcripts + live PIDs ·
~/.gemini/antigravity*/brain artifacts · git status. Read-only snapshot
(sole write: opt-in --abandon skip-markers); glyph + word carry state,
never color alone.</footer>
<script>
(function(){{
  // Restore a copy button to its "copy" state.
  function reset(btn){{
    btn.classList.remove("is-copied","is-manual");
    btn.innerHTML = btn.dataset.orig;
  }}
  // Visible, non-color-only feedback on the command's copy button. Bare
  // <code> without a button (e.g. the ready-list /build items) falls back to
  // the outline pulse the dashboard has always used.
  function feedback(code, glyph, word, cls, hold){{
    var wrap = code.closest(".cmd-wrap");
    var btn = wrap && wrap.querySelector(".copy-btn");
    if(!btn){{
      code.classList.add("copied");
      setTimeout(function(){{code.classList.remove("copied");}}, 600);
      return;
    }}
    if(btn.dataset.orig === undefined) btn.dataset.orig = btn.innerHTML;
    clearTimeout(btn._t);
    btn.classList.remove("is-copied","is-manual");
    btn.classList.add(cls);
    btn.innerHTML = '<span class="copy-glyph" aria-hidden="true">' + glyph +
                    '</span> ' + word;
    btn._t = setTimeout(function(){{reset(btn);}}, hold);
  }}
  function copied(code){{ feedback(code, "✓", "copied ✓", "is-copied", 600); }}
  // Deepest fallback: select the command text in place so ⌘C works, and say so.
  function manual(code){{
    var r = document.createRange(); r.selectNodeContents(code);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
    feedback(code, "⌘", "press ⌘C", "is-manual", 4000);
  }}
  // execCommand path: a hidden textarea, never silent — success or manual.
  function viaExec(code, text){{
    var ok = false;
    try {{
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly","");
      ta.style.position = "fixed"; ta.style.top = "-1000px"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      ok = document.execCommand('copy');
      document.body.removeChild(ta);
    }} catch(e) {{ ok = false; }}
    if(ok) copied(code); else manual(code);
  }}
  function copy(code){{
    var text = code.textContent;
    var p = navigator.clipboard && navigator.clipboard.writeText(text);
    if(p) p.then(function(){{copied(code);}}, function(){{viaExec(code, text);}});
    else viaExec(code, text);
  }}
  document.addEventListener("click", function(e){{
    var btn = e.target.closest(".copy-btn");
    var code;
    if(btn){{ var w = btn.closest(".cmd-wrap"); code = w && w.querySelector("code.cmd"); }}
    else {{ code = e.target.closest("code.cmd") || e.target.closest("td code"); }}
    if(code) copy(code);
  }});
}})();
</script>
<script>
(function(){{
  // Click-to-filter tiles: isolate one category (ready / blocked / needs-review
  // / stale) by hiding every categorized surface that doesn't match; re-clicking
  // the active tile restores the full view. Independent of the text filter above.
  var tiles = document.querySelectorAll('.ftile[data-filter]');
  var active = null;
  function apply(cat){{
    document.querySelectorAll('[data-category]').forEach(function(el){{
      el.style.display = (!cat || el.getAttribute('data-category') === cat) ? '' : 'none';
    }});
    tiles.forEach(function(t){{
      t.classList.toggle('active', t.getAttribute('data-filter') === cat);
    }});
  }}
  tiles.forEach(function(t){{
    t.addEventListener('click', function(){{
      var cat = t.getAttribute('data-filter');
      active = (active === cat) ? null : cat;
      apply(active);
    }});
  }});
}})();
</script>
</body></html>
"""

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Cross-repo agent/spec/session workboard")
    ap.add_argument("roots", nargs="*", help="directories to scan for git repos")
    ap.add_argument("--out", default="workboard.html", help="output HTML path")
    ap.add_argument("--actions-out", default=None,
                    help="path for the companion actions script "
                         "(default: --out stem + .actions.sh)")
    ap.add_argument("--json", action="store_true", help="print JSON to stdout instead")
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS_DEFAULT)
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--abandon", nargs="+", metavar="CONV_ID", default=[],
                    help="mark Antigravity conversation(s) abandoned (skip-marker only), then rescan")
    ap.add_argument("--abandon-stale", action="store_true",
                    help="abandon every stale Antigravity conversation, then rescan")
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

    roots = [Path(r) for r in args.roots] if args.roots else default_roots()
    data = assemble(roots, args.max_depth, args.stale_days, args.quiet)

    if args.json:
        json.dump(data, sys.stdout, indent=2, default=str)
        print()
        return

    out = Path(args.out)
    actions_path = (Path(args.actions_out) if args.actions_out
                    else out.parent / (out.stem + ".actions.sh"))
    actions_path.write_text(build_actions_script(data), encoding="utf-8")
    actions_path.chmod(actions_path.stat().st_mode | 0o111)
    data["actions_path"] = str(actions_path)

    out.write_text(render_html(data), encoding="utf-8")
    t = data["totals"]
    print(f"workboard: {t['repos']} repos · {t['specs_open']} open specs · "
          f"{t['tasks_open']} open tasks · {t['sessions_active']} active sessions · "
          f"{t['attention']} need attention → {out} (actions → {actions_path})")


if __name__ == "__main__":
    main()
