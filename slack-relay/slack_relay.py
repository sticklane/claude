#!/usr/bin/env python3
"""slack_relay — notify Slack of /drain DEFERRED questions and let a
threaded reply answer them, resuming the queue with no one at a keyboard.

One-shot poller (not a persistent server): run periodically by launchd's
StartInterval (see launchd/slack-relay.plist.tmpl), mirroring
~/cedarmillmonitor/cedarmill.py's shape rather than agent-console.py's
long-running HTTP server. Each run does two passes:

  1. Notify: scan configured repo roots for tasks with `Status: deferred`
     and a `## Deferred questions` section (reusing workboard.py's own
     scanner), diff against state.json's `posted` map, and post any new
     question to Slack.
  2. Reply: poll each open thread for a reply. A reply only counts as an
     answer if it is threaded to the exact question message, from the one
     configured authorized Slack user, not already processed, and within
     the staleness window. A valid answer re-checks the task file's
     Status is STILL `deferred` (compare-and-swap) before writing it under
     `## Answers` and flipping to `pending` — then, unless a live /drain
     already owns that spec (DRAIN-OWNER.md liveness), relaunches a
     headless /drain for it.

The Slack bot token lives ONLY in macOS Keychain (never in the yaml config,
never in git) — mirrors cedarmill.py's _keychain_password() exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = Path(__file__).resolve().parent / "slack_relay_state.json"
CONFIG_PATH = Path(__file__).resolve().parent / "slack_relay_config.yaml"

STATUS_LINE_RE = re.compile(r"^Status:\s*deferred\s*$", re.MULTILINE)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


workboard = _load_module(
    "workboard", REPO_ROOT / ".claude" / "skills" / "workboard" / "workboard.py"
)


# ---------------------------------------------------------------- discovery


def find_deferred_tasks(roots):
    """Every task across `roots` with `Status: deferred` and a non-empty
    `## Deferred questions` section, as a flat list of dicts: repo (str),
    spec_slug, task_rel (repo-relative path str), task_abs (Path),
    questions (list[str])."""
    found = []
    for root in roots:
        root = Path(root)
        for spec in workboard.scan_toolkit_specs(root):
            for task in spec.get("tasks", []):
                if task["status"] != "deferred":
                    continue
                questions = task.get("deferred_questions") or []
                if not questions:
                    continue
                found.append(
                    {
                        "repo": str(root),
                        "spec_slug": spec["slug"],
                        "task_rel": task["file"],
                        "task_abs": Path(task["abs"]),
                        "questions": questions,
                    }
                )
    return found


def question_key(item):
    """Stable state.json key: repo + task path + a hash of the question
    text, so a task re-deferred with a NEW question posts again instead of
    being suppressed as already-seen."""
    qtext = "\n".join(item["questions"])
    qhash = hashlib.sha1(qtext.encode("utf-8")).hexdigest()[:10]
    return f"{item['repo']}:{item['task_rel']}:{qhash}"


def diff_new_questions(found, state):
    """Items in `found` not already present (by question_key) in
    state['posted']."""
    posted = state.get("posted", {})
    return [item for item in found if question_key(item) not in posted]


# ------------------------------------------------------------ reply filter


def is_eligible_reply(
    reply, posted_entry, authorized_user_id, now_ts, max_reply_age_days
):
    """A reply counts as an answer only if it is threaded to the exact
    question message, from the one authorized user, not already
    processed, and arrived within the staleness window measured from when
    the question was POSTED (a reply to a long-dormant thread is stale,
    not an answer — the spec may have moved on)."""
    if reply.get("thread_ts") != posted_entry.get("ts"):
        return False
    if reply.get("user") != authorized_user_id:
        return False
    if reply.get("ts") in (posted_entry.get("processed_reply_ts") or []):
        return False
    posted_ts = posted_entry.get("posted_ts")
    if posted_ts is not None:
        try:
            reply_ts = float(reply.get("ts"))
        except (TypeError, ValueError):
            return False
        if reply_ts - posted_ts > max_reply_age_days * 86400:
            return False
    return True


# --------------------------------------------------------------- CAS write


def write_answer(repo, task_file, answer_text, source="slack-relay"):
    """Compare-and-swap: only writes if Status is STILL `deferred` at write
    time (protects against a race with a human answering another way
    between notify and reply). Appends under `## Answers`, flips
    `Status: deferred` -> `Status: pending`, commits path-scoped to just
    this one task file. Returns True on a successful write, False if the
    task had already moved on (nothing is touched in that case)."""
    text = task_file.read_text(encoding="utf-8")
    if not STATUS_LINE_RE.search(text):
        return False

    date = time.strftime("%Y-%m-%d", time.gmtime())
    if "## Answers" in text:
        text = text.rstrip("\n") + f"\n- [{date} {source}] {answer_text}\n"
    else:
        text = (
            text.rstrip("\n") + f"\n\n## Answers\n\n- [{date} {source}] {answer_text}\n"
        )
    text = STATUS_LINE_RE.sub("Status: pending", text, count=1)
    task_file.write_text(text, encoding="utf-8")

    rel = str(task_file.relative_to(repo))
    subprocess.run(["git", "add", rel], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", f"slack-relay: answer for {rel} (via Slack)"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return True


def push_if_upstream(repo):
    """Same push guard drain itself follows: push only if the current
    branch has a configured upstream; never --force; a rejected or
    offline push is logged and swallowed, never raised."""
    has_upstream = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=repo,
        capture_output=True,
    )
    if has_upstream.returncode != 0:
        return
    result = subprocess.run(["git", "push"], cwd=repo, capture_output=True)
    if result.returncode != 0:
        print(
            f"[slack-relay] push failed for {repo}, continuing: {result.stderr.decode().strip()}",
            file=sys.stderr,
        )


# ------------------------------------------------------------ relaunch guard


def is_owner_lease_fresh(spec_dir, window_seconds):
    """Best-effort advisory guard — NOT the safety-critical control. Drain's
    own compare-and-swap owner-lease claim (SKILL.md step 1) is what
    actually prevents two drains from dispatching against one spec at once;
    a redundant relaunch here just hits that claim's refuse path harmlessly.
    This only avoids the common-case unnecessary relaunch: FRESH iff
    specs/<slug>/DRAIN-OWNER.md exists and its mtime is within the window."""
    owner_file = spec_dir / "DRAIN-OWNER.md"
    if not owner_file.is_file():
        return False
    age = time.time() - owner_file.stat().st_mtime
    return age < window_seconds


def relaunch_drain(repo, spec_slug):
    """Detached headless /drain, the exact flag set from
    .claude/skills/drain/reference.md's Relaunch command template (fresh
    dispatch, not a baton continuation)."""
    log_path = Path(repo) / "specs" / spec_slug / ".slack-relay-drain.log"
    cmd = (
        f'nohup claude -p "/drain specs/{spec_slug}" '
        '--allowedTools "Task,Read,Edit,Write,Glob,Grep,Bash(git *)" '
        "--permission-mode dontAsk --max-turns 80 "
        f">> {log_path} 2>&1 &"
    )
    subprocess.Popen(["/bin/sh", "-c", cmd], cwd=repo)


# --------------------------------------------------------------- Slack I/O


def _keychain_token(service="slack-relay", account="bot-token"):
    out = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def slack_post_message(token, channel, text, thread_ts=None):
    payload = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=20,
    )
    return resp.json()


def slack_list_replies(token, channel, ts):
    resp = requests.get(
        "https://slack.com/api/conversations.replies",
        headers={"Authorization": f"Bearer {token}"},
        params={"channel": channel, "ts": ts},
        timeout=20,
    )
    data = resp.json()
    messages = data.get("messages", [])
    return [m for m in messages if m.get("ts") != ts]  # drop the parent itself


# ------------------------------------------------------------- config/state


def load_config(path=CONFIG_PATH):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_state(path=STATE_PATH):
    if not Path(path).is_file():
        return {"posted": {}}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(state, path=STATE_PATH):
    Path(path).write_text(json.dumps(state, indent=2), encoding="utf-8")


# ------------------------------------------------------------------- main


def run(config_path=CONFIG_PATH, state_path=STATE_PATH):
    config = load_config(config_path)
    state = load_state(state_path)
    token = _keychain_token()
    if not token:
        print(
            "[slack-relay] no Keychain token for service=slack-relay account=bot-token — skipping run",
            file=sys.stderr,
        )
        return 1

    roots = [Path(r).expanduser() for r in config["roots"]]
    channel = config["channel_id"]
    authorized_user = config["authorized_slack_user_id"]
    max_age = config.get("max_reply_age_days", 14)
    window = config.get("owner_lease_window_seconds", 900)

    # 1. Notify pass
    found = find_deferred_tasks(roots)
    for item in diff_new_questions(found, state):
        text = f"*{item['spec_slug']}* — `{item['task_rel']}`\n" + "\n".join(
            f"> {q}" for q in item["questions"]
        )
        resp = slack_post_message(token, channel, text)
        if not resp.get("ok"):
            print(f"[slack-relay] post failed: {resp}", file=sys.stderr)
            continue
        state.setdefault("posted", {})[question_key(item)] = {
            "ts": resp["ts"],
            "channel": channel,
            "posted_ts": time.time(),
            "repo": item["repo"],
            "task_rel": item["task_rel"],
            "spec_slug": item["spec_slug"],
            "processed_reply_ts": [],
        }
    save_state(state, state_path)

    # 2. Reply pass
    for key, entry in list(state.get("posted", {}).items()):
        replies = slack_list_replies(token, entry["channel"], entry["ts"])
        for reply in replies:
            if not is_eligible_reply(
                reply, entry, authorized_user, time.time(), max_age
            ):
                continue
            repo = Path(entry["repo"])
            task_file = repo / entry["task_rel"]
            entry.setdefault("processed_reply_ts", []).append(reply["ts"])
            if not write_answer(
                repo, task_file, reply.get("text", ""), source="slack-relay"
            ):
                slack_post_message(
                    token,
                    entry["channel"],
                    "(already answered another way — no action taken)",
                    thread_ts=entry["ts"],
                )
                del state["posted"][key]
                break
            push_if_upstream(repo)
            spec_dir = repo / "specs" / entry["spec_slug"]
            if is_owner_lease_fresh(spec_dir, window):
                slack_post_message(
                    token,
                    entry["channel"],
                    "answered — a live /drain already owns this spec, it'll pick it up",
                    thread_ts=entry["ts"],
                )
            else:
                relaunch_drain(repo, entry["spec_slug"])
                slack_post_message(
                    token,
                    entry["channel"],
                    "answered — relaunching /drain",
                    thread_ts=entry["ts"],
                )
            del state["posted"][key]
            break
    save_state(state, state_path)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Slack relay for /drain deferred questions"
    )
    ap.add_argument("--config", default=CONFIG_PATH)
    ap.add_argument("--state", default=STATE_PATH)
    args = ap.parse_args()
    sys.exit(run(args.config, args.state))


if __name__ == "__main__":
    main()
