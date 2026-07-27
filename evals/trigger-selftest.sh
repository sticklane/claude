#!/usr/bin/env bash
# Self-test for evals/assert-trigger.sh. Drives the grader against synthetic
# transcripts — no runner, no session — asserting each verdict it can reach:
# a Claude Code Skill call and a Codex SKILL.md read both count as activation,
# an unrelated transcript counts as no activation, both expectations fail on
# the opposite evidence, and an empty transcript fails rather than passing.
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GRADER="$ROOT/evals/assert-trigger.sh"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "SELFTEST FAIL: $1" >&2; exit 1; }

claude_call="$TMP/claude.jsonl"
printf '%s\n' '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"agentic:critique"}}]}}' > "$claude_call"

codex_read="$TMP/codex.jsonl"
printf '%s\n' '{"payload":{"type":"custom_tool_call","input":"sed -n 1,80p /x/.agents/skills/critique/SKILL.md"}}' > "$codex_read"

unrelated="$TMP/unrelated.jsonl"
printf '%s\n' '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read"}]}}' > "$unrelated"

empty="$TMP/empty.jsonl"
: > "$empty"

EVAL_TRANSCRIPT="$claude_call" bash "$GRADER" fired critique ||
  fail "a Claude Code Skill call must count as activation"
EVAL_TRANSCRIPT="$codex_read" bash "$GRADER" fired critique ||
  fail "a Codex SKILL.md read must count as activation"
EVAL_TRANSCRIPT="$unrelated" bash "$GRADER" not-fired critique ||
  fail "an unrelated transcript must count as no activation"

EVAL_TRANSCRIPT="$claude_call" bash "$GRADER" not-fired critique 2>/dev/null &&
  fail "not-fired must fail when the skill did activate"
EVAL_TRANSCRIPT="$unrelated" bash "$GRADER" fired critique 2>/dev/null &&
  fail "fired must fail when the skill did not activate"
EVAL_TRANSCRIPT="$empty" bash "$GRADER" fired critique 2>/dev/null &&
  fail "an empty transcript must fail, never pass"
EVAL_TRANSCRIPT="$claude_call" bash "$GRADER" maybe critique 2>/dev/null &&
  fail "an unknown expectation must be rejected"

echo "trigger selftest: OK (activation evidence, both expectations, empty transcript)"
