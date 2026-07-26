#!/usr/bin/env python3
"""Validate Codex JSONL events and durable outcomes for the drain eval."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"trajectory: {message}", file=sys.stderr)
    raise SystemExit(1)


if len(sys.argv) != 3 or sys.argv[2] not in {"rolling", "blocked"}:
    fail("usage: assert_codex_trajectory.py <session.log> <rolling|blocked>")

events: list[dict] = []
for line in Path(sys.argv[1]).read_text(errors="replace").splitlines():
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    if isinstance(event, dict):
        events.append(event)

if not events:
    fail("no Codex JSON events found")

items = [
    event["item"]
    for event in events
    if isinstance(event.get("item"), dict)
]
skill_reads = [
    item
    for item in items
    if item.get("type") == "command_execution"
    and item.get("status") == "completed"
    and ".agents/skills/drain/SKILL.md" in item.get("command", "")
    and "name: drain" in item.get("aggregated_output", "")
]
if not skill_reads:
    fail("no completed command read the installed drain SKILL.md")

claude_inventory_calls = [
    item
    for item in items
    if item.get("type") == "command_execution"
    and "claude agents --json" in item.get("command", "")
]
if claude_inventory_calls:
    fail("Codex trajectory called the Claude CLI for live-agent inventory")

collaboration = [
    item
    for item in items
    if item.get("type") == "collab_tool_call"
]
mode = sys.argv[2]
if mode == "rolling":
    completed_waits = [
        index
        for index, item in enumerate(items)
        if item.get("type") == "collab_tool_call"
        and item.get("tool") == "wait"
        and item.get("status") == "completed"
    ]
    worker_receipts: dict[str, int] = {}
    review_receipts: dict[str, int] = {}
    worker_pattern = re.compile(r"^DRAIN_EVAL_WORKER ([^ ]+) DONE$", re.MULTILINE)
    review_pattern = re.compile(
        r"^DRAIN_EVAL_REVIEW ([^ ]+) verifier=PASS "
        r"critic=(?:READY|READY_WITH_NITS)$",
        re.MULTILINE,
    )
    for index, item in enumerate(items):
        if item.get("type") != "agent_message":
            continue
        text = item.get("text", "")
        for issue_id in worker_pattern.findall(text):
            worker_receipts[issue_id] = index
        for issue_id in review_pattern.findall(text):
            review_receipts[issue_id] = index
    if len(worker_receipts) != 3 or set(worker_receipts) != set(review_receipts):
        fail(
            "expected matched successful worker and review receipts for "
            f"3 distinct issues, found workers={sorted(worker_receipts)} "
            f"reviews={sorted(review_receipts)}"
        )
    previous_review = -1
    for issue_id, worker_index in sorted(
        worker_receipts.items(), key=lambda entry: entry[1]
    ):
        review_index = review_receipts[issue_id]
        if review_index <= worker_index:
            fail(f"review receipt for {issue_id} preceded its worker receipt")
        if not any(previous_review < index < worker_index for index in completed_waits):
            fail(f"no completed collaboration wait preceded worker receipt for {issue_id}")
        if not any(worker_index < index < review_index for index in completed_waits):
            fail(f"no completed collaboration wait preceded review receipt for {issue_id}")
        previous_review = review_index
    completed_commands = [
        item
        for item in items
        if item.get("type") == "command_execution"
        and item.get("status") == "completed"
        and item.get("exit_code") == 0
    ]
    command_text = [item.get("command", "") for item in completed_commands]
    worktree_adds = sum("git worktree add -b drain/" in command for command in command_text)
    landings = sum(
        "git merge " in command and "drain/" in command
        for command in command_text
    )
    worktree_removes = sum("git worktree remove" in command for command in command_text)
    gate_runs = [
        item
        for item in completed_commands
        if "scripts/check.sh" in item.get("command", "")
        and "gate-worktree=drain/" in item.get("aggregated_output", "")
    ]
    if worktree_adds < 3:
        fail(f"expected 3 successful drain worktree creations, found {worktree_adds}")
    if landings < 3:
        fail(f"expected 3 successful drain branch landings, found {landings}")
    if worktree_removes < 3:
        fail(f"expected 3 successful drain worktree removals, found {worktree_removes}")
    if len(gate_runs) < 3:
        fail(
            "expected 3 successful canonical gates in drain worktrees, "
            f"found {len(gate_runs)}"
        )
    gate_ids = {
        match.group(1)
        for item in gate_runs
        if (
            match := re.search(
                r"gate-worktree=drain/([^ ]+)", item.get("aggregated_output", "")
            )
        )
    }
    if set(worker_receipts) != gate_ids:
        fail(
            "worker/review receipt ids did not match successful worktree gates: "
            f"receipts={sorted(worker_receipts)} gates={sorted(gate_ids)}"
        )
elif any(item.get("tool") in {"wait", "spawn_agent"} for item in collaboration):
    fail("blocked-only queue dispatched or awaited a collaboration agent")

print(f"trajectory: Codex drain {mode} events verified")
