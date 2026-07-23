"""``agentic resume [--json]`` — where things stand, from tracker state alone.

Prints the current frontier (the same ready set as ``agentic ready``) plus
the in-flight claims: who holds each claimed (in-progress) task, what it is,
and since when. There are no handoff, baton, or lease files (SPEC S9): the
position is a query over bd, not a file an earlier session left behind.
"""

import json
import os

from agentic import frontier


def _claim_row(issue):
    return {
        "id": issue["id"],
        "title": issue.get("title", ""),
        "owner": issue.get("owner") or "",
        "since": issue.get("started_at") or issue.get("updated_at") or "",
    }


def _ready_row(issue):
    return {
        "id": issue["id"],
        "title": issue.get("title", ""),
        "priority": frontier.priority_of(issue),
    }


def compute(cwd=None):
    fr = frontier.compute_frontier(frontier.load_issues(cwd=cwd))
    claims = sorted((_claim_row(i) for i in fr["claimed"]), key=lambda c: c["id"])
    ready = [_ready_row(i) for i in fr["admissible"]]
    return {"claims": claims, "ready": ready}


def run(args=None):
    as_json = bool(getattr(args, "json", False))
    state = compute(os.getcwd())

    if as_json:
        print(json.dumps(state))
        return 0

    claims = state["claims"]
    print(f"== in flight ({len(claims)}) ==")
    if not claims:
        print("  (nothing claimed)")
    for c in claims:
        who = c["owner"] or "unassigned"
        since = f"  since {c['since']}" if c["since"] else ""
        print(f"  {c['id']}  {who}{since}  {c['title']}")

    ready = state["ready"]
    print(f"== ready ({len(ready)}) ==")
    if not ready:
        print("  (no ready tasks)")
    for r in ready:
        print(f"  {r['id']}  P{r['priority']}  {r['title']}")
    return 0
