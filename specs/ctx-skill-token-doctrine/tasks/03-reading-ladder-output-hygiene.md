# Task 03: Reading ladder + output hygiene sections (R2, R3)

Status: pending
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md

## Goal

The ctx skill body teaches the escalation ladder and output hygiene. Add a
"Reading ladder" section prescribing, in order: (1) ctx query; (2) structural
content search (ast-grep where available, else Grep with `-l` or `-C 0`) for
body/literal/pattern questions; (3) sliced Read (`offset`/`limit` around a
ctx-reported line) when a specific body must be read; (4) whole-file Read only
when about to edit. Name the four concrete escalation triggers: symbol not
indexed, identical-qpath ambiguity, `heuristic` tag on a load-bearing ref,
body/literal questions. Add an "Output hygiene" section documenting: pipe
`map`/`tree`/`refs` through `head` or use `--limit`/`--json | jq` slices;
batch independent queries into one shell invocation; never paste more query
output into conversation than the decision needs — with at least one worked
pipe example. Mirror both sections into the antigravity ctx SKILL.md.

## Touch

Body of `.claude/skills/ctx/SKILL.md` and its antigravity mirror. This lands
after task 01 (same file — the SKILL.md-editing tasks serialize per the
spec's Landing-order registry; never run in parallel with 01/04/05). Do NOT
touch the frontmatter description (task 01) or the survey/scope sections
(tasks 04/05).

## Steps

1. Read the current ctx SKILL.md body to place the new sections coherently
   (after the query-commands table is natural).
2. Write the "Reading ladder" section: the four numbered rungs in order and
   the four named escalation triggers.
3. Write the "Output hygiene" section with the piping/batching guidance and
   at least one worked pipe example (e.g. `ctx map --limit 30 | head`).
4. Port equivalent sections into `antigravity/.agents/skills/ctx/SKILL.md`
   (paraphrased port — the concepts and rung order must land, wording may
   differ).
5. Confirm SKILL.md stays well under 500 lines.
6. Run the acceptance commands.

## Acceptance

- [ ] `grep -q 'Reading ladder' .claude/skills/ctx/SKILL.md` → exit 0
- [ ] `grep -Eqi 'ast-grep' .claude/skills/ctx/SKILL.md && grep -qi 'offset' .claude/skills/ctx/SKILL.md` → exit 0 (rungs 2 and 3 present)
- [ ] `grep -qi 'not indexed\|heuristic' .claude/skills/ctx/SKILL.md && grep -qi 'qpath\|identical' .claude/skills/ctx/SKILL.md` → exit 0 (escalation triggers named)
- [ ] `grep -qi 'Output hygiene' .claude/skills/ctx/SKILL.md && grep -q '| head\|--limit\|jq' .claude/skills/ctx/SKILL.md` → exit 0 (hygiene section + worked pipe example)
- [ ] `grep -qi 'ladder' antigravity/.agents/skills/ctx/SKILL.md && grep -qi 'hygiene\|--limit\| head' antigravity/.agents/skills/ctx/SKILL.md` → exit 0 (mirror coverage)
- [ ] `test "$(wc -l < .claude/skills/ctx/SKILL.md)" -lt 500` → exit 0
