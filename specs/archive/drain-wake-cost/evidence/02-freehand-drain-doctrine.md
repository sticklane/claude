# Verification: 02-freehand-drain-doctrine

Verdict: PASS

Base commit: 0a5bcf3
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-a9676536c9e9af4e3

## Task-file append-only check

Command: `git diff 0a5bcf3 -- specs/drain-wake-cost/tasks/02-freehand-drain-doctrine.md`

Only change is a 14-line PLAN comment block inserted between the header
`Touch:` line and the `## Goal` heading (delete-at-close-out marker present).
No edits to Goal/Steps/Touch/Budget/Acceptance text; Status line unchanged
("in-progress"). PASS — no violation.

## Criterion 1 — freehand-drain block

Command: `grep -qi 'drain-shaped' .claude/rules/token-discipline.md` → exit 0

Quoted block (added under "Delegation defaults"):
> **Drain-shaped freehand requests → recommend `/drain`.** When a freehand
> request is drain-shaped ("drain the …", "work through the remaining tasks
> in specs/…"), recommend the human launch `/drain` rather than improvising
> an unstructured dispatch loop — the skill's window/baton/verdict machinery
> is what keeps a dispatch loop cheap and safe, and improvised loops are how
> the measured ~$1,406/week of unstructured orchestration happened
> (specs/drain-wake-cost/EVIDENCE.md). `/drain` is human-gated
> (`disable-model-invocation`): recommend it, never launch it on the human's
> behalf.

Verdict: PASS — grep exits 0; block explicitly recommends /drain, never
auto-invokes.

## Criterion 2 — tier-dispatch block

Command: `grep -q '0\.067' .claude/rules/token-discipline.md` → exit 0

Quoted block (added at end of "Model and effort matching"):
> **Freehand fan-out (dispatch outside a skill).** Mechanical fan-out work
> dispatched outside a skill uses the typed pinned agents
> (scout/verifier/implementation-worker) or passes an explicit cheap-tier
> `model` override to general-purpose; bare general-purpose at the session
> model is reserved for judgment work. This applies the rungs above to
> freehand dispatch — it does not change them. The default matters because
> general-purpose inherits the session's frontier model, so at $0.067/call it
> ran *costlier* than the opus-pinned implementation-worker at $0.057/call
> over the 2026-07 agentprof week (specs/drain-wake-cost/EVIDENCE.md) — a
> mechanical fan-out on the session's frontier model is the tier ladder
> inverted.

MANUAL check: names scout/verifier/implementation-worker as the default for
mechanical fan-outs, reserves session-model general-purpose for judgment
work — confirmed in the quoted text. Cites $0.067 vs $0.057 with EVIDENCE.md
provenance. Placed after the four existing rungs (scout-tier/session-tier/
deep-tier/frontier-tier) with an explicit "does not change them" disclaimer
— full diff confirms the four rungs' text is byte-identical to before
(git diff shows only additive hunks). No contradiction found.

Verdict: PASS

## Criterion 3 — artifact file

Command: `test -f specs/drain-wake-cost/global-claude-line.md` → exit 0

File opens: "**MANUAL (attended): for Steven to apply.** `~/.claude/CLAUDE.md`
is user-private and outside this repo, so this artifact only *proposes* the
text — applying it is a manual step..." — clearly marked MANUAL/attended.

Verdict: PASS

## Criterion 4 — no auto-invoke wording

Command: `grep -qiE 'auto-?invoke|auto-?trigger' .claude/rules/token-discipline.md || true` → exit 1 (no match found; the `|| true` makes the overall command exit 0 regardless)

MANUAL sanity: neither new block contains "auto-invoke"/"auto-trigger"
wording nor instructs auto-invoking /drain. Both explicitly say "recommend,
never launch it on the human's behalf" (rules block) and "recommend it,
never launch it automatically" (artifact's proposed one-liner). /drain
remains human-gated throughout.

Verdict: PASS

## Scope check

Command: `git status --short`
```
 M .claude/rules/token-discipline.md
 M specs/drain-wake-cost/tasks/02-freehand-drain-doctrine.md
?? specs/drain-wake-cost/global-claude-line.md
```

Command: `git diff 0a5bcf3 --stat`
```
 .claude/rules/token-discipline.md                    | 20 ++++++++++++++++++++
 .../tasks/02-freehand-drain-doctrine.md              | 14 ++++++++++++++
 2 files changed, 34 insertions(+)
```
(new untracked artifact file not shown in --stat since it's untracked, but
present per `git status`.)

No edits to CLAUDE.md (repo root), no drain skill files touched, no
`~/.claude/CLAUDE.md` touched (outside repo entirely; artifact only
proposes text for it). Matches the Touch list exactly:
`.claude/rules/token-discipline.md, specs/drain-wake-cost/global-claude-line.md`.

No scope creep found.

## Overall

PASS — all 4 acceptance criteria verified by direct command execution;
task-file diff is append-only (PLAN block only); no scope creep.
